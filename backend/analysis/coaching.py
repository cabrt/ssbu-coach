import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.patterns import find_patterns
from analysis.characters import get_character_tips, get_matchup_advice, get_character_specific_feedback, get_character_info, CHARACTER_DATA
from analysis.skill_estimator import estimate_skill_level
from analysis.habits import detect_habits

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

def _fmt_pct(value) -> str:
    """Format a percentage value to one decimal place (e.g., 13.8%)."""
    if value is None:
        return "?%"
    if isinstance(value, float):
        # Show one decimal if it has decimals, otherwise just the integer
        if value == int(value):
            return f"{int(value)}%"
        return f"{value:.1f}%"
    return f"{value}%"


def _filter_impossible_tips(tips: list) -> list:
    """Remove tips that reference impossible values (OCR errors like 188% damage)."""
    import re
    filtered = []
    for t in tips:
        msg = t.get("message") or ""
        # "Took 188% damage" or "Stock lost at 188%"
        numbers = re.findall(r"\b(\d{3,})(?:\.\d+)?\s*%", msg)
        if any(float(n) > 200 for n in numbers):
            continue
        filtered.append(t)
    return filtered


def _deduplicate_tips(tips: list) -> list:
    """Remove redundant tips that describe the same event at different granularities."""
    if not tips:
        return tips

    # Index tips by type for fast lookup
    by_type = {}
    for i, t in enumerate(tips):
        by_type.setdefault(t.get("type", ""), []).append((i, t))

    remove_indices = set()

    # If damage_taken and stock_lost within 2s, remove damage_taken (stock loss subsumes it)
    for _, dt_tip in by_type.get("damage_taken", []):
        dt_ts = dt_tip.get("timestamp", 0)
        for _, sl_tip in by_type.get("stock_lost", []):
            if abs(sl_tip.get("timestamp", 0) - dt_ts) <= 2:
                remove_indices.add(id(dt_tip))
                break

    # If got_edgeguarded and stock_lost within 3s, keep got_edgeguarded (more specific)
    for _, sl_tip in by_type.get("stock_lost", []):
        sl_ts = sl_tip.get("timestamp", 0)
        for _, eg_tip in by_type.get("got_edgeguarded", []):
            if abs(eg_tip.get("timestamp", 0) - sl_ts) <= 3:
                remove_indices.add(id(sl_tip))
                break

    return [t for t in tips if id(t) not in remove_indices]


def _prioritize_tips(tips: list) -> list:
    """Score and rank tips by importance. Top 8 get priority='high', rest get 'normal'."""
    if not tips:
        return tips

    BASE_SCORES = {
        "stock_lost": 90,
        "got_edgeguarded": 85,
        "damage_taken": 60,
        "edgeguard": 60,
        "combo": 45,
        "stock_taken": 50,
        "momentum_disadvantage": 40,
        "damage_dealt": 30,
        "momentum_advantage": 25,
        "neutral": 20,
        "habit": 15,
        "character_tip": 10,
    }

    for tip in tips:
        tip_type = tip.get("type", "")
        score = BASE_SCORES.get(tip_type, 20)

        # Severity boost for damage_taken
        if tip_type == "damage_taken" and tip.get("severity") == "high":
            score = 70

        # Big combos are more interesting
        if tip_type == "combo" and (tip.get("damage") or 0) > 30:
            score = 55

        # Vision-enhanced tips are more valuable
        if tip.get("enhanced"):
            score += 10
        if tip.get("multi_frame"):
            score += 5

        tip["_priority_score"] = score

    # Sort by score descending to assign ranks
    scored = sorted(tips, key=lambda t: (-t["_priority_score"], t.get("timestamp", 0)))

    for rank, tip in enumerate(scored, 1):
        tip["priority"] = "high" if rank <= 8 else "normal"
        tip["priority_rank"] = rank
        del tip["_priority_score"]

    # Re-sort by timestamp so both sections display chronologically
    return sorted(scored, key=lambda t: t.get("timestamp", 0))


def _nearest_state(states: list, timestamp: float) -> dict:
    """Find the game state closest to the given timestamp."""
    if not states:
        return None
    return min(states, key=lambda s: abs(s.get("timestamp", 0) - timestamp))


# Build set of all character display names for hallucination detection
_ALL_CHARACTER_NAMES = set()
for _key, _data in CHARACTER_DATA.items():
    _ALL_CHARACTER_NAMES.add(_data["name"].lower())
    _ALL_CHARACTER_NAMES.add(_key.lower())


def _validate_character_names(text: str, player_char: str, opponent_char: str) -> str:
    """Replace hallucinated character names in AI output with the correct ones."""
    if not text or not player_char or not opponent_char:
        return text

    import re

    # Normalize allowed names
    p_info = get_character_info(player_char)
    o_info = get_character_info(opponent_char)
    allowed = set()
    if p_info:
        allowed.add(p_info["name"].lower())
    if o_info:
        allowed.add(o_info["name"].lower())
    allowed.add(player_char.lower())
    allowed.add(opponent_char.lower())

    player_display = p_info["name"] if p_info else player_char.title()
    opponent_display = o_info["name"] if o_info else opponent_char.title()

    for char_name in _ALL_CHARACTER_NAMES:
        if char_name in allowed:
            continue
        # Case-insensitive replacement of wrong character names
        pattern = re.compile(re.escape(char_name), re.IGNORECASE)
        if pattern.search(text):
            # Heuristic: if context says "your" or "you", replace with player char;
            # otherwise replace with opponent char
            # Simple approach: just replace with the opponent (most common hallucination)
            text = pattern.sub(opponent_display, text)

    return text


def _get_opponent_move_hints(opponent_char: str, category: str = "kill") -> list:
    """Return a small list of opponent move names to respect."""
    o_data = get_character_info(opponent_char)
    if not o_data:
        return []
    moves = o_data.get("key_moves", {}).get(category, [])
    return [m for m in moves if m][:2]


def _get_player_move_hints(player_char: str, category: str = "neutral") -> list:
    """Return a small list of your character moves to consider."""
    p_data = get_character_info(player_char)
    if not p_data:
        return []
    moves = p_data.get("key_moves", {}).get(category, [])
    return [m for m in moves if m][:2]


def _get_opponent_escape_options(opponent_char: str, kill_percent: float) -> str:
    """
    Return opponent's likely escape options based on character and percent.
    This helps the player anticipate defensive reactions and cover them.
    """
    # Universal escape options everyone has
    universal_options = []
    
    if kill_percent >= 100:
        # At high percent, opponents are more desperate
        universal_options = ["airdodge", "DI away", "jump out"]
    elif kill_percent >= 60:
        # Mid percent - more variety
        universal_options = ["DI mixups", "airdodge", "double jump"]
    else:
        # Low percent - combo escapes
        universal_options = ["SDI", "airdodge", "jump"]
    
    # Character-specific escape options - comprehensive list
    char_options = []
    if opponent_char:
        opp_lower = opponent_char.lower()
        # Characters with special escape tools
        escape_tools = {
            # Swordfighters
            "marth": ["counter", "dolphin slash"],
            "lucina": ["counter", "dolphin slash"],
            "roy": ["counter", "blazer"],
            "chrom": ["counter", "soaring slash"],
            "ike": ["counter", "aether armor"],
            "cloud": ["limit up-b", "limit side-b"],
            "sephiroth": ["wing recovery", "counter"],
            "shulk": ["vision counter", "monado jump"],
            "corrin": ["counter surge", "dragon lunge"],
            "byleth": ["up-b tether", "down-b armor"],
            "pyra": ["prominence revolt"],
            "mythra": ["photon edge", "foresight"],
            "meta knight": ["dimensional cape", "mach tornado"],
            "link": ["bomb recovery", "up-b spin"],
            "young link": ["bomb recovery", "up-b spin"],
            "toon link": ["bomb recovery", "up-b spin"],
            "hero": ["zoom recovery", "bounce"],
            "robin": ["elwind recovery"],
            "mii swordfighter": ["tornado slash", "stone scabbard"],
            
            # Heavyweights
            "bowser": ["tough guy armor", "up-b out of shield"],
            "ganondorf": ["wizard's foot", "up-b recovery"],
            "king dedede": ["multiple jumps", "gordo"],
            "k rool": ["belly armor", "propeller recovery"],
            "donkey kong": ["cargo throw mixup", "spinning kong"],
            "king k. rool": ["belly armor", "propeller recovery"],
            "incineroar": ["revenge", "cross chop"],
            "ridley": ["multiple jumps", "space pirate rush"],
            "charizard": ["rock smash armor", "fly"],
            
            # Projectile/Zoners
            "samus": ["bomb recovery", "charge shot"],
            "dark samus": ["bomb recovery", "charge shot"],
            "snake": ["C4 recovery", "cypher"],
            "mega man": ["rush coil", "leaf shield"],
            "pac-man": ["trampoline recovery", "hydrant"],
            "villager": ["lloid rocket recovery", "timber"],
            "isabelle": ["lloid recovery", "fishing rod"],
            "duck hunt": ["can recovery", "clay pigeon"],
            "rob": ["gyro toss", "robo burner"],
            "olimar": ["pikmin tether", "whistle super armor"],
            "min min": ["ARMS jump", "up-b tether"],
            "mii gunner": ["arm rocket", "grenade"],
            
            # Fast/Combo Characters
            "fox": ["shine stall", "firefox"],
            "falco": ["shine stall", "firebird"],
            "wolf": ["shine", "wolf flash"],
            "pikachu": ["quick attack escape"],
            "pichu": ["agility escape"],
            "captain falcon": ["raptor boost", "falcon dive"],
            "sonic": ["spin dash escape", "spring"],
            "sheik": ["vanish mixup", "bouncing fish"],
            "zero suit samus": ["flip kick", "boost kick"],
            "greninja": ["shadow sneak", "hydro pump"],
            "joker": ["grappling hook", "rebel's guard"],
            "kazuya": ["devil fist", "devil wings"],
            
            # Floaties/Aerials
            "peach": ["float cancel", "parasol"],
            "daisy": ["float cancel", "parasol"],
            "jigglypuff": ["multiple jumps", "pound"],
            "kirby": ["multiple jumps", "final cutter"],
            "dedede": ["multiple jumps", "super dedede jump"],
            "game & watch": ["bucket", "fire escape"],
            "mr. game & watch": ["bucket", "fire escape"],
            
            # Grapplers
            "incineroar": ["revenge", "cross chop"],
            "bowser": ["tough guy", "command grab"],
            "donkey kong": ["cargo mixup", "headbutt bury"],
            
            # Unique Movement
            "zelda": ["teleport mixup", "phantom"],
            "palutena": ["teleport mixup", "counter/reflect"],
            "mewtwo": ["teleport mixup", "disable"],
            "wario": ["waft", "bike escape"],
            "diddy": ["barrel escape", "banana"],
            "bayonetta": ["witch twist", "bat within"],
            "inkling": ["roller escape", "splat bomb"],
            "steve": ["minecart escape", "block recovery"],
            "kazuya": ["devil wings", "electric moves"],
            "terry": ["power dunk", "buster wolf"],
            "ryu": ["focus attack", "shoryuken"],
            "ken": ["focus attack", "shoryuken"],
            "little mac": ["slip counter", "jolt haymaker"],
            "mii brawler": ["suplex", "soaring axe kick"],
            
            # Others
            "ness": ["PK thunder recovery", "PSI magnet"],
            "lucas": ["PK thunder recovery", "PSI magnet"],
            "yoshi": ["double jump armor", "egg toss"],
            "wii fit trainer": ["deep breathing", "header"],
            "pit": ["multiple jumps", "guardian orbitars"],
            "dark pit": ["multiple jumps", "guardian orbitars"],
            "rosalina": ["luma recall", "gravitational pull"],
            "ice climbers": ["belay", "blizzard"],
            "pokemon trainer": ["pokemon change invincibility"],
            "squirtle": ["withdraw", "waterfall"],
            "ivysaur": ["tether recovery", "razor leaf"],
            "piranha plant": ["ptooie", "long stem strike"],
            "banjo": ["wonderwing armor", "shock spring"],
            "sora": ["aerial dodge", "sonic blade"],
            "minecraft steve": ["minecart", "block placement"],
        }
        char_options = escape_tools.get(opp_lower, [])
    
    # Combine options
    all_options = universal_options + char_options[:2]
    if all_options:
        return "Watch for opponent's escape options: " + ", ".join(all_options[:4]) + ". Cover their most likely option to secure follow-ups."
    return ""


def _add_specificity_to_tips(
    tips: list,
    patterns: dict,
    states: list,
    player_char: str = None,
    opponent_char: str = None,
    skill_tier: str = None,
) -> list:
    """Make tips more specific using rule-based context, matchup hints, and skill tier."""
    if not tips:
        return tips

    damage_dealt_times = [d.get("timestamp") for d in patterns.get("damage_dealt", []) if d.get("timestamp") is not None]

    def _recent_damage_dealt(ts: float, window: float = 2.0) -> bool:
        return any(abs(ts - t) <= window for t in damage_dealt_times)

    for tip in tips:
        tip_type = tip.get("type")
        ts = tip.get("timestamp", 0)
        state = _nearest_state(states, ts)
        your_pct = state.get("p1_percent") if state else None
        opp_pct = state.get("p2_percent") if state else None

        context_hint = None

        if tip_type == "damage_taken":
            damage = tip.get("damage", 0)
            from_pct = tip.get("from_percent", 0)
            to_pct = tip.get("to_percent", from_pct + damage)

            base = f"Took {_fmt_pct(damage)} damage quickly ({_fmt_pct(from_pct)} → {_fmt_pct(to_pct)})."

            if _recent_damage_dealt(ts, window=2.0):
                context_hint = "overextension_reversal"
                if skill_tier in ("high", "top"):
                    detail = "Reversal after your advantage—consider whether you're missing a frame trap or overextending past your safe window."
                elif skill_tier == "mid":
                    detail = "Quick reversal after your hit—reset spacing or shield after advantage to avoid the punish."
                else:
                    detail = "You got hit right after attacking. Try shielding or backing off after landing a hit instead of rushing in again."
            elif (to_pct if isinstance(to_pct, (int, float)) else 0) >= 100:
                context_hint = "high_percent_defense"
                if skill_tier in ("high", "top"):
                    detail = "At kill percent, identify their burst range and avoid positions where they can confirm. Mix platform escape routes."
                elif skill_tier == "mid":
                    detail = "At high percent, prioritize safe landings and avoid drifting into burst range."
                else:
                    detail = "You're at high percent—be extra careful! Try staying near the center of the stage and shielding more."
            elif (from_pct if isinstance(from_pct, (int, float)) else 0) <= 30:
                context_hint = "early_opening"
                if skill_tier in ("high", "top"):
                    detail = "Opening-stage damage—analyze the spacing trap and whether you fell for a bait or committed to an unsafe approach."
                elif skill_tier == "mid":
                    detail = "At low percent, avoid autopilot approaches; use safer pokes and space just outside their range."
                else:
                    detail = "Try not to rush in at the start. Use safer moves from a distance and wait for an opening."
            else:
                context_hint = "mid_percent_defense"
                if skill_tier in ("high", "top"):
                    detail = "Identify the spacing trap. Consider DI mixups and platform escape routes to avoid follow-ups."
                elif skill_tier == "mid":
                    detail = "Mix defensive options (drift, fast-fall timing, shield) to avoid taking the follow-up."
                else:
                    detail = "Try shielding or jumping away when you see them coming. Don't just stand still."

            opp_kill_moves = _get_opponent_move_hints(opponent_char, "kill")
            if opp_kill_moves and (to_pct if isinstance(to_pct, (int, float)) else 0) >= 90:
                detail += f" Respect kill options like {', '.join(opp_kill_moves)}."

            tip["message"] = f"{base} {detail}"

        elif tip_type == "stock_lost":
            percent = tip.get("percent", 0)
            stocks_left = tip.get("stocks_remaining", "?")
            base = f"Lost a stock at {_fmt_pct(percent)}. ({stocks_left} stocks remaining)"

            pct_val = percent if isinstance(percent, (int, float)) else 0
            if pct_val < 60:
                context_hint = "early_stock_loss"
                if skill_tier in ("high", "top"):
                    detail = "Very early kill—analyze whether you got hit by a setup, failed DI on a confirm, or recovered predictably."
                elif skill_tier == "mid":
                    detail = "Early stock—likely off a setup or edgeguard. Mix your recovery timing and avoid predictable landings."
                else:
                    detail = "You died very early! The opponent probably hit you offstage. Try mixing up how you get back to the stage."
            elif pct_val < 100:
                context_hint = "mid_stock_loss"
                if skill_tier in ("high", "top"):
                    detail = "Mid-percent kill—check if your DI was optimal for the kill move and if you could have teched."
                elif skill_tier == "mid":
                    detail = "Mid-percent loss—review your defensive choice and DI in that exchange."
                else:
                    detail = "You lost a stock at a pretty normal percent. Try holding the control stick away from where you're flying to survive longer."
            elif pct_val < 150:
                context_hint = "standard_stock_loss"
                detail = "Standard kill percent—prioritize DI mixups and safer landings."
            else:
                context_hint = "late_stock_loss"
                detail = "Late stock—good survival, but avoid corner pressure and watch for kill options."

            opp_kill_moves = _get_opponent_move_hints(opponent_char, "kill")
            if opp_kill_moves and pct_val >= 90:
                detail += f" Against {opponent_char}, watch for {', '.join(opp_kill_moves)} at high percent."

            tip["message"] = f"{base} {detail}"

        elif tip_type == "stock_taken":
            percent = tip.get("opponent_percent", tip.get("percent", 0))
            opp_stocks_left = tip.get("opponent_stocks_remaining", "?")
            pct_val = percent if isinstance(percent, (int, float)) else 0

            if pct_val < 60:
                kill_type = "Early kill! Great punish"
                context_hint = "early_kill"
                detail = "Great closeout—look for the same confirm or edgeguard setup in similar spots."
            elif pct_val < 100:
                kill_type = "Solid kill"
                context_hint = "solid_kill"
                detail = "Solid punish—keep stage control and set up your next advantage."
            elif pct_val < 130:
                kill_type = "Nice KO"
                context_hint = "mid_kill"
                detail = "Clean closeout—focus on consistent kill setups at this percent."
            else:
                kill_type = "Got the KO"
                context_hint = "late_kill"
                if skill_tier in ("high", "top"):
                    detail = "Took too long to close—work on kill confirms earlier and covering escape options at lower percents."
                elif skill_tier == "mid":
                    detail = "High-percent KO—good patience; keep them cornered to avoid reversals."
                else:
                    detail = "You got the KO! The opponent survived a long time though. Try using your stronger moves (smash attacks) when they're at high percent."

            escape_options = _get_opponent_escape_options(opponent_char, pct_val)
            if escape_options:
                detail += f" Tip*: {escape_options}"

            tip["message"] = f"{kill_type}! Took opponent's stock at {_fmt_pct(percent)}. (Opponent has {opp_stocks_left} stocks left) {detail}"

        elif tip_type == "damage_dealt":
            damage = tip.get("damage", 0)
            from_pct = tip.get("from_percent", 0)
            to_pct = tip.get("to_percent", from_pct + damage)
            base = f"Nice! Dealt {_fmt_pct(damage)} damage ({_fmt_pct(from_pct)} → {_fmt_pct(to_pct)})."
            context_hint = "damage_dealt"
            player_moves = _get_player_move_hints(player_char, "neutral")
            move_hint = f" Consider pokes like {', '.join(player_moves)} to keep pressure safe." if player_moves else " Keep pressure by tracking their defensive habits (shield/roll/jump)."
            tip["message"] = f"{base}{move_hint}"

        elif tip_type == "combo":
            from_pct = tip.get("from_percent", 0)
            to_pct = tip.get("to_percent", from_pct + tip.get("damage", 0))
            damage = tip.get("damage", 0)
            context_hint = "combo_extension"
            if skill_tier in ("high", "top"):
                tip["message"] = f"Combo: {_fmt_pct(damage)} damage ({_fmt_pct(from_pct)} → {_fmt_pct(to_pct)}). Check if DI-dependent extensions were covered and if you reached the optimal combo ender for this percent."
            else:
                tip["message"] = f"Nice combo dealing {_fmt_pct(damage)} damage ({_fmt_pct(from_pct)} → {_fmt_pct(to_pct)}). Track DI and be ready to catch their landing with safe follow-ups."

        elif tip_type == "neutral":
            context_hint = "neutral_stall"
            if skill_tier in ("high", "top"):
                tip["message"] = f"Neutral stall ({tip.get('duration', 0):.0f}s). Identify whether you're both playing passive and who benefits from the timeout. Take micro-space with safe aerials and dash-dance."
            else:
                tip["message"] = f"Extended neutral ({tip.get('duration', 0):.0f}s). Use safe pokes and movement to force a reaction instead of overcommitting."

        elif tip_type == "edgeguard":
            context_hint = "edgeguard_success"
            your_dmg = tip.get("your_damage_taken", 0)
            player_moves = _get_player_move_hints(player_char, "edgeguard") or _get_player_move_hints(player_char, "kill")
            move_hint = f" Consider using {', '.join(player_moves)} for safe edgeguards." if player_moves else ""
            tip["message"] = (f"Great edgeguard! You secured the kill while only taking {_fmt_pct(your_dmg)} damage. "
                             f"{'Keep using this low-risk approach!' if your_dmg < 5 else 'Watch for counter-attacks when going deep.'}"
                             f"{move_hint}")

        elif tip_type == "momentum_advantage":
            context_hint = "momentum_positive"
            player_moves = _get_player_move_hints(player_char, "combo_starters")
            move_hint = f" Look for openings with {', '.join(player_moves)}." if player_moves else ""
            tip["message"] = (f"Good exchange! Dealt {_fmt_pct(tip.get('damage_dealt', 0))} while only taking {_fmt_pct(tip.get('damage_taken', 0))}. "
                             f"Capitalize by maintaining stage control and pressuring their landing.{move_hint}")

        elif tip_type == "momentum_disadvantage":
            context_hint = "momentum_negative"
            opp_moves = _get_opponent_move_hints(opponent_char, "neutral")
            move_hint = f" Watch for {', '.join(opp_moves)}." if opp_moves else ""
            tip["message"] = (f"Took {_fmt_pct(tip.get('damage_taken', 0))} in a bad exchange. "
                             f"Reset neutral with movement or a safe option.{move_hint}")

        if context_hint:
            tip["context_hint"] = context_hint
            tip["your_percent"] = your_pct
            tip["opponent_percent"] = opp_pct

    return tips


def compute_top3_focus_areas(
    skill_profile: dict, habit_report: dict, patterns: dict,
    stats: dict, player_char: str = None, opponent_char: str = None,
) -> list:
    """
    Compute the top 3 things the player should work on, with character-specific drills.
    Pure computation — zero API cost.
    """
    import statistics as _stats_mod

    candidates = []

    # --- Source 1: Weak skill metrics (score < 55) ---
    METRIC_FOCUS = {
        "damage_per_opening": {
            "title": "Punish game",
            "explain": "You're not converting openings into enough damage. Focus on follow-ups after landing a hit.",
            "drill_category": "combo_starters",
            "drill_template": "Practice {moves} into follow-up aerials at 0-60%",
        },
        "kill_efficiency": {
            "title": "Closing out stocks",
            "explain": "You're letting opponents live too long. Work on confirming kills at the right percent.",
            "drill_category": "kill",
            "drill_template": "Practice {moves} confirms at kill percent (80-120%)",
        },
        "edgeguard_rate": {
            "title": "Edgeguarding",
            "explain": "You're letting opponents recover for free. Going offstage is a major source of early kills.",
            "drill_category": "edgeguard",
            "drill_template": "Practice going offstage with {moves} when opponent is recovering",
        },
        "death_percent": {
            "title": "Survival and DI",
            "explain": "You're dying too early. Better DI and recovery mixups would extend your stocks significantly.",
            "drill_category": None,
            "drill_template": "Practice DI-ing away from kill moves and mixing up recovery timing",
        },
        "post_death_vulnerability": {
            "title": "Post-respawn composure",
            "explain": "You're taking too much damage right after respawning. Use invincibility frames wisely and reset to neutral.",
            "drill_category": "neutral",
            "drill_template": "After respawn: use invincibility to reposition with {moves}, don't attack immediately",
        },
        "combo_quality": {
            "title": "Combo optimization",
            "explain": "Your combos aren't dealing enough damage. Learn your character's true combo routes.",
            "drill_category": "combo_starters",
            "drill_template": "Practice {moves} into full combo routes in training mode",
        },
        "neutral_duration": {
            "title": "Neutral game",
            "explain": "Neutral phases are lasting too long. Find ways to create openings and force approaches.",
            "drill_category": "neutral",
            "drill_template": "Practice approaching with {moves} and mixing up timing",
        },
        "lead_conversion": {
            "title": "Closing out games",
            "explain": "You're losing leads after getting ahead. Play more patiently when you have a stock lead.",
            "drill_category": "kill",
            "drill_template": "When ahead, focus on safe {moves} confirms instead of risky plays",
        },
    }

    metrics = skill_profile.get("metrics", {}) if skill_profile else {}
    for key, m in metrics.items():
        score = m.get("score", 50)
        if score < 55 and key in METRIC_FOCUS:
            deficit = max(0, 55 - score)
            focus = METRIC_FOCUS[key]
            candidates.append({
                "title": focus["title"],
                "stat_line": f"Score: {int(score)}/100",
                "explanation": focus["explain"],
                "drill_category": focus["drill_category"],
                "drill_template": focus["drill_template"],
                "priority_score": deficit,
                "source": f"metric:{key}",
            })

    # --- Source 2: Detected habits ---
    HABIT_OVERLAP = {
        "post_death_panic": "post_death_vulnerability",
        "early_deaths": "death_percent",
        "passive_neutral": "neutral_duration",
        "overaggressive_neutral": "neutral_duration",
    }
    severity_scores = {"critical": 40, "notable": 25, "info": 10}
    habits = habit_report.get("habits", []) if habit_report else []

    for habit in habits:
        # Skip if overlapping metric already covers this
        overlapping_metric = HABIT_OVERLAP.get(habit.get("habit_type"))
        if overlapping_metric and any(c["source"] == f"metric:{overlapping_metric}" for c in candidates):
            # Boost the existing metric candidate instead
            for c in candidates:
                if c["source"] == f"metric:{overlapping_metric}":
                    c["priority_score"] += severity_scores.get(habit["severity"], 10) * 0.5
                    break
            continue

        candidates.append({
            "title": habit["description"].split(":")[0] if ":" in habit["description"] else habit["description"],
            "stat_line": f"{habit['occurrences']}x detected",
            "explanation": habit.get("suggestion", habit["evidence"]),
            "drill_category": None,
            "drill_template": habit.get("suggestion", ""),
            "priority_score": severity_scores.get(habit["severity"], 10),
            "source": f"habit:{habit.get('habit_type', '')}",
        })

    # --- Source 3: Pattern-derived insights ---
    stock_losses = patterns.get("stock_losses", [])
    kills = patterns.get("kills", [])
    edgeguards = patterns.get("edgeguards", [])

    # No edgeguards at all
    if not edgeguards and kills and not any(c["source"] == "metric:edgeguard_rate" for c in candidates):
        candidates.append({
            "title": "Start edgeguarding",
            "stat_line": "0 edgeguards this game",
            "explanation": "You never went offstage to challenge recovery. Even one edgeguard attempt per game builds the habit.",
            "drill_category": "edgeguard",
            "drill_template": "Practice going offstage with {moves} when opponent is recovering",
            "priority_score": 20,
            "source": "pattern:no_edgeguards",
        })

    # All deaths at low percent
    if len(stock_losses) >= 2:
        death_pcts = [sl.get("percent", 0) for sl in stock_losses if sl.get("percent")]
        if death_pcts and max(death_pcts) < 90:
            if not any(c["source"] == "metric:death_percent" for c in candidates):
                candidates.append({
                    "title": "Surviving longer",
                    "stat_line": f"Avg death at {sum(death_pcts)/len(death_pcts):.0f}%",
                    "explanation": "You're dying very early. Focus on DI and recovery mixups to live longer.",
                    "drill_category": None,
                    "drill_template": "Practice DI-ing away from kill moves and mixing up recovery",
                    "priority_score": 30,
                    "source": "pattern:early_deaths",
                })

    # Sort by priority score (highest first) and take top 3
    candidates.sort(key=lambda c: c["priority_score"], reverse=True)
    top3 = candidates[:3]

    # Generate character-specific drills
    char_data = get_character_info(player_char) if player_char else None
    key_moves = char_data.get("key_moves", {}) if char_data else {}

    results = []
    for area in top3:
        drills = []
        cat = area.get("drill_category")
        template = area.get("drill_template", "")

        if cat and key_moves.get(cat):
            moves = key_moves[cat][:3]
            moves_str = ", ".join(moves)
            drills.append(template.format(moves=moves_str))
        elif template and "{moves}" not in template:
            drills.append(template)
        elif template:
            drills.append(template.replace("{moves}", "safe options"))

        # Add a generic secondary drill based on category
        if cat == "kill" and key_moves.get("kill"):
            drills.append(f"In training mode, practice kill confirms with {key_moves['kill'][0]} at 80-130%")
        elif cat == "combo_starters" and key_moves.get("combo_starters"):
            drills.append(f"Lab {key_moves['combo_starters'][0]} follow-ups at low, mid, and high percent")

        results.append({
            "title": area["title"],
            "stat_line": area["stat_line"],
            "explanation": area["explanation"],
            "drills": drills[:2],
            "priority_score": area["priority_score"],
        })

    return results


def compute_opponent_report(
    patterns: dict, stats: dict, game_states: list,
    player_char: str = None, opponent_char: str = None,
    skill_profile: dict = None,
) -> dict:
    """
    Build a scouting report on the opponent's tendencies.
    Pure computation — zero API cost.
    """
    import statistics as _stats_mod
    from analysis.move_data import identify_best_move

    stock_losses = patterns.get("stock_losses", [])
    damage_spikes = patterns.get("damage_spikes", [])
    damage_dealt = patterns.get("damage_dealt", [])
    long_neutral = patterns.get("long_neutral", [])
    got_edgeguarded = patterns.get("got_edgeguarded", [])
    kills = patterns.get("kills", [])

    # --- 1. How they killed you ---
    # At 3fps OCR, damage deltas can't reliably identify specific moves:
    # a single move's damage may be split across frames, and combos get
    # merged into one delta. Instead, report each death with the damage
    # burst pattern and flag notable situations (early kills, spikes).
    deaths_detail = []
    for loss in stock_losses:
        death_ts = loss.get("timestamp", 0)
        death_pct = loss.get("percent", 0)

        # Collect damage deltas from game_states in 4s before death
        deltas = []
        for i, gs in enumerate(game_states):
            ts = gs.get("timestamp", 0)
            if ts > death_ts:
                break
            if death_ts - ts > 4:
                continue
            if i == 0:
                continue
            prev = game_states[i - 1]
            p1_now = gs.get("p1_percent") or 0
            p1_prev = prev.get("p1_percent") or 0
            delta = p1_now - p1_prev
            if delta > 3:
                deltas.append({"ts": ts, "delta": delta, "to_pct": p1_now})

        total_burst = sum(d["delta"] for d in deltas) if deltas else 0
        burst_duration = (deltas[-1]["ts"] - deltas[0]["ts"]) if len(deltas) >= 2 else 0

        # Build death description
        detail = {"kill_percent": death_pct, "burst_damage": round(total_burst, 1)}

        if death_pct < 80:
            detail["flag"] = "early kill"
            # Check if we got edgeguarded at this time
            got_eg = any(
                abs(eg.get("timestamp", 0) - death_ts) < 3
                for eg in got_edgeguarded
            )
            if got_eg:
                detail["description"] = f"Killed at {death_pct:.0f}% (edgeguarded/spiked)"
            else:
                detail["description"] = f"Killed at {death_pct:.0f}% — early kill, likely a spike or offstage KO"
        elif total_burst > 5:
            detail["description"] = f"Killed at {death_pct:.0f}% after taking {total_burst:.0f}% in {burst_duration:.1f}s"
        else:
            detail["description"] = f"Killed at {death_pct:.0f}%"

        deaths_detail.append(detail)

    # Aggregate kill percent stats
    kill_percents = [d["kill_percent"] for d in deaths_detail if d["kill_percent"]]
    avg_kill_pct = sum(kill_percents) / len(kill_percents) if kill_percents else 0
    early_kills = sum(1 for d in deaths_detail if d.get("flag") == "early kill")

    # --- 2. Neutral tendencies ---
    your_openings = len(damage_dealt)
    their_openings = len(damage_spikes)
    aggression_ratio = their_openings / max(1, your_openings)

    if aggression_ratio > 1.3:
        neutral_tendency = "aggressive"
        neutral_desc = "Your opponent played aggressively, creating more openings than you. Look for ways to punish their approaches."
    elif aggression_ratio < 0.7:
        neutral_tendency = "defensive"
        neutral_desc = "Your opponent played defensively, letting you approach more often. Mix up your approach timing and bait their defensive options."
    else:
        neutral_tendency = "balanced"
        neutral_desc = "The neutral game was fairly even. Focus on winning more of these exchanges through spacing and timing."

    if len(long_neutral) >= 3:
        neutral_desc += " There were multiple extended neutral phases — the opponent is patient."

    # --- 3. Exploitable patterns ---
    exploitable = []

    # Predictable kill percent
    if len(stock_losses) >= 2:
        death_pcts = [sl.get("percent", 0) for sl in stock_losses if sl.get("percent")]
        if len(death_pcts) >= 2:
            try:
                std = _stats_mod.stdev(death_pcts)
                if std < 15:
                    avg = sum(death_pcts) / len(death_pcts)
                    exploitable.append(
                        f"Opponent kills at a consistent percent range (~{avg:.0f}%). "
                        f"Expect their kill setup around this percent and prepare to DI or shield."
                    )
            except _stats_mod.StatisticsError:
                pass

    # Opponent doesn't edgeguard
    if stock_losses and len(got_edgeguarded) == 0:
        p_data = get_character_info(player_char) if player_char else None
        exploitable.append(
            "Opponent never went offstage to edgeguard you. "
            "You can recover more safely and predictably — save your mixups for when they start challenging."
        )

    # Opponent is passive
    if len(long_neutral) >= 3 and neutral_tendency != "aggressive":
        p_data = get_character_info(player_char)
        neutral_moves = p_data.get("key_moves", {}).get("neutral", [])[:2] if p_data else []
        if neutral_moves:
            exploitable.append(
                f"Opponent plays passively. Approach with {', '.join(neutral_moves)} and force them to react."
            )
        else:
            exploitable.append("Opponent plays passively. Approach more often and force reactions.")

    # --- 4. Character-specific tips ---
    o_data = get_character_info(opponent_char) if opponent_char else None
    char_tips = o_data.get("tips_against", [])[:3] if o_data else []

    # --- Summary ---
    summary_parts = []
    if deaths_detail:
        summary_parts.append(f"You died {len(deaths_detail)} time(s) (avg {avg_kill_pct:.0f}%)")
        if early_kills:
            summary_parts.append(f"{early_kills} early kill(s) — watch for spikes/edgeguards")
    summary_parts.append(f"Their neutral was {neutral_tendency}")
    if exploitable:
        summary_parts.append(f"{len(exploitable)} exploitable pattern(s) found")

    return {
        "deaths": deaths_detail,
        "avg_kill_percent": round(avg_kill_pct, 1),
        "early_kills": early_kills,
        "neutral_tendency": neutral_tendency,
        "neutral_description": neutral_desc,
        "exploitable_patterns": exploitable,
        "character_tips": char_tips,
        "summary": ". ".join(summary_parts) + ".",
    }


def compute_matchup_gameplan(
    player_char: str, opponent_char: str,
    patterns: dict = None, stats: dict = None,
) -> dict:
    """
    Build a pre-match game plan based on character matchup data.
    Pure computation from character database — zero API cost.
    """
    p_data = get_character_info(player_char) if player_char else None
    o_data = get_character_info(opponent_char) if opponent_char else None

    if not p_data and not o_data:
        return None

    # Archetype advantage insights
    ARCHETYPE_TIPS = {
        ("rushdown", "zoner"): "Get in close and stay aggressive. Don't let them zone you out.",
        ("rushdown", "heavyweight"): "Use your speed advantage. Hit and run — don't trade hits.",
        ("zoner", "rushdown"): "Keep them out with projectiles. Don't let them get in for free.",
        ("zoner", "heavyweight"): "Wall them out. They struggle to approach through projectiles.",
        ("heavyweight", "rushdown"): "One solid read wins the exchange. Be patient and punish overcommitment.",
        ("heavyweight", "zoner"): "Use your range and armor to push through projectiles. Close the gap.",
        ("swordfighter", "rushdown"): "Use your disjoint to stuff approaches. Space with tilts and aerials.",
        ("rushdown", "swordfighter"): "Get inside their sword range. Parry or shield their pokes and punish.",
        ("all-rounder", "zoner"): "Mix approaches with your balanced kit. You can play their game or rush in.",
        ("grappler", "zoner"): "Shield through projectiles and grab. One read leads to huge damage.",
    }

    p_arch = p_data.get("archetype", "").lower() if p_data else ""
    o_arch = o_data.get("archetype", "").lower() if o_data else ""

    # --- Win conditions ---
    win_conditions = []
    p_strengths = p_data.get("strengths", []) if p_data else []
    o_weaknesses = o_data.get("weaknesses", []) if o_data else []

    for s in p_strengths:
        s_lower = s.lower()
        for w in o_weaknesses:
            w_lower = w.lower()
            # Look for strength-weakness overlaps
            if any(kw in s_lower and kw in w_lower for kw in
                   ["range", "speed", "combo", "edge", "recover", "kill", "projectile", "air", "weight"]):
                win_conditions.append(f"Your {s.lower()} exploits their {w.lower()}")

    archetype_tip = ARCHETYPE_TIPS.get((p_arch, o_arch))
    if archetype_tip:
        win_conditions.append(archetype_tip)

    if not win_conditions:
        # Generic win condition from strengths
        if p_strengths:
            win_conditions.append(f"Lean on your strengths: {', '.join(p_strengths[:2]).lower()}")

    # --- Watch for (opponent threats) ---
    watch_for = []
    o_kill_moves = o_data.get("key_moves", {}).get("kill", []) if o_data else []
    o_strengths = o_data.get("strengths", []) if o_data else []

    if o_kill_moves:
        watch_for.append(f"Kill moves to respect: {', '.join(o_kill_moves[:3])}")
    if o_strengths:
        watch_for.append(f"Their strengths: {', '.join(o_strengths[:2]).lower()}")

    # --- Neutral approach ---
    neutral_approach = []
    p_neutral = p_data.get("key_moves", {}).get("neutral", []) if p_data else []
    p_tips_as = p_data.get("tips_as", []) if p_data else []
    o_tips_against = o_data.get("tips_against", []) if o_data else []

    if p_neutral:
        neutral_approach.append(f"Your best neutral tools: {', '.join(p_neutral[:3])}")
    if p_tips_as:
        neutral_approach.append(p_tips_as[0])
    if o_tips_against:
        neutral_approach.append(o_tips_against[0])

    # --- Key interactions ---
    key_interactions = []
    p_combo = p_data.get("key_moves", {}).get("combo_starters", []) if p_data else []
    p_edgeguard = p_data.get("key_moves", {}).get("edgeguard", []) if p_data else []
    p_kill = p_data.get("key_moves", {}).get("kill", []) if p_data else []

    if p_combo:
        key_interactions.append(f"Combo starters: {', '.join(p_combo[:2])} — look for these at low percent")
    if p_edgeguard:
        key_interactions.append(f"Edgeguard with: {', '.join(p_edgeguard[:2])}")
    if p_kill:
        key_interactions.append(f"Kill confirms: {', '.join(p_kill[:2])} at 80-130%")

    return {
        "win_conditions": win_conditions[:3],
        "watch_for": watch_for[:3],
        "neutral_approach": neutral_approach[:3],
        "key_interactions": key_interactions[:3],
    }


def _swap_game_states(game_states: list) -> list:
    """Swap P1 and P2 in each state so we can treat P2 as 'you' when you_are_p1 is False."""
    return [
        {
            "timestamp": s["timestamp"],
            "p1_percent": s.get("p2_percent"),
            "p2_percent": s.get("p1_percent"),
            "p1_stocks": s.get("p2_stocks"),
            "p2_stocks": s.get("p1_stocks"),
            "p1_character": s.get("p2_character"),
            "p2_character": s.get("p1_character"),
        }
        for s in game_states
    ]


def generate_coaching(
    game_states: list,
    player_char: str = None,
    opponent_char: str = None,
    you_are_p1: bool = True,
    video_path: str = None,
) -> dict:
    """
    Analyze game states and generate coaching feedback from your perspective.

    Args:
        game_states: List of game state dictionaries from video processing
        player_char: Your character (optional)
        opponent_char: Opponent character (optional)
        you_are_p1: True if you are the left/red player (P1), False if right/blue (P2)
        video_path: If provided, run offstage classifier to gate edgeguard labels (no false edgeguards)
    """
    if not game_states:
        return {"summary": "No game data detected. Make sure the video shows gameplay with the HUD visible.", "tips": []}

    # Normalize so that "you" are always P1 in the data we analyze
    states_to_analyze = game_states if you_are_p1 else _swap_game_states(game_states)

    patterns = find_patterns(states_to_analyze)

    # Gate edgeguard / got_edgeguarded on offstage evidence (vision) when video is available
    if video_path:
        try:
            from cv.offstage_classifier import refine_edgeguards_with_vision
            refine_edgeguards_with_vision(video_path, patterns, you_are_p1=you_are_p1)
        except Exception as e:
            import traceback
            print(f"[Coaching] Offstage classifier failed (edgeguards unchanged): {e}")
            traceback.print_exc()

    raw_stats = calculate_stats(states_to_analyze)

    # Resolve character identities from the normalized state (P1 = you, P2 = opponent)
    if not player_char or not opponent_char:
        auto_player, auto_opponent = detect_match_characters(states_to_analyze)
        player_char = player_char or auto_player
        opponent_char = opponent_char or auto_opponent

    # --- Skill estimation & habit detection (zero API cost) ---
    skill_profile = estimate_skill_level(
        patterns, states_to_analyze, player_char, opponent_char
    )
    habit_report = detect_habits(
        patterns, states_to_analyze, player_char, opponent_char
    )
    skill_tier = skill_profile.get("tier", "mid")
    
    tips = []
    
    # generate tips based on patterns (already from "you" perspective)
    if patterns.get("damage_spikes"):
        for spike in patterns["damage_spikes"][:5]:
            from_pct = spike.get("from_percent", 0)
            to_pct = spike.get("to_percent", spike["damage"])
            damage = spike['damage']
            tips.append({
                "timestamp": spike["timestamp"],
                "type": "damage_taken",
                "severity": "high" if damage > 50 else "medium",
                "message": f"Took {_fmt_pct(damage)} damage quickly ({_fmt_pct(from_pct)} → {_fmt_pct(to_pct)}).",
                "from_percent": from_pct,
                "to_percent": to_pct,
                "damage": damage,
            })
    
    if patterns.get("long_neutral"):
        for neutral in patterns["long_neutral"][:3]:
            tips.append({
                "timestamp": neutral["start"],
                "type": "neutral",
                "severity": "low",
                "message": f"Extended neutral ({neutral['duration']:.0f}s). Look for ways to force an approach or create openings.",
                "duration": neutral.get("duration", 0),
            })
    
    if patterns.get("stock_losses"):
        for loss in patterns["stock_losses"]:
            stocks_left = loss.get("stocks_remaining", "?")
            percent = loss.get("percent", 0)
            tips.append({
                "timestamp": loss["timestamp"],
                "type": "stock_lost",
                "severity": "high",
                "message": f"Lost a stock at {_fmt_pct(percent)}. ({stocks_left} stocks remaining) " + get_stock_loss_advice(percent),
                "percent": percent,
                "stocks_remaining": stocks_left,
            })
    
    if patterns.get("combos"):
        for combo in patterns["combos"][:5]:
            from_pct = combo.get("from_percent", 0)
            to_pct = combo.get("to_percent", from_pct + combo["damage"])
            damage = combo['damage']
            tips.append({
                "timestamp": combo["start"],
                "type": "combo",
                "severity": "positive",
                "message": f"Nice combo dealing {_fmt_pct(damage)} damage ({_fmt_pct(from_pct)} → {_fmt_pct(to_pct)})!",
                "from_percent": from_pct,
                "to_percent": to_pct,
                "damage": damage,
            })
    
    if patterns.get("kills"):
        for kill in patterns["kills"]:
            opp_stocks_left = kill.get("opponent_stocks_remaining", "?")
            percent = kill.get("opponent_percent", 0)
            # Determine how early/late the kill was
            pct_val = percent if isinstance(percent, (int, float)) else 0
            if pct_val < 60:
                kill_type = "Early kill! Great punish"
            elif pct_val < 100:
                kill_type = "Solid kill"
            elif pct_val < 130:
                kill_type = "Nice KO"
            else:
                kill_type = "Got the KO"
            tips.append({
                "timestamp": kill["timestamp"],
                "type": "stock_taken",
                "severity": "positive",
                "message": f"{kill_type}! Took opponent's stock at {_fmt_pct(percent)}. (Opponent has {opp_stocks_left} stocks left)",
                "opponent_percent": percent,
                "opponent_stocks_remaining": opp_stocks_left,
            })
    
    if patterns.get("damage_dealt"):
        # Include more damage_dealt events (up to 10) to cover full match
        for dealt in patterns["damage_dealt"][:10]:
            from_pct = dealt.get("from_percent", 0)
            to_pct = dealt.get("to_percent", dealt["damage"])
            damage = dealt['damage']
            tips.append({
                "timestamp": dealt["timestamp"],
                "type": "damage_dealt",
                "severity": "positive",
                "message": f"Nice! Dealt {_fmt_pct(damage)} damage ({_fmt_pct(from_pct)} → {_fmt_pct(to_pct)}).",
                "from_percent": from_pct,
                "to_percent": to_pct,
                "damage": damage,
            })
    
    # EDGEGUARD TIPS - recognize successful offstage plays
    if patterns.get("edgeguards"):
        for eg in patterns["edgeguards"][:5]:
            likely = eg.get("is_likely_edgeguard", False)
            your_dmg = eg.get("your_damage_taken", 0)
            tips.append({
                "timestamp": eg["timestamp"],
                "type": "edgeguard",
                "severity": "positive",
                "message": f"Great edgeguard! You secured the kill while only taking {_fmt_pct(your_dmg)} damage. "
                          f"{'Low-risk edgeguard - keep using this approach!' if likely else 'Watch for trades when going deep offstage.'}",
                "your_damage_taken": your_dmg,
                "opponent_percent": eg.get("opponent_percent", 0),
            })
    
    # GOT EDGEGUARDED TIPS - learn from opponent's successful edgeguards
    if patterns.get("got_edgeguarded"):
        for eg in patterns["got_edgeguarded"][:3]:
            death_pct = eg.get("your_death_percent", 0)
            opp_dmg = eg.get("opponent_damage_taken", 0)
            tips.append({
                "timestamp": eg["timestamp"],
                "type": "got_edgeguarded",
                "severity": "high",
                "message": f"Got edgeguarded at {_fmt_pct(death_pct)}. "
                          f"{'Opponent took 0 damage - they read your recovery option. ' if opp_dmg < 5 else ''}"
                          f"Mix up recovery timing, angle, and use of double jump/up-B to make yourself harder to edgeguard.",
                "your_death_percent": death_pct,
                "opponent_damage_taken": opp_dmg,
            })
    
    # MOMENTUM SWING TIPS - help players understand match flow
    if patterns.get("momentum_swings"):
        advantage_count = sum(1 for m in patterns["momentum_swings"] if m.get("type") == "advantage")
        disadvantage_count = sum(1 for m in patterns["momentum_swings"] if m.get("type") == "disadvantage")
        
        # Only add tips for significant momentum swings (up to 3)
        for swing in patterns["momentum_swings"][:3]:
            if swing.get("type") == "advantage":
                tips.append({
                    "timestamp": swing["timestamp"],
                    "type": "momentum_advantage",
                    "severity": "positive",
                    "message": f"Good exchange! Dealt {_fmt_pct(swing.get('damage_dealt', 0))} while only taking {_fmt_pct(swing.get('damage_taken', 0))}. "
                              f"Capitalize on advantage by maintaining stage control.",
                    "damage_dealt": swing.get("damage_dealt", 0),
                    "damage_taken": swing.get("damage_taken", 0),
                })
            elif swing.get("type") == "disadvantage":
                tips.append({
                    "timestamp": swing["timestamp"],
                    "type": "momentum_disadvantage",
                    "severity": "medium",
                    "message": f"Took {_fmt_pct(swing.get('damage_taken', 0))} damage in a bad exchange. "
                              f"Look to reset neutral with movement or a safe option instead of engaging directly.",
                    "damage_dealt": swing.get("damage_dealt", 0),
                    "damage_taken": swing.get("damage_taken", 0),
                })
    
    # add habit-based tips
    for habit in habit_report.get("habits", []):
        tips.append({
            "timestamp": 0,
            "type": "habit",
            "severity": habit.get("severity", "info"),
            "message": f"[Habit] {habit['description']}: {habit['suggestion']}",
            "habit_type": habit.get("habit_type"),
            "evidence": habit.get("evidence"),
            "occurrences": habit.get("occurrences", 0),
        })

    # add character-specific tips
    char_tips = get_character_specific_feedback(player_char, opponent_char, patterns)
    for char_tip in char_tips:
        char_tip["timestamp"] = 0
        char_tip["severity"] = "info"
        tips.append(char_tip)
    
    # drop tips with impossible game-state (OCR errors: 188% damage, stock lost at 188%, etc.)
    tips = _filter_impossible_tips(tips)

    # add rule-based specificity and matchup context (calibrated by skill tier)
    tips = _add_specificity_to_tips(tips, patterns, states_to_analyze, player_char, opponent_char, skill_tier=skill_tier)
    
    # generate AI summary and enhance tips with factual advice only
    summary, enhanced_tips = generate_ai_coaching(
        raw_stats, patterns, tips, player_char, opponent_char,
        skill_profile=skill_profile, habit_report=habit_report,
    )
    
    # Normalize stats for frontend: always "your" and "opponent" (no p1/p2)
    # Use raw stats max (unsmoothed) - this is the TRUE maximum percent reached
    # Pattern's true_max uses smoothed data which can be lower
    your_max = raw_stats.get("p1_max_percent", 0) or patterns.get("p1_true_max_percent", 0)
    opp_max = raw_stats.get("p2_max_percent", 0) or patterns.get("p2_true_max_percent", 0)
    
    stats = {
        "duration": raw_stats.get("duration", 0),
        "your_max_percent": round(your_max, 1) if isinstance(your_max, float) else your_max,
        "opponent_max_percent": round(opp_max, 1) if isinstance(opp_max, float) else opp_max,
        "you_won": raw_stats.get("winner") == "p1",
        "p1_max_percent": round(your_max, 1) if isinstance(your_max, float) else your_max,
        "p2_max_percent": round(opp_max, 1) if isinstance(opp_max, float) else opp_max,
        "winner": raw_stats.get("winner"),
    }
    
    # --- Top 3 focus areas, opponent scouting, matchup gameplan (zero API cost) ---
    top3_focus = compute_top3_focus_areas(
        skill_profile, habit_report, patterns, raw_stats, player_char, opponent_char
    )
    opponent_report = compute_opponent_report(
        patterns, raw_stats, states_to_analyze, player_char, opponent_char, skill_profile
    )
    matchup_gameplan = compute_matchup_gameplan(
        player_char, opponent_char, patterns, raw_stats
    )

    sorted_tips = sorted(enhanced_tips or tips, key=lambda x: x["timestamp"])
    prioritized_tips = _prioritize_tips(_deduplicate_tips(sorted_tips))

    return {
        "summary": summary,
        "stats": stats,
        "tips": prioritized_tips,
        "patterns": patterns,
        "characters": {
            "player": player_char,
            "opponent": opponent_char
        },
        "skill_profile": skill_profile,
        "habits": habit_report.get("habits", []),
        "top3_focus_areas": top3_focus,
        "opponent_report": opponent_report,
        "matchup_gameplan": matchup_gameplan,
    }

def detect_match_characters(game_states: list) -> tuple:
    """Determine characters by most common detection across frames."""
    p1_chars = {}
    p2_chars = {}
    
    for state in game_states:
        p1_char = state.get("p1_character")
        p2_char = state.get("p2_character")
        
        if p1_char:
            p1_chars[p1_char] = p1_chars.get(p1_char, 0) + 1
        if p2_char:
            p2_chars[p2_char] = p2_chars.get(p2_char, 0) + 1
    
    player_char = max(p1_chars, key=p1_chars.get) if p1_chars else None
    opponent_char = max(p2_chars, key=p2_chars.get) if p2_chars else None
    
    return player_char, opponent_char

def calculate_stats(game_states: list) -> dict:
    """Calculate overall match statistics."""
    if not game_states:
        return {}
    
    p1_percents = [s["p1_percent"] for s in game_states if s.get("p1_percent") is not None]
    p2_percents = [s["p2_percent"] for s in game_states if s.get("p2_percent") is not None]
    
    stats = {
        "duration": game_states[-1]["timestamp"] if game_states else 0,
        "p1_max_percent": max(p1_percents) if p1_percents else 0,
        "p2_max_percent": max(p2_percents) if p2_percents else 0,
        "p1_avg_percent": sum(p1_percents) / len(p1_percents) if p1_percents else 0,
        "p2_avg_percent": sum(p2_percents) / len(p2_percents) if p2_percents else 0,
    }
    
    # WINNER DETECTION: Simple rule - whoever has 0 stocks at the end LOST
    # The game NEVER ends with both players alive
    winner = "unknown"
    
    # Method 1: Look at ALL frames and find who reaches 0 stocks FIRST
    # (while the other player still has stocks remaining)
    for i, state in enumerate(game_states):
        p1_stocks = state.get("p1_stocks")
        p2_stocks = state.get("p2_stocks")
        
        # P1 at 0 stocks while P2 still has stocks = P2 wins
        if p1_stocks == 0 and p2_stocks is not None and p2_stocks >= 1:
            winner = "p2"
            print(f"[Winner] P1 at 0 stocks while P2 has {p2_stocks} at {state['timestamp']}s -> P2 wins")
            break
        
        # P2 at 0 stocks while P1 still has stocks = P1 wins
        if p2_stocks == 0 and p1_stocks is not None and p1_stocks >= 1:
            winner = "p1"
            print(f"[Winner] P2 at 0 stocks while P1 has {p1_stocks} at {state['timestamp']}s -> P1 wins")
            break
    
    # Method 2: If no clear 0-vs-1+ found, look at the last valid stock readings
    # Find who had fewer stocks in the final portion of the match
    if winner == "unknown":
        # Get last 30 frames to look for stock differences
        last_frames = game_states[-30:] if len(game_states) >= 30 else game_states
        
        for state in reversed(last_frames):
            p1_s = state.get("p1_stocks")
            p2_s = state.get("p2_stocks")
            
            if p1_s is not None and p2_s is not None and p1_s != p2_s:
                if p1_s < p2_s:
                    winner = "p2"  # P1 has fewer stocks = P2 wins
                else:
                    winner = "p1"  # P2 has fewer stocks = P1 wins
                print(f"[Winner] Stock difference found: P1={p1_s}, P2={p2_s} -> {winner} wins")
                break
    
    # Method 3: Count total stock losses throughout the match
    if winner == "unknown":
        p1_stock_losses = 0
        p2_stock_losses = 0
        
        for i in range(1, len(game_states)):
            prev = game_states[i - 1]
            curr = game_states[i]
            
            p1_prev = prev.get("p1_stocks")
            p1_curr = curr.get("p1_stocks")
            p2_prev = prev.get("p2_stocks")
            p2_curr = curr.get("p2_stocks")
            
            # Count when stocks decrease
            if p1_prev is not None and p1_curr is not None and p1_curr < p1_prev:
                p1_stock_losses += (p1_prev - p1_curr)
            if p2_prev is not None and p2_curr is not None and p2_curr < p2_prev:
                p2_stock_losses += (p2_prev - p2_curr)
        
        # Player who lost more stocks = lost the game
        if p1_stock_losses > p2_stock_losses:
            winner = "p2"
            print(f"[Winner] P1 lost {p1_stock_losses} stocks, P2 lost {p2_stock_losses} -> P2 wins")
        elif p2_stock_losses > p1_stock_losses:
            winner = "p1"
            print(f"[Winner] P1 lost {p1_stock_losses} stocks, P2 lost {p2_stock_losses} -> P1 wins")
    
    # Method 4: Count percent resets (deaths) throughout the game FIRST
    # This is more reliable than percent heuristics
    if winner == "unknown":
        p1_deaths = 0
        p2_deaths = 0
        
        for i in range(1, len(game_states)):
            prev = game_states[i-1]
            curr = game_states[i]
            
            p1_prev_pct = prev.get("p1_percent") or 0
            p1_curr_pct = curr.get("p1_percent") or 0
            p2_prev_pct = prev.get("p2_percent") or 0
            p2_curr_pct = curr.get("p2_percent") or 0
            
            # Detect percent resets (high -> low)
            if p1_prev_pct >= 50 and p1_curr_pct < 15:
                p1_deaths += 1
            if p2_prev_pct >= 50 and p2_curr_pct < 15:
                p2_deaths += 1
        
        if p1_deaths > p2_deaths:
            winner = "p2"  # P1 died more = P2 wins
            print(f"[Winner] Death count: P1={p1_deaths}, P2={p2_deaths} -> P2 wins")
        elif p2_deaths > p1_deaths:
            winner = "p1"  # P2 died more = P1 wins
            print(f"[Winner] Death count: P1={p1_deaths}, P2={p2_deaths} -> P1 wins")
        else:
            # Deaths are tied - likely missed the final death
            print(f"[Winner] Death count tied: P1={p1_deaths}, P2={p2_deaths} - checking other methods")
    
    # Method 5: Check for sudden percent drop in final frames (indicates a kill happened)
    if winner == "unknown" and len(game_states) >= 10:
        final_frames = game_states[-10:]
        
        for i in range(1, len(final_frames)):
            prev = final_frames[i-1]
            curr = final_frames[i]
            
            p1_prev_pct = prev.get("p1_percent") or 0
            p1_curr_pct = curr.get("p1_percent") or 0
            p2_prev_pct = prev.get("p2_percent") or 0
            p2_curr_pct = curr.get("p2_percent") or 0
            
            if p1_prev_pct >= 50 and p1_curr_pct < 15:
                winner = "p2"
                print(f"[Winner] Final frame P1 reset: {p1_prev_pct}% -> {p1_curr_pct}% -> P2 wins")
                break
            if p2_prev_pct >= 50 and p2_curr_pct < 15:
                winner = "p1"
                print(f"[Winner] Final frame P2 reset: {p2_prev_pct}% -> {p2_curr_pct}% -> P1 wins")
                break
    
    # Method 6: Percent heuristic - ONLY use when one player is clearly at kill percent
    # This is a last resort and only works when there's a BIG difference
    if winner == "unknown":
        last_active_frame = None
        for s in reversed(game_states):
            if s.get("game_active", True):
                last_active_frame = s
                break
        
        if last_active_frame:
            p1_last_pct = last_active_frame.get("p1_percent")
            p2_last_pct = last_active_frame.get("p2_percent")
            
            # Only use this heuristic with a LARGE threshold (50%+)
            # Small differences are unreliable
            if p1_last_pct is not None and p2_last_pct is not None:
                if p1_last_pct > p2_last_pct + 50:
                    winner = "p2"
                    print(f"[Winner] Large percent diff: P1={p1_last_pct}%, P2={p2_last_pct}% -> P1 likely KO'd -> P2 wins")
                elif p2_last_pct > p1_last_pct + 50:
                    winner = "p1"
                    print(f"[Winner] Large percent diff: P1={p1_last_pct}%, P2={p2_last_pct}% -> P2 likely KO'd -> P1 wins")
    
    # Get final stock counts
    def get_mode(lst):
        if not lst:
            return None
        return max(set(lst), key=lst.count)
    
    last_frames = game_states[-15:] if len(game_states) >= 15 else game_states
    p1_final_stocks_list = [s.get("p1_stocks") for s in last_frames if s.get("p1_stocks") is not None]
    p2_final_stocks_list = [s.get("p2_stocks") for s in last_frames if s.get("p2_stocks") is not None]
    
    stats["winner"] = winner
    stats["p1_final_stocks"] = get_mode(p1_final_stocks_list)
    stats["p2_final_stocks"] = get_mode(p2_final_stocks_list)
    
    print(f"[Stats] Final stocks: P1={stats['p1_final_stocks']}, P2={stats['p2_final_stocks']}, Winner={winner}")
    
    return stats

def get_stock_loss_advice(percent: int) -> str:
    if percent < 60:
        return "Early stock loss. Watch out for kill confirms at low percent."
    elif percent < 100:
        return "Mid-percent stock. Check if you got read on a defensive option."
    elif percent < 150:
        return "Standard kill percent. Could be unavoidable, but review your DI."
    else:
        return "Late stock. Good survival, but you might've been able to close out earlier."

def generate_ai_coaching(
    stats: dict, patterns: dict, tips: list,
    player_char: str = None, opponent_char: str = None,
    skill_profile: dict = None, habit_report: dict = None,
) -> tuple:
    """Generate AI-powered summary and enhanced tips (stats are already from 'you' = P1 perspective)."""

    duration = stats.get("duration", 0)
    mins = int(duration // 60)
    secs = int(duration % 60)
    you_won = stats.get("winner") == "p1"

    basic_summary = f"Match duration: {mins}:{secs:02d}. "
    basic_summary += "You won this game. " if you_won else "You lost this game. "
    basic_summary += f"Found {len(tips)} moments to review."

    if not os.getenv("OPENAI_API_KEY"):
        # Fall back to Gemini for tip enhancement (summary stays basic)
        tips = enhance_tips_with_gemini(tips, player_char, opponent_char)
        return basic_summary, tips

    try:
        from openai import OpenAI
        client = OpenAI()

        damage_spikes = patterns.get("damage_spikes", [])
        stock_losses = patterns.get("stock_losses", [])

        char_context = ""
        if player_char:
            p_data = get_character_info(player_char)
            if p_data:
                char_context += f"\nYOUR CHARACTER: {p_data['name']} ({p_data['archetype']})"
                char_context += f"\n- Strengths: {', '.join(p_data['strengths'])}"
                char_context += f"\n- Weaknesses: {', '.join(p_data['weaknesses'])}"
                char_context += f"\n- Key moves: {', '.join(p_data.get('key_moves', {}).get('neutral', [])[:3])}"
        if opponent_char:
            o_data = get_character_info(opponent_char)
            if o_data:
                char_context += f"\nOPPONENT: {o_data['name']} ({o_data['archetype']})"
                char_context += f"\n- Kill moves to respect: {', '.join(o_data.get('key_moves', {}).get('kill', [])[:3])}"
                char_context += f"\n- Tips against them: {', '.join(o_data.get('tips_against', [])[:2])}"

        # Skill and habit context for calibrated coaching
        skill_context = ""
        if skill_profile:
            tier = skill_profile.get("tier", "mid")
            score = skill_profile.get("overall_score", 0)
            strengths = skill_profile.get("strengths", [])
            weaknesses = skill_profile.get("weaknesses", [])
            skill_context = f"\nSKILL ASSESSMENT: {tier.upper()} level (score: {score:.0f}/100)"
            if strengths:
                skill_context += f"\n- Strengths: {', '.join(strengths)}"
            if weaknesses:
                skill_context += f"\n- Areas to improve: {', '.join(weaknesses)}"

            tier_instruction = {
                "low": "\nCALIBRATION: This player is a beginner. Use simple language, focus on fundamentals (spacing, shielding, not rushing in). Avoid frame data or advanced tech.",
                "mid": "\nCALIBRATION: This player is intermediate. Give specific option-select advice, mention DI, and suggest concrete counterplay. Avoid over-simplifying.",
                "high": "\nCALIBRATION: This player is advanced. Discuss option coverage, frame advantage, conditioning, and matchup-specific counterplay. Be precise.",
                "top": "\nCALIBRATION: This player is competitive-level. Discuss frame data, DI mixup percentages, micro-spacing, and reads. Assume deep game knowledge.",
            }
            skill_context += tier_instruction.get(tier, "")

        habit_context = ""
        if habit_report and habit_report.get("habits"):
            habit_lines = []
            for h in habit_report["habits"][:3]:
                habit_lines.append(f"- [{h['severity'].upper()}] {h['description']}: {h['evidence']}")
            habit_context = "\nDETECTED HABITS:\n" + "\n".join(habit_lines)

        p_name = player_char or "unknown"
        o_name = opponent_char or "unknown"

        context = f"""CHARACTERS (MANDATORY — only reference these two):
- You are playing: {p_name}
- Opponent: {o_name}
Do NOT mention any other characters by name.

Analyze this Smash Ultimate match and provide coaching. Always refer to the player as "you."

MATCH STATS:
- Duration: {mins}:{secs:02d}
- Your max damage taken: {stats.get('p1_max_percent', 0)}%
- Opponent max damage: {stats.get('p2_max_percent', 0)}%
- Result: {"You won" if you_won else "You lost"}
{char_context}{skill_context}{habit_context}

KEY MOMENTS:
- Damage spikes (you took heavy damage): {len(damage_spikes)} times
- Your stocks lost: {len(stock_losses)} at percents: {[l['percent'] for l in stock_losses]}
- Long neutral exchanges: {len(patterns.get('long_neutral', []))}

Provide:
1. A 2-3 sentence encouraging but honest summary, calibrated to the player's skill level and detected habits.
2. The single most important thing to focus on improving (specific and actionable, based on weaknesses and habits).
3. One character-specific tip: something to do more of or avoid when playing {p_name} vs {o_name}.

Keep it concise and actionable. Speak directly to the player."""

        system_content = (
            f"You are a friendly Smash Ultimate coach. Give specific, actionable advice. "
            f"CRITICAL: The player is playing {p_name} against {o_name}. "
            f"You MUST ONLY mention these two characters. Never reference any other character."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": context}
            ],
            max_tokens=350
        )

        ai_summary = response.choices[0].message.content
        ai_summary = _validate_character_names(ai_summary, player_char, opponent_char)
        
        # Enhance each tip with detailed, character-specific suggestions
        enhanced_tips = enhance_tips_with_ai(client, tips, player_char, opponent_char)
        
        return ai_summary, enhanced_tips
        
    except Exception as e:
        print(f"AI coaching error: {e}")
        return basic_summary, tips


def enhance_tips_with_ai(client, tips: list, player_char: str = None, opponent_char: str = None) -> list:
    """Add factual, grounded advice to each tip. Do not invent specific moves or events."""
    if not tips:
        return tips
    
    try:
        tips_text = "\n".join([
            f"{i+1}. [{t['type']}] @ {t['timestamp']}s: {t['message']}"
            for i, t in enumerate(tips[:8])
        ])
        
        prompt = f"""For each coaching moment below, add ONE short "Suggestion" (1-2 sentences) that is general and factual.

CRITICAL: Use ONLY the information stated in each moment. Do NOT invent specific moves (e.g. do not say "Wolf's laser" or "Cloud's limit" unless the moment explicitly says that). Do NOT assume what happened—we only know the type of event (e.g. "took damage", "lost stock"). Give general advice for that situation (e.g. defensive options, reviewing your option selection, DI, etc.). Matchup advice is OK only in general terms (e.g. "When at high percent as Cloud, look for safe escape options") without inventing the opponent's move.

Moments:
{tips_text}

Reply with a numbered list: for each number, write ONLY the extra suggestion text. Format:
1. [suggestion for moment 1]
2. [suggestion for moment 2]
..."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You add brief Smash Ultimate improvement suggestions. Be factual. Do not invent specific moves or actions that are not stated in the moment. Give general, actionable advice based only on the type of event (damage taken, stock lost, etc.)."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        
        ai_text = response.choices[0].message.content
        # Parse numbered lines and attach to corresponding tips
        import re
        lines = re.findall(r"^\s*\d+[\.\)]\s*(.+)$", ai_text, re.MULTILINE)
        for i, tip in enumerate(tips[: min(len(lines), len(tips))]):
            if i < len(lines):
                tip["ai_advice"] = lines[i].strip()
        
        return tips
    except Exception as e:
        print(f"Tip enhancement error: {e}")
        return tips


def enhance_tips_with_gemini(tips: list, player_char: str = None, opponent_char: str = None) -> list:
    """Add short, specific advice to each tip using Gemini (if available)."""
    if not tips or not GEMINI_AVAILABLE:
        return tips

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return tips

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        o_data = get_character_info(opponent_char) if opponent_char else None
        p_data = get_character_info(player_char) if player_char else None

        allowed_opponent_moves = []
        if o_data:
            allowed_opponent_moves = (
                o_data.get("key_moves", {}).get("kill", [])[:3] +
                o_data.get("key_moves", {}).get("neutral", [])[:3]
            )

        allowed_player_moves = []
        if p_data:
            allowed_player_moves = (
                p_data.get("key_moves", {}).get("neutral", [])[:3] +
                p_data.get("key_moves", {}).get("combo_starters", [])[:3]
            )

        payload = []
        for t in tips[:10]:
            payload.append({
                "type": t.get("type"),
                "timestamp": t.get("timestamp"),
                "message": t.get("message"),
                "context_hint": t.get("context_hint"),
                "your_percent": t.get("your_percent"),
                "opponent_percent": t.get("opponent_percent"),
            })

        prompt = f"""You are a Smash Ultimate coach. For each moment, write ONE short, specific suggestion (1-2 sentences).

Rules:
- Do NOT claim a specific move was used unless it appears in the allowed move list.
- You may say "watch for moves like X" ONLY if X is in the allowed list.
- If unsure, use "likely" or "may have" language.
- Keep it actionable and matchup-aware.

Player: {player_char or "Unknown"}
Opponent: {opponent_char or "Unknown"}
Allowed opponent moves: {", ".join(allowed_opponent_moves) or "None"}
Allowed player moves: {", ".join(allowed_player_moves) or "None"}

Moments (JSON):
{json.dumps(payload, ensure_ascii=True)}

Return ONLY a JSON array of suggestion strings in the same order."""

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=600,
            )
        )

        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        suggestions = json.loads(text)
        if isinstance(suggestions, list):
            for i, tip in enumerate(tips[: min(len(suggestions), len(tips))]):
                if isinstance(suggestions[i], str):
                    tip["ai_advice"] = suggestions[i].strip()

        return tips
    except Exception as e:
        print(f"Gemini tip enhancement error: {e}")
        return tips

def generate_summary(stats: dict, patterns: dict, tips: list) -> str:
    """Deprecated - use generate_ai_coaching instead."""
    summary, _ = generate_ai_coaching(stats, patterns, tips)
    return summary

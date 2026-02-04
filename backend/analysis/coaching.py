import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.patterns import find_patterns
from analysis.characters import get_character_tips, get_matchup_advice, get_character_specific_feedback, get_character_info

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


def generate_coaching(game_states: list, player_char: str = None, opponent_char: str = None, you_are_p1: bool = True) -> dict:
    """
    Analyze game states and generate coaching feedback from your perspective.
    
    Args:
        game_states: List of game state dictionaries from video processing
        player_char: Your character (optional)
        opponent_char: Opponent character (optional)
        you_are_p1: True if you are the left/red player (P1), False if you are the right/blue player (P2)
    """
    if not game_states:
        return {"summary": "No game data detected. Make sure the video shows gameplay with the HUD visible.", "tips": []}
    
    # Normalize so that "you" are always P1 in the data we analyze
    states_to_analyze = game_states if you_are_p1 else _swap_game_states(game_states)
    
    patterns = find_patterns(states_to_analyze)
    raw_stats = calculate_stats(states_to_analyze)
    
    # Resolve character identities from the normalized state (P1 = you, P2 = opponent)
    if not player_char or not opponent_char:
        auto_player, auto_opponent = detect_match_characters(states_to_analyze)
        player_char = player_char or auto_player
        opponent_char = opponent_char or auto_opponent
    
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
                "message": f"Took {_fmt_pct(damage)} damage quickly ({_fmt_pct(from_pct)} → {_fmt_pct(to_pct)}). Review what option you chose here."
            })
    
    if patterns.get("long_neutral"):
        for neutral in patterns["long_neutral"][:3]:
            tips.append({
                "timestamp": neutral["start"],
                "type": "neutral",
                "severity": "low",
                "message": f"Extended neutral ({neutral['duration']:.0f}s). Look for ways to force an approach or create openings."
            })
    
    if patterns.get("stock_losses"):
        for loss in patterns["stock_losses"]:
            stocks_left = loss.get("stocks_remaining", "?")
            percent = loss.get("percent", 0)
            tips.append({
                "timestamp": loss["timestamp"],
                "type": "stock_lost",
                "severity": "high",
                "message": f"Lost a stock at {_fmt_pct(percent)}. ({stocks_left} stocks remaining) " + get_stock_loss_advice(percent)
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
                "message": f"Nice combo dealing {_fmt_pct(damage)} damage ({_fmt_pct(from_pct)} → {_fmt_pct(to_pct)})!"
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
                "message": f"{kill_type}! Took opponent's stock at {_fmt_pct(percent)}. (Opponent has {opp_stocks_left} stocks left)"
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
                "message": f"Nice! Dealt {_fmt_pct(damage)} damage ({_fmt_pct(from_pct)} → {_fmt_pct(to_pct)})."
            })
    
    # add character-specific tips
    char_tips = get_character_specific_feedback(player_char, opponent_char, patterns)
    for char_tip in char_tips:
        char_tip["timestamp"] = 0
        char_tip["severity"] = "info"
        tips.append(char_tip)
    
    # drop tips with impossible game-state (OCR errors: 188% damage, stock lost at 188%, etc.)
    tips = _filter_impossible_tips(tips)
    
    # generate AI summary and enhance tips with factual advice only
    summary, enhanced_tips = generate_ai_coaching(raw_stats, patterns, tips, player_char, opponent_char)
    
    # Normalize stats for frontend: always "your" and "opponent" (no p1/p2)
    # Use raw stats max (unsmoothed) - this is the TRUE maximum percent reached
    # Pattern's true_max uses smoothed data which can be lower
    your_max = raw_stats.get("p1_max_percent", 0) or patterns.get("p1_true_max_percent", 0)
    opp_max = raw_stats.get("p2_max_percent", 0) or patterns.get("p2_true_max_percent", 0)
    
    print(f"[DEBUG Coaching] raw_stats p1_max: {raw_stats.get('p1_max_percent')}, p2_max: {raw_stats.get('p2_max_percent')}")
    print(f"[DEBUG Coaching] patterns p1_true_max: {patterns.get('p1_true_max_percent')}, p2_true_max: {patterns.get('p2_true_max_percent')}")
    print(f"[DEBUG Coaching] FINAL your_max: {your_max}, opp_max: {opp_max}")
    
    stats = {
        "duration": raw_stats.get("duration", 0),
        "your_max_percent": round(your_max, 1) if isinstance(your_max, float) else your_max,
        "opponent_max_percent": round(opp_max, 1) if isinstance(opp_max, float) else opp_max,
        "you_won": raw_stats.get("winner") == "p1",
        "p1_max_percent": round(your_max, 1) if isinstance(your_max, float) else your_max,
        "p2_max_percent": round(opp_max, 1) if isinstance(opp_max, float) else opp_max,
        "winner": raw_stats.get("winner"),
    }
    
    return {
        "summary": summary,
        "stats": stats,
        "tips": sorted(enhanced_tips or tips, key=lambda x: x["timestamp"]),
        "patterns": patterns,
        "characters": {
            "player": player_char,
            "opponent": opponent_char
        }
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
    
    # Method 4: If game ended (game_active=false) and stocks still tied, 
    # use last known percent - higher percent player likely got KO'd
    if winner == "unknown":
        # Find the last frame before game_active became false
        last_active_frame = None
        for s in reversed(game_states):
            if s.get("game_active", True):
                last_active_frame = s
                break
        
        if last_active_frame:
            p1_last_pct = last_active_frame.get("p1_percent")
            p2_last_pct = last_active_frame.get("p2_percent")
            
            # The player at HIGHER percent just before "GAME!" was likely KO'd
            if p1_last_pct is not None and p2_last_pct is not None:
                if p1_last_pct > p2_last_pct + 20:
                    winner = "p2"  # P1 at higher percent = P1 got KO'd = P2 wins
                    print(f"[Winner] Last active: P1={p1_last_pct}%, P2={p2_last_pct}% -> P1 likely KO'd -> P2 wins")
                elif p2_last_pct > p1_last_pct + 20:
                    winner = "p1"  # P2 at higher percent = P2 got KO'd = P1 wins
                    print(f"[Winner] Last active: P1={p1_last_pct}%, P2={p2_last_pct}% -> P2 likely KO'd -> P1 wins")
    
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

def generate_ai_coaching(stats: dict, patterns: dict, tips: list, player_char: str = None, opponent_char: str = None) -> tuple:
    """Generate AI-powered summary and enhanced tips (stats are already from 'you' = P1 perspective)."""
    
    duration = stats.get("duration", 0)
    mins = int(duration // 60)
    secs = int(duration % 60)
    you_won = stats.get("winner") == "p1"
    
    basic_summary = f"Match duration: {mins}:{secs:02d}. "
    basic_summary += "You won this game. " if you_won else "You lost this game. "
    basic_summary += f"Found {len(tips)} moments to review."
    
    if not os.getenv("OPENAI_API_KEY"):
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
        
        context = f"""Analyze this Smash Ultimate match and provide coaching. Always refer to the player as "you."

MATCH STATS:
- Duration: {mins}:{secs:02d}
- Your max damage taken: {stats.get('p1_max_percent', 0)}%
- Opponent max damage: {stats.get('p2_max_percent', 0)}%
- Result: {"You won" if you_won else "You lost"}
{char_context}

KEY MOMENTS:
- Damage spikes (you took heavy damage): {len(damage_spikes)} times
- Your stocks lost: {len(stock_losses)} at percents: {[l['percent'] for l in stock_losses]}
- Long neutral exchanges: {len(patterns.get('long_neutral', []))}

Provide:
1. A 2-3 sentence encouraging but honest summary, tailored to this matchup if characters are known.
2. The single most important thing to focus on improving (specific and actionable).
3. One character-specific tip: something to do more of or avoid when playing your character vs this opponent.

Keep it concise and actionable. Speak directly to the player."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a friendly Smash Ultimate coach. Give specific, actionable advice. Reference character names and key moves when possible."},
                {"role": "user", "content": context}
            ],
            max_tokens=350
        )
        
        ai_summary = response.choices[0].message.content
        
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

def generate_summary(stats: dict, patterns: dict, tips: list) -> str:
    """Deprecated - use generate_ai_coaching instead."""
    summary, _ = generate_ai_coaching(stats, patterns, tips)
    return summary

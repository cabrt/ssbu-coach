"""
Skill level estimator for Smash Ultimate players.
Pure computation on existing pattern data — zero API cost.

Computes 8 metrics from match patterns and game states, then produces
a weighted skill tier (low / mid / high / top) with strengths/weaknesses.
"""

from typing import Optional


# ---------------------------------------------------------------------------
# Tier boundary constants (inclusive lower bound for each tier)
# Each metric maps a raw value → 0-100 score via piecewise-linear interpolation.
# ---------------------------------------------------------------------------

def _lerp(value: float, lo: float, hi: float) -> float:
    """Linearly interpolate value from [lo, hi] into [0, 1], clamped."""
    if hi <= lo:
        return 1.0 if value >= lo else 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


# --- Individual metric scorers (each returns 0-100) ---

def _score_damage_per_opening(avg_damage: float) -> float:
    """Higher avg damage per opening → higher skill."""
    # Low ~10, Mid ~20, High ~32, Top ~45
    if avg_damage <= 5:
        return _lerp(avg_damage, 0, 5) * 15
    if avg_damage <= 15:
        return 15 + _lerp(avg_damage, 5, 15) * 20
    if avg_damage <= 25:
        return 35 + _lerp(avg_damage, 15, 25) * 20
    if avg_damage <= 40:
        return 55 + _lerp(avg_damage, 25, 40) * 25
    return 80 + _lerp(avg_damage, 40, 55) * 20


def _score_kill_efficiency(avg_kill_percent: float) -> float:
    """Lower kill percent → higher skill (closing stocks earlier)."""
    # Top ~70%, High ~90%, Mid ~115%, Low ~145%+
    if avg_kill_percent >= 160:
        return _lerp(160 - avg_kill_percent, 0, 20) * 10  # very low
    if avg_kill_percent >= 130:
        return 10 + _lerp(160 - avg_kill_percent, 0, 30) * 20
    if avg_kill_percent >= 100:
        return 30 + _lerp(130 - avg_kill_percent, 0, 30) * 25
    if avg_kill_percent >= 80:
        return 55 + _lerp(100 - avg_kill_percent, 0, 20) * 25
    return 80 + _lerp(80 - avg_kill_percent, 0, 20) * 20


def _score_edgeguard_rate(rate: float) -> float:
    """Higher edgeguard-to-kill ratio → higher skill."""
    # 0% = low, 10% = mid, 20% = high, 35%+ = top
    if rate <= 0:
        return 0
    if rate <= 0.10:
        return _lerp(rate, 0, 0.10) * 30
    if rate <= 0.20:
        return 30 + _lerp(rate, 0.10, 0.20) * 25
    if rate <= 0.35:
        return 55 + _lerp(rate, 0.20, 0.35) * 25
    return 80 + _lerp(rate, 0.35, 0.50) * 20


def _score_death_percent(avg_death: float) -> float:
    """Higher average death percent → better survival → higher skill."""
    # Low <80, Mid 80-110, High 110-140, Top 140+
    if avg_death < 50:
        return _lerp(avg_death, 0, 50) * 10
    if avg_death < 80:
        return 10 + _lerp(avg_death, 50, 80) * 20
    if avg_death < 110:
        return 30 + _lerp(avg_death, 80, 110) * 25
    if avg_death < 140:
        return 55 + _lerp(avg_death, 110, 140) * 25
    return 80 + _lerp(avg_death, 140, 170) * 20


def _score_post_death_vulnerability(avg_damage_after: float) -> float:
    """Lower damage taken in 5s after respawn → better composure → higher skill."""
    # Top <10, High 10-20, Mid 20-35, Low 35+
    if avg_damage_after >= 45:
        return 5
    if avg_damage_after >= 35:
        return 5 + _lerp(45 - avg_damage_after, 0, 10) * 15
    if avg_damage_after >= 20:
        return 20 + _lerp(35 - avg_damage_after, 0, 15) * 30
    if avg_damage_after >= 10:
        return 50 + _lerp(20 - avg_damage_after, 0, 10) * 25
    return 75 + _lerp(10 - avg_damage_after, 0, 10) * 25


def _score_combo_quality(avg_combo_damage: float) -> float:
    """Higher average combo damage → higher skill."""
    # Low <20, Mid 20-35, High 35-50, Top 50+
    if avg_combo_damage < 10:
        return _lerp(avg_combo_damage, 0, 10) * 10
    if avg_combo_damage < 20:
        return 10 + _lerp(avg_combo_damage, 10, 20) * 20
    if avg_combo_damage < 35:
        return 30 + _lerp(avg_combo_damage, 20, 35) * 25
    if avg_combo_damage < 50:
        return 55 + _lerp(avg_combo_damage, 35, 50) * 25
    return 80 + _lerp(avg_combo_damage, 50, 70) * 20


def _score_neutral_duration(avg_neutral: float) -> float:
    """Moderate neutral is healthy; excessive neutral = passive = lower skill.
    Very short neutral could mean aggressive play (good) or sloppy (ambiguous).
    """
    # Top 2-4s, High 4-6s, Mid 6-10s, Low 10s+
    if avg_neutral >= 12:
        return 10
    if avg_neutral >= 10:
        return 10 + _lerp(12 - avg_neutral, 0, 2) * 15
    if avg_neutral >= 6:
        return 25 + _lerp(10 - avg_neutral, 0, 4) * 30
    if avg_neutral >= 4:
        return 55 + _lerp(6 - avg_neutral, 0, 2) * 25
    if avg_neutral >= 2:
        return 80 + _lerp(4 - avg_neutral, 0, 2) * 15
    return 90  # very short neutral — likely aggressive, slightly ambiguous


def _score_lead_conversion(rate: float) -> float:
    """Higher lead conversion rate → higher skill."""
    # 0.3 = low, 0.5 = mid, 0.7 = high, 0.85+ = top
    return _lerp(rate, 0.2, 0.9) * 100


# ---------------------------------------------------------------------------
# Metric weights (sum to 1.0)
# ---------------------------------------------------------------------------
METRIC_WEIGHTS = {
    "damage_per_opening": 0.18,
    "kill_efficiency": 0.15,
    "edgeguard_rate": 0.10,
    "death_percent": 0.15,
    "post_death_vulnerability": 0.10,
    "combo_quality": 0.12,
    "neutral_duration": 0.08,
    "lead_conversion": 0.12,
}

METRIC_LABELS = {
    "damage_per_opening": "Damage Per Opening",
    "kill_efficiency": "Kill Efficiency",
    "edgeguard_rate": "Edgeguard Rate",
    "death_percent": "Survival / Death Percent",
    "post_death_vulnerability": "Post-Death Composure",
    "combo_quality": "Combo Quality",
    "neutral_duration": "Neutral Pacing",
    "lead_conversion": "Lead Conversion",
}

# Tier thresholds on the final weighted score (0-100)
TIER_THRESHOLDS = [
    (70, "top"),
    (50, "high"),
    (28, "mid"),
    (0, "low"),
]


# ---------------------------------------------------------------------------
# Raw metric extraction from patterns + game_states
# ---------------------------------------------------------------------------

def _compute_raw_metrics(patterns: dict, game_states: list) -> dict:
    """Extract raw metric values from pattern data."""

    # -- damage_per_opening --
    damage_dealt = patterns.get("damage_dealt", [])
    avg_damage_per_opening = (
        sum(d.get("damage", 0) for d in damage_dealt) / len(damage_dealt)
        if damage_dealt else 0
    )

    # -- kill_efficiency (average opponent percent at kill) --
    kills = patterns.get("kills", [])
    kill_percents = [k.get("opponent_percent", 0) for k in kills if k.get("opponent_percent")]
    avg_kill_percent = sum(kill_percents) / len(kill_percents) if kill_percents else 150

    # -- edgeguard_rate --
    edgeguards = patterns.get("edgeguards", [])
    total_kills = len(kills) if kills else 1
    edgeguard_rate = len(edgeguards) / total_kills if total_kills > 0 else 0

    # -- death_percent --
    stock_losses = patterns.get("stock_losses", [])
    death_percents = [sl.get("percent", 0) for sl in stock_losses if sl.get("percent")]
    avg_death_percent = sum(death_percents) / len(death_percents) if death_percents else 80

    # -- post_death_vulnerability --
    avg_post_death_damage = _compute_post_death_damage(stock_losses, game_states)

    # -- combo_quality --
    combos = patterns.get("combos", [])
    combo_damages = [c.get("damage", 0) for c in combos]
    avg_combo_damage = sum(combo_damages) / len(combo_damages) if combo_damages else 0

    # -- neutral_duration --
    long_neutral = patterns.get("long_neutral", [])
    neutral_durs = [n.get("duration", 0) for n in long_neutral]
    avg_neutral = sum(neutral_durs) / len(neutral_durs) if neutral_durs else 8

    # -- lead_conversion --
    lead_conv = _compute_lead_conversion(patterns, game_states)

    return {
        "damage_per_opening": avg_damage_per_opening,
        "kill_efficiency": avg_kill_percent,
        "edgeguard_rate": edgeguard_rate,
        "death_percent": avg_death_percent,
        "post_death_vulnerability": avg_post_death_damage,
        "combo_quality": avg_combo_damage,
        "neutral_duration": avg_neutral,
        "lead_conversion": lead_conv,
    }


def _compute_post_death_damage(stock_losses: list, game_states: list) -> float:
    """Average damage taken in the 5 seconds following each respawn."""
    if not stock_losses or not game_states:
        return 25  # neutral default

    # Build a quick timestamp→index lookup
    ts_list = [s["timestamp"] for s in game_states]

    damages = []
    for sl in stock_losses:
        # Skip final death (0 stocks remaining) — no respawn
        if sl.get("stocks_remaining", 1) == 0:
            continue
        death_ts = sl.get("timestamp", 0)
        respawn_ts = death_ts + 1.0  # ~1s invincibility
        end_ts = death_ts + 5.0

        # Find percent at respawn and at +5s
        pct_at_respawn = _percent_at_time(game_states, ts_list, respawn_ts)
        pct_at_end = _percent_at_time(game_states, ts_list, end_ts)

        if pct_at_respawn is not None and pct_at_end is not None:
            dmg = max(0, pct_at_end - pct_at_respawn)
            damages.append(dmg)

    return sum(damages) / len(damages) if damages else 25


def _percent_at_time(game_states: list, ts_list: list, target_ts: float) -> Optional[float]:
    """Find p1_percent at the game state closest to target_ts."""
    if not ts_list:
        return None
    # Binary search for closest timestamp
    lo, hi = 0, len(ts_list) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if ts_list[mid] < target_ts:
            lo = mid + 1
        else:
            hi = mid
    # Check neighbors
    best = lo
    if lo > 0 and abs(ts_list[lo - 1] - target_ts) < abs(ts_list[lo] - target_ts):
        best = lo - 1
    state = game_states[best]
    return state.get("p1_percent")


def _compute_lead_conversion(patterns: dict, game_states: list) -> float:
    """
    Approximate lead conversion: when you take a stock lead, how often
    do you maintain or extend it (vs. the opponent evening it up)?

    Returns a rate 0-1.  Falls back to 0.5 if not enough data.
    """
    kills = sorted(patterns.get("kills", []), key=lambda k: k.get("timestamp", 0))
    stock_losses = sorted(patterns.get("stock_losses", []), key=lambda s: s.get("timestamp", 0))

    # Build a timeline of stock differential changes
    events = []
    for k in kills:
        events.append((k.get("timestamp", 0), +1))  # you gained a stock lead
    for sl in stock_losses:
        events.append((sl.get("timestamp", 0), -1))  # you lost a stock lead

    events.sort(key=lambda e: e[0])

    if len(events) < 2:
        return 0.5  # not enough data

    # Walk through: track whenever you go from even/behind to ahead
    differential = 0
    lead_moments = 0
    lead_held = 0

    for i, (ts, delta) in enumerate(events):
        was_ahead = differential > 0
        differential += delta
        now_ahead = differential > 0

        if was_ahead:
            lead_moments += 1
            # If still ahead or further ahead after next event, we held the lead
            if now_ahead or differential > 0:
                lead_held += 1

    if lead_moments == 0:
        return 0.5
    return lead_held / lead_moments


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def estimate_skill_level(
    patterns: dict,
    game_states: list,
    player_char: str = None,
    opponent_char: str = None,
) -> dict:
    """
    Estimate the player's skill level from a single match.

    Returns a SkillProfile dict:
    {
        "tier": "low" | "mid" | "high" | "top",
        "overall_score": float (0-100),
        "confidence": float (0-1),
        "metrics": {name: {"raw": float, "score": float, "label": str}},
        "strengths": [str],
        "weaknesses": [str],
    }
    """
    raw = _compute_raw_metrics(patterns, game_states)

    # Score each metric
    scorers = {
        "damage_per_opening": _score_damage_per_opening,
        "kill_efficiency": _score_kill_efficiency,
        "edgeguard_rate": _score_edgeguard_rate,
        "death_percent": _score_death_percent,
        "post_death_vulnerability": _score_post_death_vulnerability,
        "combo_quality": _score_combo_quality,
        "neutral_duration": _score_neutral_duration,
        "lead_conversion": _score_lead_conversion,
    }

    metrics = {}
    for name, scorer in scorers.items():
        score = scorer(raw[name])
        metrics[name] = {
            "raw": round(raw[name], 2),
            "score": round(score, 1),
            "label": METRIC_LABELS[name],
        }

    # Weighted overall score
    overall = sum(
        metrics[name]["score"] * METRIC_WEIGHTS[name]
        for name in METRIC_WEIGHTS
    )

    # Tier assignment
    tier = "low"
    for threshold, tier_name in TIER_THRESHOLDS:
        if overall >= threshold:
            tier = tier_name
            break

    # Confidence: higher with more data points (kills, deaths, combos, etc.)
    n_events = (
        len(patterns.get("kills", []))
        + len(patterns.get("stock_losses", []))
        + len(patterns.get("combos", []))
        + len(patterns.get("damage_dealt", []))
        + len(patterns.get("edgeguards", []))
    )
    # 10+ events = high confidence, 3 = low
    confidence = min(1.0, max(0.2, n_events / 12))

    # Strengths & weaknesses (top 2 / bottom 2 by score)
    sorted_metrics = sorted(metrics.items(), key=lambda kv: kv[1]["score"], reverse=True)
    strengths = [metrics[name]["label"] for name, _ in sorted_metrics[:3] if metrics[name]["score"] >= 45]
    weaknesses = [metrics[name]["label"] for name, _ in sorted_metrics[-3:] if metrics[name]["score"] < 55]

    return {
        "tier": tier,
        "overall_score": round(overall, 1),
        "confidence": round(confidence, 2),
        "metrics": metrics,
        "strengths": strengths,
        "weaknesses": weaknesses,
    }

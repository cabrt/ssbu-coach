"""
Habit detection for Smash Ultimate match analysis.
Identifies repetitive tendencies from a single match's pattern data.

All computation is local (zero API cost).
"""

import statistics
from typing import Optional


def detect_habits(
    patterns: dict,
    game_states: list,
    player_char: str = None,
    opponent_char: str = None,
) -> dict:
    """
    Analyze patterns for repetitive tendencies.

    Returns:
    {
        "habits": [
            {
                "habit_type": str,
                "description": str,
                "evidence": str,
                "severity": "info" | "notable" | "critical",
                "occurrences": int,
                "suggestion": str,
            },
            ...
        ],
        "summary": str,
    }
    """
    habits = []

    habits += _detect_recovery_habits(patterns)
    habits += _detect_post_death_panic(patterns)
    habits += _detect_kill_fishing(patterns)
    habits += _detect_neutral_tendency(patterns, game_states)
    habits += _detect_damage_trading(patterns)
    habits += _detect_di_habits(patterns)

    # Sort by severity (critical first)
    severity_order = {"critical": 0, "notable": 1, "info": 2}
    habits.sort(key=lambda h: severity_order.get(h["severity"], 2))

    summary = _build_summary(habits)

    return {
        "habits": habits,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Individual habit detectors
# ---------------------------------------------------------------------------

def _detect_recovery_habits(patterns: dict) -> list:
    """
    Check if the player repeatedly dies in similar situations
    (similar percent ranges, frequent edgeguarding by opponent).
    """
    habits = []
    got_eg = patterns.get("got_edgeguarded", [])
    stock_losses = patterns.get("stock_losses", [])

    # 1. Repeatedly getting edgeguarded
    if len(got_eg) >= 2:
        death_percents = [eg.get("your_death_percent", 0) for eg in got_eg]
        avg_pct = sum(death_percents) / len(death_percents) if death_percents else 0
        habits.append({
            "habit_type": "recovery_predictable",
            "description": "Predictable recovery pattern",
            "evidence": (
                f"Got edgeguarded {len(got_eg)} times "
                f"(avg death at {avg_pct:.0f}%). "
                "Opponent is reading your recovery options."
            ),
            "severity": "critical" if len(got_eg) >= 3 else "notable",
            "occurrences": len(got_eg),
            "suggestion": (
                "Mix up recovery timing: sometimes go high, sometimes low, "
                "delay your double jump, or drift to ledge vs. stage. "
                "Don't always recover the same way."
            ),
        })

    # 2. Dying at similar percents (narrow range)
    if len(stock_losses) >= 3:
        percents = [sl.get("percent", 0) for sl in stock_losses if sl.get("percent")]
        if len(percents) >= 3:
            stdev = statistics.stdev(percents)
            avg = statistics.mean(percents)
            if stdev < 20 and avg < 120:
                habits.append({
                    "habit_type": "consistent_death_range",
                    "description": "Dying in a narrow percent range",
                    "evidence": (
                        f"Lost {len(percents)} stocks all around "
                        f"{avg:.0f}% (spread: {stdev:.0f}%). "
                        "This suggests the opponent is reliably converting "
                        "in the same situation."
                    ),
                    "severity": "notable",
                    "occurrences": len(percents),
                    "suggestion": (
                        "Vary your DI and defensive options at this percent range. "
                        "If you always DI the same way or pick the same escape option, "
                        "the opponent will keep converting."
                    ),
                })

    return habits


def _detect_post_death_panic(patterns: dict) -> list:
    """Check for taking heavy damage immediately after respawning."""
    habits = []
    after_death = patterns.get("after_death_phases", [])
    if not after_death:
        return habits

    panic_phases = [p for p in after_death if p.get("behavior") == "panic"]

    if len(panic_phases) >= 2:
        avg_dmg = statistics.mean(
            [p.get("damage_taken", 0) for p in panic_phases]
        )
        habits.append({
            "habit_type": "post_death_panic",
            "description": "Taking heavy damage after respawning",
            "evidence": (
                f"In {len(panic_phases)} of {len(after_death)} respawns, "
                f"you took an average of {avg_dmg:.0f}% damage within 5 seconds. "
                "This suggests rushing in or panicking after losing a stock."
            ),
            "severity": "critical" if len(panic_phases) >= 3 else "notable",
            "occurrences": len(panic_phases),
            "suggestion": (
                "After respawning, use your invincibility frames wisely. "
                "Take a moment to assess, then re-engage safely. "
                "Don't dash-attack or approach recklessly out of frustration."
            ),
        })

    return habits


def _detect_kill_fishing(patterns: dict) -> list:
    """
    Check if all kills happen at similar percents (narrow spread),
    suggesting the player only goes for one kill option.
    """
    habits = []
    kills = patterns.get("kills", [])
    if len(kills) < 3:
        return habits

    kill_percents = [
        k.get("opponent_percent", 0) for k in kills if k.get("opponent_percent")
    ]
    if len(kill_percents) < 3:
        return habits

    stdev = statistics.stdev(kill_percents)
    avg = statistics.mean(kill_percents)

    # Very tight clustering suggests one-dimensional kill confirms
    if stdev < 15:
        habits.append({
            "habit_type": "kill_fishing",
            "description": "One-dimensional kill confirms",
            "evidence": (
                f"All {len(kill_percents)} kills were around {avg:.0f}% "
                f"(spread: {stdev:.0f}%). "
                "This suggests relying on a single kill setup."
            ),
            "severity": "notable",
            "occurrences": len(kill_percents),
            "suggestion": (
                "Diversify your kill options. Practice different kill confirms "
                "at various percents (edge traps, raw smash attacks, aerials, "
                "edgeguards) to become less predictable."
            ),
        })

    return habits


def _detect_neutral_tendency(patterns: dict, game_states: list) -> list:
    """
    Detect if the player is overly passive or aggressive in neutral.
    Uses damage_dealt vs damage_spikes (damage_taken) ratio and
    momentum swings.
    """
    habits = []

    damage_dealt = patterns.get("damage_dealt", [])
    damage_taken = patterns.get("damage_spikes", [])
    momentum = patterns.get("momentum_swings", [])

    total_dealt_events = len(damage_dealt)
    total_taken_events = len(damage_taken)

    if total_dealt_events + total_taken_events < 4:
        return habits  # not enough data

    # Ratio of dealt to taken events
    ratio = total_dealt_events / max(1, total_taken_events)

    if ratio < 0.5 and total_taken_events >= 4:
        habits.append({
            "habit_type": "passive_neutral",
            "description": "Passive in neutral — taking more hits than landing",
            "evidence": (
                f"Landed {total_dealt_events} significant hits but took "
                f"{total_taken_events} damage spikes. "
                "Opponents are consistently winning neutral."
            ),
            "severity": "notable" if total_taken_events >= 5 else "info",
            "occurrences": total_taken_events,
            "suggestion": (
                "Work on spacing and approach timing. Use safe pokes "
                "to test the opponent's reactions before committing. "
                "Don't just wait — use movement to create openings."
            ),
        })
    elif ratio > 2.5 and total_dealt_events >= 5:
        # Very aggressive — might be overextending
        habits.append({
            "habit_type": "overaggressive_neutral",
            "description": "Very aggressive neutral — may be overcommitting",
            "evidence": (
                f"Landed {total_dealt_events} hits vs {total_taken_events} taken. "
                "While winning neutral, heavy aggression can become predictable."
            ),
            "severity": "info",
            "occurrences": total_dealt_events,
            "suggestion": (
                "Great neutral pressure, but check if you're getting punished "
                "for overextending. Mix in some bait-and-punish play to keep "
                "the opponent guessing."
            ),
        })

    # Check for rapid momentum swings (trading)
    adv_swings = [m for m in momentum if m.get("type") == "advantage"]
    dis_swings = [m for m in momentum if m.get("type") == "disadvantage"]
    if len(adv_swings) >= 2 and len(dis_swings) >= 2:
        # Lots of back-and-forth
        total_swings = len(adv_swings) + len(dis_swings)
        if total_swings >= 5:
            habits.append({
                "habit_type": "momentum_volatile",
                "description": "Volatile momentum — frequent advantage/disadvantage swaps",
                "evidence": (
                    f"{total_swings} momentum swings detected. "
                    "The match had rapid back-and-forth exchanges."
                ),
                "severity": "info",
                "occurrences": total_swings,
                "suggestion": (
                    "Focus on maintaining advantage state longer. "
                    "After winning neutral, keep stage control and pursue "
                    "safe follow-ups instead of resetting to neutral."
                ),
            })

    return habits


def _detect_damage_trading(patterns: dict) -> list:
    """Detect if the player frequently trades damage instead of clean hits."""
    habits = []
    momentum = patterns.get("momentum_swings", [])

    # Look for rapid alternation between advantage and disadvantage
    if len(momentum) < 4:
        return habits

    trade_count = 0
    for i in range(1, len(momentum)):
        prev_type = momentum[i - 1].get("type")
        curr_type = momentum[i].get("type")
        time_gap = momentum[i].get("timestamp", 0) - momentum[i - 1].get("timestamp", 0)

        # A "trade" is when you go from advantage to disadvantage (or vice versa)
        # within 3 seconds
        if prev_type != curr_type and time_gap < 3:
            trade_count += 1

    if trade_count >= 3:
        habits.append({
            "habit_type": "damage_trading",
            "description": "Frequent damage trades",
            "evidence": (
                f"{trade_count} rapid momentum reversals detected. "
                "You're frequently trading hits instead of securing clean openings."
            ),
            "severity": "notable" if trade_count >= 4 else "info",
            "occurrences": trade_count,
            "suggestion": (
                "After landing a hit, focus on safe follow-ups rather than "
                "going for another immediate aggressive option. "
                "Trading damage favors the opponent when they're at lower percent."
            ),
        })

    return habits


def _detect_di_habits(patterns: dict) -> list:
    """
    Infer possible DI issues from death percent patterns.
    If the player consistently dies early (below expected kill percent),
    they may have DI problems.
    """
    habits = []
    stock_losses = patterns.get("stock_losses", [])
    if len(stock_losses) < 2:
        return habits

    early_deaths = [
        sl for sl in stock_losses
        if sl.get("percent") and sl["percent"] < 80
        and sl.get("stocks_remaining", 1) > 0  # not the final game-ender
    ]

    if len(early_deaths) >= 2:
        percents = [sl["percent"] for sl in early_deaths]
        avg = statistics.mean(percents)
        habits.append({
            "habit_type": "early_deaths",
            "description": "Dying at low percent — possible DI or positioning issue",
            "evidence": (
                f"Lost {len(early_deaths)} stocks below 80% "
                f"(avg: {avg:.0f}%). "
                "This can indicate poor DI, bad recovery habits, "
                "or getting caught by kill setups."
            ),
            "severity": "critical" if len(early_deaths) >= 3 else "notable",
            "occurrences": len(early_deaths),
            "suggestion": (
                "Practice survival DI (hold away from the blast zone). "
                "At these percents, you should be surviving most hits. "
                "Review what killed you and practice the correct DI for those moves."
            ),
        })

    return habits


# ---------------------------------------------------------------------------
# Summary builder
# ---------------------------------------------------------------------------

def _build_summary(habits: list) -> str:
    if not habits:
        return "No significant habits detected in this match."

    critical = [h for h in habits if h["severity"] == "critical"]
    notable = [h for h in habits if h["severity"] == "notable"]

    parts = []
    if critical:
        parts.append(
            f"{len(critical)} critical habit{'s' if len(critical) > 1 else ''} found: "
            + ", ".join(h["description"].lower() for h in critical)
            + "."
        )
    if notable:
        parts.append(
            f"{len(notable)} notable pattern{'s' if len(notable) > 1 else ''}: "
            + ", ".join(h["description"].lower() for h in notable)
            + "."
        )

    return " ".join(parts) if parts else "Minor tendencies detected — keep playing to build a clearer picture."

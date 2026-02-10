"""
Multi-frame event context extraction for enhanced vision analysis.

For the top N most impactful events, extracts 4-5 frame sequences
(before/during/after the event) so GPT-4o can analyze *progression*
rather than a single snapshot.

Follows the same cv2 extraction pattern as offstage_classifier.py.
"""

import base64
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple


# Frame offsets per event type (seconds relative to event timestamp)
EVENT_FRAME_OFFSETS = {
    "stock_lost": [-2.0, -1.0, -0.5, 0.0],
    "stock_taken": [-2.0, -1.5, -1.0, -0.5, 0.0],
    "damage_taken": [-1.5, -1.0, -0.5, 0.0, 0.5],
    "combo": [-1.0, -0.5, 0.0, 0.5, 1.0],
    "edgeguard": [-2.0, -1.5, -1.0, -0.5, 0.0],
    "got_edgeguarded": [-2.0, -1.0, -0.5, 0.0],
}

# Default offsets for any event type not listed above
DEFAULT_OFFSETS = [-1.5, -1.0, -0.5, 0.0]

# Budget: max events to extract multi-frame sequences for
MAX_MULTI_FRAME_EVENTS = 8

# Max width to resize frames to (keeps API cost down)
MAX_FRAME_WIDTH = 1280

# JPEG quality for encoding
JPEG_QUALITY = 85


def extract_event_frame_sequences(
    video_path: str,
    tips: list,
    max_events: int = MAX_MULTI_FRAME_EVENTS,
) -> list:
    """
    Extract multi-frame sequences for the most impactful tips/events.

    Args:
        video_path: Path to the gameplay video.
        tips: List of tip dicts (each has 'timestamp', 'type', 'severity').
        max_events: Max number of events to extract frames for.

    Returns:
        List of EventFrameSequence dicts:
        [
            {
                "tip_index": int,        # index into the original tips list
                "timestamp": float,
                "type": str,
                "frames": [              # ordered list of frame snapshots
                    {
                        "offset": float,        # seconds relative to event
                        "abs_time": float,      # absolute video time
                        "image_b64": str,       # base64-encoded JPEG
                    },
                    ...
                ],
            },
            ...
        ]
    """
    if not video_path or not Path(video_path).exists() or not tips:
        return []

    # Prioritize tips: stock_lost > got_edgeguarded > damage_taken(high) > edgeguard > combo > others
    priority_order = {
        "stock_lost": 0,
        "got_edgeguarded": 1,
        "damage_taken": 2,
        "edgeguard": 3,
        "combo": 4,
        "stock_taken": 5,
    }
    severity_boost = {"high": -0.5, "medium": 0, "positive": 0.5, "low": 1, "info": 2}

    scored_tips = []
    for idx, tip in enumerate(tips):
        tip_type = tip.get("type", "")
        base_priority = priority_order.get(tip_type, 6)
        sev = severity_boost.get(tip.get("severity", ""), 1)
        scored_tips.append((base_priority + sev, idx, tip))

    scored_tips.sort(key=lambda x: x[0])
    selected = scored_tips[:max_events]

    if not selected:
        return []

    # Open video once, extract all frames
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if video_fps <= 0 or total_frames <= 0:
        cap.release()
        return []

    video_duration = total_frames / video_fps

    results = []
    for _, tip_idx, tip in selected:
        ts = tip.get("timestamp", 0)
        tip_type = tip.get("type", "")
        offsets = EVENT_FRAME_OFFSETS.get(tip_type, DEFAULT_OFFSETS)

        frames = []
        for offset in offsets:
            abs_time = ts + offset
            if abs_time < 0 or abs_time > video_duration:
                continue

            frame_num = int(abs_time * video_fps)
            frame_num = max(0, min(frame_num, total_frames - 1))

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret:
                continue

            # Resize if too large
            if frame.shape[1] > MAX_FRAME_WIDTH:
                scale = MAX_FRAME_WIDTH / frame.shape[1]
                frame = cv2.resize(
                    frame, (MAX_FRAME_WIDTH, int(frame.shape[0] * scale))
                )

            _, buf = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
            )
            b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

            frames.append({
                "offset": offset,
                "abs_time": round(abs_time, 2),
                "image_b64": b64,
            })

        if frames:
            results.append({
                "tip_index": tip_idx,
                "timestamp": ts,
                "type": tip_type,
                "frames": frames,
            })

    cap.release()
    return results


def build_sequence_vision_prompt(
    event_seq: dict,
    tip: dict,
    skill_tier: str = None,
    player_char: str = None,
    opponent_char: str = None,
    game_states: list = None,
    you_are_p1: bool = True,
) -> Tuple[str, list]:
    """
    Build a vision prompt + image parts for a multi-frame event sequence.

    Move identification is done algorithmically from damage data (not by GPT-4o).
    The vision model focuses on what it's good at: positioning, spacing, stage
    control, DI, and coaching advice.

    Returns (text_prompt, image_parts) where image_parts is a list of
    dicts with {"mime_type": "image/jpeg", "data": base64_str}.
    """
    from analysis.move_data import (
        compute_damage_context, format_damage_deltas_for_prompt,
    )

    tip_type = event_seq.get("type", "")
    frames = event_seq.get("frames", [])
    timestamp = event_seq.get("timestamp", 0)

    # Build context string
    char_ctx = ""
    if player_char:
        char_ctx += f"Your character: {player_char}. "
    if opponent_char:
        char_ctx += f"Opponent: {opponent_char}. "

    tier_ctx = ""
    if skill_tier:
        tier_guidance = {
            "low": "The player is a beginner. Focus on fundamental concepts: basic spacing, shield usage, and simple punishes.",
            "mid": "The player has intermediate skills. Discuss specific defensive options, DI mixups, and recognizable setups.",
            "high": "The player is advanced. Analyze option coverage, frame advantage situations, and optimal punish routes.",
            "top": "The player is competitive-level. Discuss conditioning reads, DI mixup percentages, and frame-specific interactions.",
        }
        tier_ctx = tier_guidance.get(skill_tier, "")

    # Coaching-focused prompts — moves are already identified in WHAT HAPPENED
    type_prompts = {
        "stock_lost": (
            "The player lost a stock. The moves used are identified in WHAT HAPPENED below. "
            "FIRST: Identify the opponent's ACTUAL FINISHING MOVE (the move that sent the player flying to their death) by looking at the frames carefully. "
            "A spike/meteor (downward hit while offstage) looks different from a grounded kill move. "
            "If the player died offstage at low percent, it was very likely a spike (dair) or meteor smash — NOT a grounded kill move. "
            "State it at the start in format: KILL MOVE: [move name]\n"
            "Then focus your analysis on:\n"
            "1. What positioning or spacing mistake led to getting hit?\n"
            "2. What could they have done differently — better DI, different recovery path, avoid the situation entirely?\n"
            "3. Give one specific, actionable tip to avoid this death next time."
        ),
        "damage_taken": (
            "The player took significant damage. The moves are identified below. "
            "Focus your analysis on:\n"
            "1. What was the player doing before getting hit — approaching unsafely, landing predictably, whiffing a move?\n"
            "2. What defensive option would have avoided this — shield, spot dodge, spacing differently?\n"
            "3. Give one specific, actionable tip."
        ),
        "combo": (
            "The player executed a combo. The moves are identified below. "
            "Focus your analysis on:\n"
            "1. Look at the positioning across frames — was the spacing and timing clean?\n"
            "2. Did they drop the combo early or extend it well? What follow-ups were available?\n"
            "3. Give one specific tip for optimizing this combo at this percent range."
        ),
        "edgeguard": (
            "The player went offstage for an edgeguard. The moves are identified below. "
            "Focus your analysis on:\n"
            "1. Was this a safe edgeguard choice given the opponent's recovery options?\n"
            "2. Look at positioning — could they have covered more options or been safer?\n"
            "3. Give one specific tip for edgeguarding this opponent."
        ),
        "got_edgeguarded": (
            "The player got edgeguarded. The moves are identified below. "
            "Focus your analysis on:\n"
            "1. Was the player's recovery path predictable from the frames?\n"
            "2. What alternative recovery route would have been safer?\n"
            "3. Give one specific tip for recovering in this situation."
        ),
        "stock_taken": (
            "The player took the opponent's stock. The moves are identified below. "
            "Focus your analysis on:\n"
            "1. Look at the setup — how did they create the kill opportunity?\n"
            "2. Was the opponent's DI readable from their position in the frames?\n"
            "3. Is this a repeatable setup? Give one specific tip for securing kills earlier."
        ),
    }

    analysis_prompt = type_prompts.get(tip_type, (
        "Analyze the positioning and player decisions in this sequence. "
        "The moves are already identified below — focus on spacing, stage control, and actionable advice."
    ))

    # Compute damage deltas from game states — moves are identified algorithmically
    damage_section = ""
    if game_states and frames:
        frame_times = [f["abs_time"] for f in frames]
        deltas = compute_damage_context(game_states, frame_times, you_are_p1)
        damage_section = format_damage_deltas_for_prompt(
            deltas, player_char=player_char, opponent_char=opponent_char,
            event_type=tip_type,
        )

    # Add opponent's move list for stock_lost to help vision model identify the kill move
    kill_move_context = ""
    if tip_type == "stock_lost" and opponent_char:
        try:
            from analysis.characters import get_character_info
            o_data = get_character_info(opponent_char)
            if o_data:
                all_moves = []
                for cat in ("kill", "neutral", "combo_starters"):
                    all_moves.extend(o_data.get("key_moves", {}).get(cat, []))
                # Always include dair/dsmash/fsmash as common kill moves
                for m in ["dair", "down air", "down smash", "forward smash"]:
                    if m not in [x.lower() for x in all_moves]:
                        all_moves.append(m)
                if all_moves:
                    kill_move_context = f"\n{opponent_char.upper()}'s KNOWN MOVES (pick from these): {', '.join(all_moves[:12])}\n"
        except Exception:
            pass

    text = f"""You are a Super Smash Bros Ultimate coach analyzing {len(frames)} gameplay frames around a key moment at {timestamp:.1f}s.

{char_ctx}{tier_ctx}

Event: {tip.get('message', tip_type)}

{damage_section}
{kill_move_context}
{analysis_prompt}

IMPORTANT RULES:
- The moves listed in WHAT HAPPENED are identified from verified damage data. TRUST them — do not contradict or re-identify moves.
- Focus on POSITIONING, SPACING, STAGE CONTROL, and PLAYER DECISIONS visible in the frames.
- Look at how positions change ACROSS frames to understand the flow of the interaction.
- Give specific, actionable advice — not generic platitudes.
- Keep your response to 2-3 sentences.

Gameplay frames (in chronological order):
"""

    image_parts = []
    for i, frame in enumerate(frames):
        text += f"\n--- Frame {i + 1} (t={frame['abs_time']:.1f}s, offset={frame['offset']:+.1f}s) ---"
        image_parts.append({
            "mime_type": "image/jpeg",
            "data": frame["image_b64"],
        })

    return text, image_parts

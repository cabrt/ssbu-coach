"""
Lightweight offstage/onstage classifier for death context.
Runs ONLY on short windows around candidate death events to gate edgeguard detection.
Uses Gemini Vision on gameplay-area crops; batches frames to limit API calls.
"""
import os
import json
import base64
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple

# Optional Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Threshold: victim must be offstage in >= this fraction of pre-death frames to call it edgeguard
OFFSTAGE_RATIO_THRESHOLD = 0.4
# If victim is on ledge in >= this fraction, treat as ledge hang (not pure offstage recovery)
LEDGE_DOMINANT_THRESHOLD = 0.6

WINDOW_LOOKBACK_SEC = 1.5
WINDOW_LOOKAHEAD_SEC = 0.2
WINDOW_FPS = 10
MAX_FRAMES_PER_CALL = 8


def classify_death_context(
    video_path: str,
    candidate_deaths: List[dict],
    you_are_p1: bool = True,
) -> List[dict]:
    """
    For each candidate death (from patterns: edgeguards or got_edgeguarded),
    extract a short window, run vision classifier, return per-candidate result.

    candidate_deaths: list of {
        "timestamp": float,
        "victim": "p1" | "p2",  # who died
        "type": "edgeguard" | "got_edgeguarded",
    }
    Returns: list of {
        "timestamp", "victim", "type",
        "victim_offstage_ratio": float,
        "victim_ledge_ratio": float,
        "is_edgeguard": bool,
        "debug": str,
    }
    """
    if not GEMINI_AVAILABLE or not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        # No API: treat all as unknown -> don't label as edgeguard (safe)
        return [
            {
                **c,
                "victim_offstage_ratio": 0.0,
                "victim_ledge_ratio": 0.0,
                "is_edgeguard": False,
                "debug": "no_api",
            }
            for c in candidate_deaths
        ]

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    results = []
    for cand in candidate_deaths:
        ts = cand.get("timestamp", 0)
        victim = cand.get("victim", "p2")
        cand_type = cand.get("type", "got_edgeguarded")

        # Extract frames in [ts - 1.5, ts + 0.2] at WINDOW_FPS
        frames_with_t = _extract_window_frames(
            video_path,
            death_time=ts,
            lookback=WINDOW_LOOKBACK_SEC,
            lookahead=WINDOW_LOOKAHEAD_SEC,
            fps=WINDOW_FPS,
        )
        if not frames_with_t:
            results.append({
                **cand,
                "victim_offstage_ratio": 0.0,
                "victim_ledge_ratio": 0.0,
                "is_edgeguard": False,
                "debug": "no_frames",
            })
            print(f"[OffstageClassifier] {cand_type} @ {ts:.1f}s: no frames extracted")
            continue

        # Crop to gameplay area (remove HUD): center ~70% of height, full width
        cropped = []
        for t, frame_bgr in frames_with_t:
            crop = _crop_gameplay_region(frame_bgr)
            _, buf = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
            cropped.append((t, buf.tobytes()))

        # Batch into chunks of MAX_FRAMES_PER_CALL
        all_p1 = []
        all_p2 = []
        for i in range(0, len(cropped), MAX_FRAMES_PER_CALL):
            chunk = cropped[i : i + MAX_FRAMES_PER_CALL]
            p1_states, p2_states = _run_vision_classifier(chunk)
            all_p1.extend(p1_states)
            all_p2.extend(p2_states)

        # Victim is in analysis space (p1=you, p2=opponent). In frame, P1=left, P2=right.
        # Convert to video space: you_are_p1 -> you=P1 left, opp=P2 right; else you=P2 right, opp=P1 left
        video_victim = "p1" if (victim == "p1" and you_are_p1) or (victim == "p2" and not you_are_p1) else "p2"
        victim_states = all_p1 if video_victim == "p1" else all_p2
        offstage_count = sum(1 for s in victim_states if s == "offstage")
        ledge_count = sum(1 for s in victim_states if s == "on_ledge")
        onstage_count = sum(1 for s in victim_states if s == "onstage")
        n = len(victim_states) or 1
        victim_offstage_ratio = offstage_count / n
        victim_ledge_ratio = ledge_count / n

        is_edgeguard = (
            victim_offstage_ratio >= OFFSTAGE_RATIO_THRESHOLD
            and victim_ledge_ratio < LEDGE_DOMINANT_THRESHOLD
        )
        debug = (
            f"offstage_ratio={victim_offstage_ratio:.2f} ledge_ratio={victim_ledge_ratio:.2f} "
            f"n={n} -> {'edgeguard' if is_edgeguard else 'onstage_kill'}"
        )
        print(f"[OffstageClassifier] {cand_type} @ {ts:.1f}s: {debug}")

        results.append({
            **cand,
            "victim_offstage_ratio": round(victim_offstage_ratio, 3),
            "victim_ledge_ratio": round(victim_ledge_ratio, 3),
            "is_edgeguard": is_edgeguard,
            "debug": debug,
        })
    return results


def _crop_gameplay_region(frame: np.ndarray) -> np.ndarray:
    """Crop to gameplay area: drop top 10% and bottom 25% (HUD). Keep center 65% height."""
    h, w = frame.shape[:2]
    y0 = int(h * 0.10)
    y1 = int(h * 0.75)
    return frame[y0:y1, :].copy()


def _extract_window_frames(
    video_path: str,
    death_time: float,
    lookback: float,
    lookahead: float,
    fps: float,
) -> List[Tuple[float, np.ndarray]]:
    """Extract frames in [death_time - lookback, death_time + lookahead] at given fps."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        cap.release()
        return []

    start_t = max(0.0, death_time - lookback)
    end_t = death_time + lookahead
    out = []
    t = start_t
    while t <= end_t:
        frame_num = int(t * video_fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if ret:
            if frame.shape[1] > 1280:
                scale = 1280 / frame.shape[1]
                frame = cv2.resize(frame, (1280, int(frame.shape[0] * scale)))
            out.append((t, frame))
        t += 1.0 / fps
    cap.release()
    return out


def _run_vision_classifier(frames_with_bytes: List[Tuple[float, bytes]]) -> Tuple[List[str], List[str]]:
    """Call Gemini with gameplay crops; return (p1_states, p2_states) per frame. Each state: onstage | offstage | on_ledge | unknown."""
    if not frames_with_bytes or not GEMINI_AVAILABLE:
        return ([], [])

    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt_parts = [
        """You are analyzing Super Smash Bros Ultimate gameplay. For each image, classify each player's position:
- "onstage": character is clearly on the main stage platform (not in the air off the edge)
- "offstage": character is off the stage (in the air or below stage, recovering or being hit)
- "on_ledge": character is hanging on the ledge (grabbing ledge)
- "unknown": cannot tell (obscured, UI, or ambiguous)

Player 1 (P1) is typically on the LEFT side of the stage, Player 2 (P2) on the RIGHT.
Return ONLY a JSON array with one object per image, each with keys: "p1_state", "p2_state".
Use only those exact strings: "onstage", "offstage", "on_ledge", "unknown".

Example: [{"p1_state": "onstage", "p2_state": "offstage"}, {"p1_state": "onstage", "p2_state": "on_ledge"}]

Images (one per frame in order):
"""
    ]
    for i, (t, b) in enumerate(frames_with_bytes):
        prompt_parts.append(f"\n--- Frame {i+1} (t={t:.1f}s) ---")
        prompt_parts.append({
            "mime_type": "image/jpeg",
            "data": base64.b64encode(b).decode("utf-8"),
        })
    prompt_parts.append("\n\nReturn ONLY the JSON array:")

    try:
        response = model.generate_content(
            prompt_parts,
            generation_config=genai.types.GenerationConfig(temperature=0.0, max_output_tokens=1024),
        )
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        arr = json.loads(text)
        p1_states = []
        p2_states = []
        for obj in arr:
            p1 = (obj.get("p1_state") or "unknown").strip().lower()
            p2 = (obj.get("p2_state") or "unknown").strip().lower()
            if p1 not in ("onstage", "offstage", "on_ledge", "unknown"):
                p1 = "unknown"
            if p2 not in ("onstage", "offstage", "on_ledge", "unknown"):
                p2 = "unknown"
            p1_states.append(p1)
            p2_states.append(p2)
        return (p1_states, p2_states)
    except Exception as e:
        print(f"[OffstageClassifier] Vision error: {e}")
        return (["unknown"] * len(frames_with_bytes), ["unknown"] * len(frames_with_bytes))


def refine_edgeguards_with_vision(
    video_path: Optional[str],
    patterns: dict,
    you_are_p1: bool = True,
) -> None:
    """
    Run offstage classifier on current edgeguards and got_edgeguarded.
    Filter to only keep events where victim was actually offstage (victim_offstage_ratio >= 0.4).
    Modifies patterns in place.
    """
    if not video_path or not os.path.exists(video_path):
        # No video: leave lists as-is (current heuristic only)
        return

    candidates = []
    for eg in patterns.get("edgeguards", []):
        candidates.append({
            "timestamp": eg.get("timestamp", 0),
            "victim": "p2",
            "type": "edgeguard",
            "payload": eg,
        })
    for eg in patterns.get("got_edgeguarded", []):
        candidates.append({
            "timestamp": eg.get("timestamp", 0),
            "victim": "p1",
            "type": "got_edgeguarded",
            "payload": eg,
        })
    if not candidates:
        return

    results = classify_death_context(video_path, candidates, you_are_p1=you_are_p1)

    edgeguards_keep = []
    got_keep = []
    for r in results:
        if not r.get("is_edgeguard", False):
            continue
        if r.get("type") == "edgeguard":
            edgeguards_keep.append(r.get("payload"))
        else:
            got_keep.append(r.get("payload"))

    patterns["edgeguards"] = edgeguards_keep
    patterns["got_edgeguarded"] = got_keep

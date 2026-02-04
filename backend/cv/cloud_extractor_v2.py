"""
Cloud-based frame extraction v2 - Simplified and robust.

Sends full frames to Gemini and asks it to read the exact values.
No complex cropping - let the AI find the numbers.
"""
import cv2
import base64
import json
import os
import sys
from pathlib import Path
# ThreadPoolExecutor removed - using sequential processing to avoid rate limits
from dataclasses import dataclass
from typing import List, Optional, Callable
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def extract_frames_cloud_v2(
    video_path: str,
    fps_sample: float = 1.0,  # 1 fps to reduce API calls (rate limits)
    progress_callback: Callable[[float], None] = None,
    max_duration: int = None,
    batch_size: int = 12,  # Larger batches to reduce API calls
    max_parallel_batches: int = 1,  # Sequential to avoid rate limits
) -> List[dict]:
    """
    Extract game states using Gemini vision.
    
    Simplified approach:
    - Send full frames (no complex cropping)
    - Smaller batches for better accuracy
    - Clear prompting for exact number reading
    """
    if not GEMINI_AVAILABLE:
        raise ImportError("google-generativeai required")
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY required")
    
    genai.configure(api_key=api_key)
    
    print(f"[CloudExtractor v2] Processing {video_path}")
    print(f"[CloudExtractor v2] Sample rate: {fps_sample} fps")
    
    # Extract frames
    frames = _extract_frames(video_path, fps_sample, max_duration)
    print(f"[CloudExtractor v2] Extracted {len(frames)} frames")
    
    if not frames:
        return []
    
    import time as time_module
    
    # Create batches
    batches = [frames[i:i+batch_size] for i in range(0, len(frames), batch_size)]
    print(f"[CloudExtractor v2] Processing {len(batches)} batches SEQUENTIALLY with 4s delay")
    
    # Process batches SEQUENTIALLY with delay to avoid rate limits
    all_states = []
    
    for batch_idx, batch in enumerate(batches):
        try:
            states = _process_batch(batch, batch_idx)
            all_states.extend(states)
            
            if progress_callback:
                progress_callback((batch_idx + 1) / len(batches) * 0.9)
            
            print(f"[CloudExtractor v2] Batch {batch_idx + 1}/{len(batches)}: {len(states)} states")
            
            # Wait between batches to respect rate limits (Gemini free tier: ~15 req/min)
            if batch_idx < len(batches) - 1:
                time_module.sleep(5)  # 5 seconds between batches = 12 req/min (safe)
                
        except Exception as e:
            print(f"[CloudExtractor v2] Batch {batch_idx} error: {e}")
    
    # Sort by timestamp
    all_states.sort(key=lambda s: s["timestamp"])
    
    # Validation pass
    print("[CloudExtractor v2] Running validation pass...")
    validated = _validate_states(all_states)
    
    if progress_callback:
        progress_callback(1.0)
    
    print(f"[CloudExtractor v2] Complete: {len(validated)} states")
    
    return validated


def _extract_frames(video_path: str, fps_sample: float, max_duration: Optional[int]) -> List[tuple]:
    """Extract frames from video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps
    
    if max_duration:
        duration = min(duration, max_duration)
        total_frames = int(duration * video_fps)
    
    frame_interval = int(video_fps / fps_sample) if fps_sample < video_fps else 1
    
    frames = []
    frame_num = 0
    
    while frame_num < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_num % frame_interval == 0:
            timestamp = frame_num / video_fps
            
            # Skip very dark frames
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if np.mean(gray) > 20:
                # Resize and encode
                h, w = frame.shape[:2]
                if w > 1280:
                    scale = 1280 / w
                    frame = cv2.resize(frame, (1280, int(h * scale)))
                
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                frames.append((timestamp, buffer.tobytes()))
        
        frame_num += 1
    
    cap.release()
    return frames


def _process_batch(frames: List[tuple], batch_idx: int, max_retries: int = 3) -> List[dict]:
    """Process a batch of frames with Gemini, with retry logic for rate limits."""
    import time as time_module
    import random
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt_parts = [
        """You are analyzing Super Smash Bros Ultimate gameplay screenshots.

YOUR TASK: Extract the EXACT damage percentages and stock counts shown on screen.

WHAT TO LOOK FOR:
- Damage percentages are large colored numbers (red/orange/yellow) at the BOTTOM of the screen
- Player 1 (P1) HUD is on the LEFT side, Player 2 (P2) HUD is on the RIGHT side
- Stock icons are small character portrait icons below/near the damage percent
- Count the stock icons carefully: 0, 1, 2, or 3

DETECTING "GAME!" END SCREENS:
- "GAME!" appears in large text when the match ENDS
- On GAME! screens, one player ALWAYS has 0 stocks (they lost)
- The other player has 1, 2, or 3 stocks (they won)
- Look carefully at where stock icons SHOULD be - if a player's stock area is EMPTY, they have 0 stocks
- The losing player's stock icons will be GONE or show 0

CRITICAL - STOCK READING:
- Stock icons are small character face portraits
- If you see NO portraits in a player's stock area = 0 stocks
- If portraits are greyed out or have an X = those stocks are lost
- One player MUST have 0 stocks when "GAME!" appears

RULES:
1. READ exact numbers shown - do NOT guess
2. Stock counts: 0, 1, 2, or 3 (0 is VALID and CRITICAL for game end)
3. game_active = false when you see "GAME!", "GO!", or "READY" text

Return ONLY a JSON array:
[
  {"timestamp": 0.0, "p1_percent": 0, "p2_percent": 0, "p1_stocks": 3, "p2_stocks": 3, "game_active": true},
  {"timestamp": 210.0, "p1_percent": null, "p2_percent": null, "p1_stocks": 0, "p2_stocks": 1, "game_active": false}
]

Here are the frames to analyze:
"""
    ]
    
    for timestamp, frame_bytes in frames:
        prompt_parts.append(f"\n--- Frame at {timestamp:.1f} seconds ---")
        prompt_parts.append({
            "mime_type": "image/jpeg",
            "data": base64.b64encode(frame_bytes).decode('utf-8')
        })
    
    prompt_parts.append("\n\nReturn ONLY the JSON array with extracted values:")
    
    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt_parts,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=2000,
                )
            )
            
            text = response.text.strip()
            
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            
            # Clean up
            states = []
            for item in data:
                states.append({
                    "timestamp": round(float(item.get("timestamp", 0)), 1),
                    "p1_percent": _parse_percent(item.get("p1_percent")),
                    "p2_percent": _parse_percent(item.get("p2_percent")),
                    "p1_stocks": _parse_stocks(item.get("p1_stocks")),
                    "p2_stocks": _parse_stocks(item.get("p2_stocks")),
                    "game_active": item.get("game_active", True),
                    "p1_character": None,
                    "p2_character": None,
                })
            
            return states
            
        except json.JSONDecodeError as e:
            print(f"[CloudExtractor v2] JSON error in batch {batch_idx}: {e}")
            return []
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error (429)
            if "429" in error_str or "Resource exhausted" in error_str:
                if attempt < max_retries - 1:
                    # Exponential backoff: 5s, 15s, 45s + random jitter
                    wait_time = (5 * (3 ** attempt)) + random.uniform(0, 5)
                    print(f"[CloudExtractor v2] Rate limited on batch {batch_idx}, waiting {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                    time_module.sleep(wait_time)
                    continue
            print(f"[CloudExtractor v2] Error in batch {batch_idx}: {e}")
            return []
    
    return []  # All retries failed


def _parse_percent(value) -> Optional[float]:
    """Parse percent value."""
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            p = float(value)
        else:
            p = float(str(value).replace('%', '').strip())
        return round(p, 1) if 0 <= p <= 999 else None
    except:
        return None


def _parse_stocks(value) -> Optional[int]:
    """Parse stock count."""
    if value is None:
        return None
    try:
        s = int(value)
        return s if 0 <= s <= 3 else None
    except:
        return None


def _validate_states(states: List[dict]) -> List[dict]:
    """Validate and fix extracted states."""
    if not states:
        return []
    
    # Find game start (skip pre-game frames like "READY" or "GO!")
    start_idx = 0
    for i, s in enumerate(states):
        # Game starts when we have actual percent data and game is active
        if s.get("game_active", True) and (s.get("p1_percent") is not None or s.get("p2_percent") is not None):
            start_idx = i
            break
    
    validated = []
    last_p1 = 0
    last_p2 = 0
    last_p1_stocks = 3
    last_p2_stocks = 3
    max_p1 = 0
    max_p2 = 0
    game_ended = False
    
    for state in states[start_idx:]:
        # Skip pre-game frames, but KEEP end-game frames (game_active=false after game started)
        if not state.get("game_active", True):
            if game_ended:
                # Already processed end-game, skip further frames
                continue
            elif last_p1_stocks > 0 or last_p2_stocks > 0:
                # This is an end-game frame (GAME! screen) - process it for stock counts
                game_ended = True
                # Fall through to process this frame
            else:
                continue
        
        p1 = state.get("p1_percent")
        p2 = state.get("p2_percent")
        p1_stocks = state.get("p1_stocks")
        p2_stocks = state.get("p2_stocks")
        
        # Track max percents
        if p1 is not None and p1 > max_p1:
            max_p1 = p1
        if p2 is not None and p2 > max_p2:
            max_p2 = p2
        
        # Validate P1 percent
        if p1 is not None:
            if p1 > 300:  # Impossible
                p1 = None
            elif last_p1 > 0 and p1 < last_p1 - 20 and p1 > 15:
                # Dropped but not to zero (OCR error)
                p1 = last_p1
            elif last_p1 > 0 and p1 > last_p1 + 80:
                # Huge jump (OCR error)
                p1 = None
        
        # Validate P2 percent
        if p2 is not None:
            if p2 > 300:
                p2 = None
            elif last_p2 > 0 and p2 < last_p2 - 20 and p2 > 15:
                p2 = last_p2
            elif last_p2 > 0 and p2 > last_p2 + 80:
                p2 = None
        
        # Validate stocks (don't allow increase, but DO allow decrease to 0)
        if p1_stocks is not None:
            if p1_stocks > last_p1_stocks:
                p1_stocks = last_p1_stocks  # Can't gain stocks
            # Allow decrease to any value (including 0) - stock can drop 2 at once in rare cases
        
        if p2_stocks is not None:
            if p2_stocks > last_p2_stocks:
                p2_stocks = last_p2_stocks  # Can't gain stocks
            # Allow decrease to any value (including 0)
        
        state["p1_percent"] = p1
        state["p2_percent"] = p2
        state["p1_stocks"] = p1_stocks
        state["p2_stocks"] = p2_stocks
        
        if p1 is not None:
            last_p1 = p1
        if p2 is not None:
            last_p2 = p2
        if p1_stocks is not None:
            last_p1_stocks = p1_stocks
        if p2_stocks is not None:
            last_p2_stocks = p2_stocks
        
        validated.append(state)
    
    return validated


def process_video(
    video_path: str,
    fps_sample: float = 2.0,  # 2 fps for better accuracy
    progress_callback: Callable[[float], None] = None,
    max_duration: int = None
) -> List[dict]:
    """Drop-in replacement."""
    return extract_frames_cloud_v2(
        video_path=video_path,
        fps_sample=fps_sample,
        progress_callback=progress_callback,
        max_duration=max_duration
    )

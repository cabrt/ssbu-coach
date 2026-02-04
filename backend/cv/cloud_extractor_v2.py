"""
Cloud-based frame extraction v2 - Improved accuracy.

Key improvements over v1:
1. Higher sample rate (1 fps for better tracking)
2. Crops percent regions for precise OCR
3. Better prompting to read EXACT numbers
4. Validation pass to catch OCR errors
5. Game start detection (skip pre-"GO!" frames)
"""
import cv2
import base64
import json
import os
import sys
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Tuple
import time
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# UI regions for percent extraction (based on tournament overlay 1080p)
# These are the specific areas where damage percentages appear
PERCENT_REGIONS = {
    "720p": {
        "p1": (280, 580, 180, 80),   # x, y, width, height - left player
        "p2": (820, 580, 180, 80),   # right player
    },
    "1080p": {
        "p1": (420, 870, 270, 120),
        "p2": (1230, 870, 270, 120),
    }
}


@dataclass
class FrameData:
    """Data for a single frame."""
    timestamp: float
    full_frame: bytes  # Full frame JPEG
    p1_crop: bytes     # Cropped P1 percent region
    p2_crop: bytes     # Cropped P2 percent region
    is_gameplay: bool  # Whether this looks like gameplay


@dataclass
class GameState:
    """Extracted game state."""
    timestamp: float
    p1_percent: Optional[float]
    p2_percent: Optional[float]
    p1_stocks: Optional[int]
    p2_stocks: Optional[int]
    game_active: bool  # False during "GO!", "GAME!", etc.


def extract_frames_cloud_v2(
    video_path: str,
    fps_sample: float = 1.0,  # Higher default for accuracy
    progress_callback: Callable[[float], None] = None,
    max_duration: int = None,
    batch_size: int = 10,
    max_parallel_batches: int = 2,
) -> List[dict]:
    """
    Extract game states with improved accuracy.
    
    Changes from v1:
    - 1 fps default (was 0.5)
    - Crops percent regions for precise reading
    - Two-pass: full frame for context, crops for numbers
    - Validation pass to fix OCR errors
    """
    if not GEMINI_AVAILABLE:
        raise ImportError("google-generativeai required")
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY required")
    
    genai.configure(api_key=api_key)
    
    print(f"[CloudExtractor v2] Processing {video_path}")
    print(f"[CloudExtractor v2] Sample rate: {fps_sample} fps")
    
    # Extract frames with cropped regions
    frames = _extract_frames_with_crops(video_path, fps_sample, max_duration)
    print(f"[CloudExtractor v2] Extracted {len(frames)} frames")
    
    if not frames:
        return []
    
    # Create batches
    batches = [frames[i:i+batch_size] for i in range(0, len(frames), batch_size)]
    print(f"[CloudExtractor v2] Processing {len(batches)} batches")
    
    # Process batches
    all_states = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_parallel_batches) as executor:
        futures = {
            executor.submit(_process_batch_v2, batch, idx): idx
            for idx, batch in enumerate(batches)
        }
        
        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                states = future.result()
                all_states.extend(states)
                
                if progress_callback:
                    progress_callback((batch_idx + 1) / len(batches) * 0.8)
                
                print(f"[CloudExtractor v2] Batch {batch_idx + 1}/{len(batches)}: {len(states)} states")
            except Exception as e:
                print(f"[CloudExtractor v2] Batch {batch_idx} failed: {e}")
    
    # Sort by timestamp
    all_states.sort(key=lambda s: s["timestamp"])
    
    # Validation pass - fix impossible values
    print("[CloudExtractor v2] Running validation pass...")
    validated_states = _validate_and_smooth(all_states)
    
    if progress_callback:
        progress_callback(1.0)
    
    elapsed = time.time() - start_time
    print(f"[CloudExtractor v2] Complete: {len(validated_states)} states in {elapsed:.1f}s")
    
    return validated_states


def _extract_frames_with_crops(
    video_path: str,
    fps_sample: float,
    max_duration: Optional[int]
) -> List[FrameData]:
    """Extract frames with cropped percent regions."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if max_duration:
        duration = min(duration, max_duration)
        total_frames = int(duration * video_fps)
    
    # Select region preset based on resolution
    regions = PERCENT_REGIONS["1080p"] if height > 800 else PERCENT_REGIONS["720p"]
    scale = height / (1080 if height > 800 else 720)
    
    frame_interval = int(video_fps / fps_sample) if fps_sample < video_fps else 1
    
    frames = []
    frame_num = 0
    
    while frame_num < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_num % frame_interval == 0:
            timestamp = frame_num / video_fps
            
            # Check if gameplay (not black screen)
            is_gameplay = _is_gameplay_frame(frame)
            
            if is_gameplay:
                # Resize full frame
                full_resized = _resize_and_encode(frame, max_width=1280)
                
                # Crop percent regions
                p1_crop = _crop_region(frame, regions["p1"], scale)
                p2_crop = _crop_region(frame, regions["p2"], scale)
                
                frames.append(FrameData(
                    timestamp=timestamp,
                    full_frame=full_resized,
                    p1_crop=p1_crop,
                    p2_crop=p2_crop,
                    is_gameplay=True
                ))
        
        frame_num += 1
    
    cap.release()
    return frames


def _is_gameplay_frame(frame) -> bool:
    """Check if frame is actual gameplay."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    
    # Skip very dark frames (loading)
    if mean_brightness < 25:
        return False
    
    # Check for color variance (menus are often solid colors)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    sat_std = np.std(hsv[:, :, 1])
    if sat_std < 20:
        return False
    
    return True


def _crop_region(frame, region: Tuple[int, int, int, int], scale: float) -> bytes:
    """Crop and encode a region of the frame."""
    x, y, w, h = [int(v * scale) for v in region]
    crop = frame[y:y+h, x:x+w]
    
    # Upscale crop for better OCR
    crop = cv2.resize(crop, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
    
    _, buffer = cv2.imencode('.jpg', crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return buffer.tobytes()


def _resize_and_encode(frame, max_width: int = 1280) -> bytes:
    """Resize frame and encode as JPEG."""
    h, w = frame.shape[:2]
    if w > max_width:
        scale = max_width / w
        frame = cv2.resize(frame, (max_width, int(h * scale)))
    
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return buffer.tobytes()


def _process_batch_v2(frames: List[FrameData], batch_idx: int) -> List[dict]:
    """Process a batch with improved prompting."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Build prompt with cropped percent regions
    prompt_parts = [
        """You are analyzing Super Smash Bros Ultimate gameplay frames.

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. READ THE EXACT NUMBERS shown on screen. Do NOT estimate or infer.
2. Damage percentages are shown as large colored numbers (usually red/orange/yellow)
3. The format is typically "XX%" or "XXX%" (e.g., "42%", "127%")
4. If a number has a decimal (e.g., "85.3%"), include it
5. Stock icons are small character portraits - COUNT them exactly (0, 1, 2, or 3)
6. If "GO!" or "GAME!" text is visible, set game_active to false
7. If you cannot clearly read a value, use null - DO NOT GUESS

For each frame, I'm showing:
- The full game screen
- A zoomed crop of Player 1's damage percent (left side)
- A zoomed crop of Player 2's damage percent (right side)

Return ONLY a JSON array with this exact format:
[
  {
    "timestamp": 0.0,
    "p1_percent": 42.5,
    "p2_percent": 0,
    "p1_stocks": 3,
    "p2_stocks": 3,
    "game_active": true
  }
]

IMPORTANT: Read the EXACT numbers from the zoomed crops. They show the damage percentages clearly.

Here are the frames:
"""
    ]
    
    # Add each frame with its crops
    for frame in frames:
        prompt_parts.append(f"\n\n=== FRAME at {frame.timestamp:.1f} seconds ===")
        prompt_parts.append("\nFull screen:")
        prompt_parts.append({
            "mime_type": "image/jpeg",
            "data": base64.b64encode(frame.full_frame).decode('utf-8')
        })
        prompt_parts.append("\nPlayer 1 (left) damage percent - READ THIS NUMBER:")
        prompt_parts.append({
            "mime_type": "image/jpeg",
            "data": base64.b64encode(frame.p1_crop).decode('utf-8')
        })
        prompt_parts.append("\nPlayer 2 (right) damage percent - READ THIS NUMBER:")
        prompt_parts.append({
            "mime_type": "image/jpeg",
            "data": base64.b64encode(frame.p2_crop).decode('utf-8')
        })
    
    prompt_parts.append("\n\nNow extract the EXACT values from each frame. Return ONLY valid JSON:")
    
    try:
        response = model.generate_content(
            prompt_parts,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,  # Zero temperature for deterministic output
                max_output_tokens=3000,
            )
        )
        
        response_text = response.text.strip()
        
        # Extract JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        states = json.loads(response_text)
        
        # Clean and validate
        cleaned = []
        for state in states:
            cleaned.append({
                "timestamp": round(float(state.get("timestamp", 0)), 1),
                "p1_percent": _parse_percent(state.get("p1_percent")),
                "p2_percent": _parse_percent(state.get("p2_percent")),
                "p1_stocks": _parse_stocks(state.get("p1_stocks")),
                "p2_stocks": _parse_stocks(state.get("p2_stocks")),
                "game_active": state.get("game_active", True),
                "p1_character": None,
                "p2_character": None,
            })
        
        return cleaned
        
    except Exception as e:
        print(f"[CloudExtractor v2] Batch {batch_idx} error: {e}")
        return []


def _parse_percent(value) -> Optional[float]:
    """Parse percent value."""
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            percent = float(value)
        else:
            cleaned = str(value).replace('%', '').strip()
            percent = float(cleaned)
        
        if 0 <= percent <= 999:
            return round(percent, 1)
        return None
    except:
        return None


def _parse_stocks(value) -> Optional[int]:
    """Parse stock count."""
    if value is None:
        return None
    try:
        stocks = int(value)
        return stocks if 0 <= stocks <= 3 else None
    except:
        return None


def _validate_and_smooth(states: List[dict]) -> List[dict]:
    """
    Validate and smooth extracted states.
    
    Rules:
    1. Percent can't decrease unless near zero (stock loss)
    2. Percent can't jump more than 60% in one frame (even big hits)
    3. Stocks can only decrease, by 1 at a time
    4. Filter out pre-game frames (game_active=False at start)
    """
    if not states:
        return []
    
    # Find game start (first frame where game_active and we have data)
    game_start_idx = 0
    for i, s in enumerate(states):
        if s.get("game_active", True) and s.get("p1_percent") is not None:
            game_start_idx = i
            break
    
    # Filter to game frames only
    states = states[game_start_idx:]
    
    if not states:
        return []
    
    validated = []
    
    last_p1 = 0
    last_p2 = 0
    last_p1_stocks = 3
    last_p2_stocks = 3
    max_p1 = 0
    max_p2 = 0
    
    for state in states:
        # Skip non-game frames
        if not state.get("game_active", True):
            continue
        
        p1 = state.get("p1_percent")
        p2 = state.get("p2_percent")
        p1_stocks = state.get("p1_stocks")
        p2_stocks = state.get("p2_stocks")
        
        # Validate P1 percent
        if p1 is not None:
            # Track max
            if p1 > max_p1:
                max_p1 = p1
            
            # Check for impossible values
            if p1 > 300:
                p1 = None
            elif last_p1 > 0:
                # Percent dropped significantly but not to near-zero = likely stock loss
                if p1 < last_p1 - 20 and p1 > 15:
                    # OCR error - use last value
                    p1 = last_p1
                # Huge jump = OCR error
                elif p1 > last_p1 + 80:
                    p1 = None
        
        # Validate P2 percent (same logic)
        if p2 is not None:
            if p2 > max_p2:
                max_p2 = p2
            
            if p2 > 300:
                p2 = None
            elif last_p2 > 0:
                if p2 < last_p2 - 20 and p2 > 15:
                    p2 = last_p2
                elif p2 > last_p2 + 80:
                    p2 = None
        
        # Validate stocks
        if p1_stocks is not None:
            # Stocks can only decrease
            if p1_stocks > last_p1_stocks:
                p1_stocks = last_p1_stocks
            # Can only lose 1 at a time
            elif p1_stocks < last_p1_stocks - 1:
                p1_stocks = last_p1_stocks - 1
        
        if p2_stocks is not None:
            if p2_stocks > last_p2_stocks:
                p2_stocks = last_p2_stocks
            elif p2_stocks < last_p2_stocks - 1:
                p2_stocks = last_p2_stocks - 1
        
        # Update state
        state["p1_percent"] = p1
        state["p2_percent"] = p2
        state["p1_stocks"] = p1_stocks
        state["p2_stocks"] = p2_stocks
        
        # Update tracking
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


# Drop-in replacement
def process_video(
    video_path: str,
    fps_sample: float = 1.0,
    progress_callback: Callable[[float], None] = None,
    max_duration: int = None
) -> List[dict]:
    """Drop-in replacement using improved cloud extraction."""
    return extract_frames_cloud_v2(
        video_path=video_path,
        fps_sample=fps_sample,
        progress_callback=progress_callback,
        max_duration=max_duration
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        states = extract_frames_cloud_v2(sys.argv[1])
        print(f"\nExtracted {len(states)} states")
        for s in states[:15]:
            print(f"  {s['timestamp']:.1f}s: P1={s['p1_percent']}% ({s['p1_stocks']}) | P2={s['p2_percent']}% ({s['p2_stocks']})")

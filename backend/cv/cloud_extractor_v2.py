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
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    fps_sample: float = 3.0,  # 3 fps for better accuracy on peak percentages
    progress_callback: Callable[[float], None] = None,
    max_duration: int = None,
    batch_size: int = 8,  # Frames per API call
    max_parallel_batches: int = 2,  # 2 parallel to avoid rate limits while staying fast
) -> List[dict]:
    """
    Extract game states using Gemini vision.
    
    Simplified approach:
    - Send full frames (no complex cropping)
    - Smaller batches for better accuracy
    - Clear prompting for exact number reading
    - High-resolution resampling around detected deaths for peak percentages
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
    
    # Create batches
    batches = [frames[i:i+batch_size] for i in range(0, len(frames), batch_size)]
    print(f"[CloudExtractor v2] Processing {len(batches)} batches (parallel workers={max_parallel_batches})")
    
    # Process batches in parallel (batching + cloud OCR)
    all_states = []
    
    with ThreadPoolExecutor(max_workers=max_parallel_batches) as executor:
        futures = {executor.submit(_process_batch, batch, idx): idx for idx, batch in enumerate(batches)}
        
        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                states = future.result()
                all_states.extend(states)
                
                if progress_callback:
                    progress_callback((batch_idx + 1) / len(batches) * 0.8)
                
                print(f"[CloudExtractor v2] Batch {batch_idx + 1}/{len(batches)}: {len(states)} states")
            except Exception as e:
                print(f"[CloudExtractor v2] Batch {batch_idx} error: {e}")
    
    # Sort by timestamp
    all_states.sort(key=lambda s: s["timestamp"])
    
    # Validation pass
    print("[CloudExtractor v2] Running validation pass...")
    validated = _validate_states(all_states)
    
    # HIGH-RESOLUTION RESAMPLE around detected deaths
    # The peak percentage before death only appears briefly (~0.1s)
    # Standard 3fps misses it, so we resample at 10fps around death moments
    print("[CloudExtractor v2] Resampling around deaths for peak percentages...")
    validated = _resample_death_moments(video_path, validated, fps_sample)
    
    if progress_callback:
        progress_callback(1.0)
    
    print(f"[CloudExtractor v2] Complete: {len(validated)} states")
    
    return validated


def _resample_death_moments(video_path: str, states: List[dict], base_fps: float) -> List[dict]:
    """
    Resample at higher fps around detected deaths to capture peak percentages.
    
    The peak percentage before death only appears for ~0.1-0.2 seconds during
    hit effects. At 3fps sampling, we often miss this. This function:
    1. Identifies death moments (percent drops from high to near 0)
    2. Extracts 10fps samples in the 1 second before each death
    3. Runs OCR on those frames to find the peak percentage
    4. Updates states with better peak values
    """
    if not states:
        return states
    
    # Find death moments - where percent drops from >50 to <15
    death_moments = []
    for i, state in enumerate(states):
        if i < 1:
            continue
        
        prev = states[i-1]
        for player in ["p1", "p2"]:
            pct_key = f"{player}_percent"
            prev_pct = prev.get(pct_key) or 0
            curr_pct = state.get(pct_key) or 0
            
            # Death = high percent to low percent
            if prev_pct > 50 and curr_pct < 15:
                death_moments.append({
                    "timestamp": state["timestamp"],
                    "player": player,
                    "pre_death_pct": prev_pct,
                    "state_idx": i
                })
    
    if not death_moments:
        return states
    
    print(f"[CloudExtractor v2] Found {len(death_moments)} death moments to resample")
    
    # Open video and extract high-res frames around each death
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return states
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    
    # For each death, extract frames at 15fps in the 1.5 seconds before
    # Higher fps = better chance of catching the brief peak frame
    HIGH_RES_FPS = 15
    LOOKBACK_SECS = 1.5
    
    for death in death_moments:
        death_ts = death["timestamp"]
        player = death["player"]
        
        # Calculate frame range
        start_ts = max(0, death_ts - LOOKBACK_SECS)
        end_ts = death_ts
        
        # Extract frames at 10fps in this window
        high_res_frames = []
        frame_interval = video_fps / HIGH_RES_FPS
        
        for t in np.arange(start_ts, end_ts, 1.0 / HIGH_RES_FPS):
            frame_num = int(t * video_fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if ret:
                # Resize and encode
                h, w = frame.shape[:2]
                if w > 1280:
                    scale = 1280 / w
                    frame = cv2.resize(frame, (1280, int(h * scale)))
                
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                high_res_frames.append((t, buffer.tobytes()))
        
        if len(high_res_frames) < 3:
            continue
        
        # Process these frames with OCR
        try:
            high_res_states = _process_batch(high_res_frames, -1)
            
            # Find max percent for this player
            pct_key = f"{player}_percent"
            max_pct = death["pre_death_pct"]
            
            for hrs in high_res_states:
                pct = hrs.get(pct_key)
                if pct is not None and pct > max_pct and pct < 300:
                    max_pct = pct
            
            # If we found a higher peak, update the state before death
            if max_pct > death["pre_death_pct"]:
                print(f"[CloudExtractor v2] Found higher {player} peak: {death['pre_death_pct']}% -> {max_pct}%")
                # Update the state right before death with the peak
                state_idx = death["state_idx"] - 1
                if 0 <= state_idx < len(states):
                    states[state_idx][pct_key] = max_pct
            else:
                # Apply damage estimation heuristic if we couldn't capture the peak
                # The final hit that causes the kill typically adds 10-20% damage
                # that only appears briefly before the percent resets
                estimated_pct = _estimate_kill_percent(death["pre_death_pct"])
                if estimated_pct > death["pre_death_pct"]:
                    print(f"[CloudExtractor v2] Estimated {player} peak: {death['pre_death_pct']}% -> ~{estimated_pct}% (estimated)")
                    state_idx = death["state_idx"] - 1
                    if 0 <= state_idx < len(states):
                        # Mark as estimated so coaching tips can note this
                        states[state_idx][pct_key] = estimated_pct
                        states[state_idx][f"{player}_percent_estimated"] = True
        except Exception as e:
            print(f"[CloudExtractor v2] High-res resample error: {e}")
            continue
    
    cap.release()
    return states


def _estimate_kill_percent(last_stable_pct: float) -> float:
    """
    Estimate the actual kill percentage when we couldn't capture the peak frame.
    
    In Smash, the final hit that causes a KO typically adds 10-20% damage,
    which only appears for ~0.1 seconds before the percent resets.
    
    This provides a more realistic estimate based on common kill scenarios:
    - Kill moves at 120-140% often do 12-18% damage
    - Kill moves at 140-160% may be weaker confirms doing 8-15%
    - Very high percent kills (160+) may just be pokes doing 5-10%
    """
    if last_stable_pct < 100:
        # Early kill - likely a strong kill move or combo
        return last_stable_pct + 15
    elif last_stable_pct < 130:
        # Standard kill range - typical kill move
        return last_stable_pct + 12
    elif last_stable_pct < 150:
        # Higher percent - could be weaker kill option
        return last_stable_pct + 10
    else:
        # Very high percent - likely just a poke
        return last_stable_pct + 8


def _extract_frames(video_path: str, fps_sample: float, max_duration: Optional[int]) -> List[tuple]:
    """Extract frames from video with high-FPS sampling for final seconds."""
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
    
    # Calculate when to switch to high-FPS mode for final seconds
    # Use 10 seconds to account for post-game screens that pad the video
    HIGH_FPS_FINAL_SECONDS = 10.0
    HIGH_FPS_RATE = 8  # 8 fps for final seconds (balance between coverage and API cost)
    high_fps_start_time = max(0, duration - HIGH_FPS_FINAL_SECONDS)
    high_fps_interval = int(video_fps / HIGH_FPS_RATE) if HIGH_FPS_RATE < video_fps else 1
    
    frames = []
    frame_num = 0
    
    while frame_num < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        current_time = frame_num / video_fps
        
        # Use high FPS for final 3 seconds, normal FPS otherwise
        if current_time >= high_fps_start_time:
            should_sample = (frame_num % high_fps_interval == 0)
        else:
            should_sample = (frame_num % frame_interval == 0)
        
        if should_sample:
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

DAMAGE PERCENTAGE READING - CRITICAL:
- Damage percentages are LARGE COLORED NUMBERS at the BOTTOM of the screen
- The numbers use a stylized font - read EACH DIGIT carefully
- Common values range from 0% to 200%+ (high percent = close to death)
- Player 1 (P1) percentage is on the LEFT side
- Player 2 (P2) percentage is on the RIGHT side
- The "%" symbol appears after the number

DIGIT READING TIPS (the font can be tricky):
- "1" looks like a thin vertical line, often with a small base
- "4" has a horizontal bar crossing a vertical line (like an upside-down 'h')
- "6" has a curved bottom loop (like a rotated 'g' shape) - DO NOT confuse with "4"
- "0" is a full oval/circle shape
- "3" has two curved bumps on the right
- "2" has a curved top and flat bottom with diagonal connector
- Watch for 3-digit numbers: 100%, 120%, 145%, 162%, etc.
- CRITICAL: If damage is high, expect 3 digits! Values like 140%, 145%, 160%, 162% are common before deaths
- When in doubt between "4" and "6", look for the curved loop at bottom (6) vs straight lines (4)

STOCK ICONS:
- Stock icons are small character face portraits below/near the damage percent
- P1 stocks are on the LEFT, P2 stocks are on the RIGHT
- Count carefully: 0, 1, 2, or 3 stock icons visible
- Empty/missing stock area = 0 stocks

GAME END DETECTION:
- "GAME!" text appears when the match ENDS
- On GAME! screens, the LOSER has 0 stocks, WINNER has 1-3 stocks
- game_active = false when you see "GAME!", "GO!", or "READY" text

RULES:
1. READ the exact digits shown - do NOT estimate or round
2. Double-check 3-digit percentages (100%+) - these are common before deaths
3. Stock counts: 0, 1, 2, or 3 only

Return ONLY a JSON array:
[
  {"timestamp": 0.0, "p1_percent": 0, "p2_percent": 0, "p1_stocks": 3, "p2_stocks": 3, "game_active": true},
  {"timestamp": 210.0, "p1_percent": 162, "p2_percent": 145, "p1_stocks": 1, "p2_stocks": 0, "game_active": false}
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
                    # Exponential backoff: 2s, 4s, 8s + small jitter (faster for paid tier)
                    wait_time = (2 * (2 ** attempt)) + random.uniform(0, 1)
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
    """
    Validate and fix extracted states.
    
    CRITICAL: OCR stock counts are UNRELIABLE. We use percent resets
    as the primary signal for stock losses:
    - Death = percent drops from >50% to <15%
    - We IGNORE OCR stock values and track stocks based on deaths
    """
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
    # Track stocks OURSELVES based on percent resets (ignore OCR)
    tracked_p1_stocks = 3
    tracked_p2_stocks = 3
    max_p1 = 0
    max_p2 = 0
    game_ended = False
    
    # Respawn cooldown: after death, ignore OCR errors for this many seconds
    RESPAWN_COOLDOWN = 10.0  # seconds (increased for safety)
    p1_death_time = None
    p2_death_time = None
    
    for state in states[start_idx:]:
        # Skip pre-game frames
        if not state.get("game_active", True):
            continue
        
        timestamp = state.get("timestamp", 0)
        p1 = state.get("p1_percent")
        p2 = state.get("p2_percent")
        raw_p1_stocks = state.get("p1_stocks")
        raw_p2_stocks = state.get("p2_stocks")
        
        if game_ended:
            continue
        
        # During respawn cooldown, be VERY careful about OCR readings
        # Only accept percent values that make sense (low during respawn)
        if p1_death_time is not None and timestamp - p1_death_time < RESPAWN_COOLDOWN:
            # P1 is respawning - reject high percent readings (OCR errors)
            if p1 is not None and p1 > 30:
                p1 = last_p1  # Keep last known value (should be low)
        
        if p2_death_time is not None and timestamp - p2_death_time < RESPAWN_COOLDOWN:
            # P2 is respawning - reject high percent readings (OCR errors)
            if p2 is not None and p2 > 30:
                p2 = last_p2  # Keep last known value (should be low)
        
        # Track max percents for each stock
        if p1 is not None and p1 > max_p1:
            max_p1 = p1
        if p2 is not None and p2 > max_p2:
            max_p2 = p2
        
        # STOCK TRACKING: Detect deaths from percent resets ONLY
        # Death = percent drops from high (>50%) to low (<15%)
        # CRITICAL: Only count ONE death per reset
        if p1 is not None and last_p1 > 50 and p1 < 15:
            # P1 died - decrement stock
            tracked_p1_stocks -= 1
            max_p1 = 0  # Reset max for next stock
            last_p1 = p1  # UPDATE IMMEDIATELY to prevent double-counting
            p1_death_time = timestamp  # Start respawn cooldown
            if tracked_p1_stocks <= 0:
                tracked_p1_stocks = 0
                # DON'T immediately end game - wait for "new game" signal
        
        if p2 is not None and last_p2 > 50 and p2 < 15:
            # P2 died - decrement stock
            tracked_p2_stocks -= 1
            max_p2 = 0  # Reset max for next stock
            last_p2 = p2  # UPDATE IMMEDIATELY to prevent double-counting
            p2_death_time = timestamp  # Start respawn cooldown
            if tracked_p2_stocks <= 0:
                tracked_p2_stocks = 0
        
        # End game when someone has 0 stocks (after a brief delay for GAME! screen)
        if tracked_p1_stocks == 0 or tracked_p2_stocks == 0:
            # Check if we're a few seconds past the final death
            final_death_time = p1_death_time if tracked_p1_stocks == 0 else p2_death_time
            if final_death_time and timestamp - final_death_time > 3.0:
                game_ended = True
        
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
        
        # IGNORE OCR stock values entirely - use our tracked stocks
        # (OCR is too unreliable for stock counts)
        
        state["p1_percent"] = p1
        state["p2_percent"] = p2
        state["p1_stocks"] = tracked_p1_stocks
        state["p2_stocks"] = tracked_p2_stocks
        
        if p1 is not None:
            last_p1 = p1
        if p2 is not None:
            last_p2 = p2
        
        validated.append(state)
    
    return validated


def process_video(
    video_path: str,
    fps_sample: float = 3.0,  # 3 fps for better accuracy
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

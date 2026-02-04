import cv2
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cv.state_detector import detect_game_state, is_gameplay_frame

def process_video(video_path: str, fps_sample: float = 0.5, progress_callback=None, max_duration: int = None):
    """
    Extract frames from video and detect game state for each.
    We sample at a low FPS since game state doesn't change that fast.
    
    Args:
        video_path: Path to video file
        fps_sample: Frames per second to sample (default 1.0 = 1 frame per second)
        progress_callback: Function to call with progress (0-1)
        max_duration: Maximum seconds of video to process (None = entire video)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps
    
    print(f"[VideoProcessor] Video: {duration:.1f}s, {total_frames} frames, {video_fps:.1f} fps")
    
    if max_duration:
        duration = min(duration, max_duration)
        total_frames = int(duration * video_fps)
        print(f"[VideoProcessor] Limiting to {max_duration}s")
    
    frame_interval = int(video_fps / fps_sample) if fps_sample < video_fps else 1
    print(f"[VideoProcessor] Sampling every {frame_interval} frames ({fps_sample} fps)")
    
    game_states = []
    frame_num = 0
    last_valid_p1 = 0
    last_valid_p2 = 0
    last_valid_p1_stocks = 3
    last_valid_p2_stocks = 3
    running_max_p1 = 0  # Track highest P1 percent seen
    running_max_p2 = 0  # Track highest P2 percent seen
    
    while frame_num < total_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        # only process every nth frame
        if frame_num % frame_interval == 0:
            timestamp = frame_num / video_fps
            
            # skip non-gameplay frames (menus, loading, etc.)
            if not is_gameplay_frame(frame):
                frame_num += 1
                continue
            
            state = detect_game_state(frame, timestamp)
            
            if state:
                # Track raw max before smoothing (so we don't miss peak values)
                raw_p1 = state.get("p1_percent")
                raw_p2 = state.get("p2_percent")
                if raw_p1 is not None and raw_p1 > running_max_p1 and raw_p1 <= 250:
                    running_max_p1 = raw_p1
                if raw_p2 is not None and raw_p2 > running_max_p2 and raw_p2 <= 250:
                    running_max_p2 = raw_p2
                
                # smooth out OCR/detection errors with sanity checks
                state = smooth_state(
                    state, last_valid_p1, last_valid_p2,
                    last_valid_p1_stocks, last_valid_p2_stocks,
                    running_max_p1, running_max_p2
                )
                
                if state["p1_percent"] is not None:
                    last_valid_p1 = state["p1_percent"]
                if state["p2_percent"] is not None:
                    last_valid_p2 = state["p2_percent"]
                if state["p1_stocks"] is not None:
                    last_valid_p1_stocks = state["p1_stocks"]
                if state["p2_stocks"] is not None:
                    last_valid_p2_stocks = state["p2_stocks"]
                
                game_states.append(state)
            
            if progress_callback:
                progress_callback(frame_num / total_frames)
        
        frame_num += 1
    
    cap.release()
    print(f"[VideoProcessor] Extracted {len(game_states)} game states from {frame_num} frames")
    return game_states

def smooth_state(state: dict, last_p1: int, last_p2: int, 
                  last_p1_stocks: int = None, last_p2_stocks: int = None,
                  running_max_p1: int = 0, running_max_p2: int = 0) -> dict:
    """
    Apply sanity checks to filter out obvious OCR/detection errors.
    
    Rules:
    - Percent can't go above 300 (even in extreme cases)
    - When we have gaps in readings, allow larger jumps to "catch up"
    - Percent can't go down unless it drops to near-zero (stock loss)
    - Stocks can only decrease by 1 at a time
    """
    p1 = state.get("p1_percent")
    p2 = state.get("p2_percent")
    p1_stocks = state.get("p1_stocks")
    p2_stocks = state.get("p2_stocks")
    
    # absolute cap: game percent is 0-999 but typically under 200
    MAX_PERCENT = 250  # allow higher percents in extreme cases
    # Allow larger jumps - combos can deal 60%+ in a second
    max_jump = 70
    
    if p1 is not None:
        if p1 > MAX_PERCENT:
            state["p1_percent"] = None
        elif last_p1 == 0 and p1 > 100:
            # first read: allow up to 100% (could have missed earlier readings)
            state["p1_percent"] = None
        elif last_p1 > 0:
            # Allow the value if it's higher than running max (new max is valid)
            if p1 > running_max_p1 and p1 <= MAX_PERCENT:
                pass  # This is a new max, keep it
            elif p1 > last_p1 + max_jump:
                state["p1_percent"] = None
            elif p1 < last_p1 - 15 and p1 > 10:
                # percent dropped but not to near-zero: OCR error
                state["p1_percent"] = None
    
    if p2 is not None:
        if p2 > MAX_PERCENT:
            state["p2_percent"] = None
        elif last_p2 == 0 and p2 > 100:
            state["p2_percent"] = None
        elif last_p2 > 0:
            # Allow the value if it's higher than running max (new max is valid)
            if p2 > running_max_p2 and p2 <= MAX_PERCENT:
                pass  # This is a new max, keep it
            elif p2 > last_p2 + max_jump:
                state["p2_percent"] = None
            elif p2 < last_p2 - 15 and p2 > 10:
                state["p2_percent"] = None
    
    # validate stock counts
    if p1_stocks is not None and last_p1_stocks is not None:
        # stocks can only decrease by 1 at a time (no jumping from 3 to 1)
        if p1_stocks < last_p1_stocks - 1:
            state["p1_stocks"] = last_p1_stocks
        # stocks can never increase during a match
        elif p1_stocks > last_p1_stocks:
            state["p1_stocks"] = last_p1_stocks
    
    if p2_stocks is not None and last_p2_stocks is not None:
        if p2_stocks < last_p2_stocks - 1:
            state["p2_stocks"] = last_p2_stocks
        elif p2_stocks > last_p2_stocks:
            state["p2_stocks"] = last_p2_stocks
    
    return state

def extract_frames(video_path: str, output_dir: str, fps_sample: int = 2):
    """Save frames to disk for debugging/training data collection."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(video_fps / fps_sample)
    
    frame_num = 0
    saved = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_num % frame_interval == 0:
            out_path = os.path.join(output_dir, f"frame_{saved:05d}.jpg")
            cv2.imwrite(out_path, frame)
            saved += 1
        
        frame_num += 1
    
    cap.release()
    return saved

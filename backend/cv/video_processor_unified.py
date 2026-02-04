"""
Unified video processor with cloud-first extraction and local fallback.

Strategy:
1. Try cloud extraction (Gemini 1.5 Flash) - fast, accurate, ~$0.20/video
2. If cloud fails, fall back to local parallel processing
3. If local parallel fails, fall back to sequential processing

This ensures the system always works, with graceful degradation.
"""
import os
import sys
from pathlib import Path
from typing import List, Callable, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))


def process_video(
    video_path: str,
    fps_sample: float = 0.5,
    progress_callback: Callable[[float], None] = None,
    max_duration: int = None,
    prefer_cloud: bool = True,
    force_local: bool = False,
) -> List[dict]:
    """
    Process video to extract game states.
    
    Uses a tiered approach:
    1. Cloud (Gemini) - if API key available and prefer_cloud=True
    2. Local parallel - if cloud fails or unavailable
    3. Local sequential - final fallback
    
    Args:
        video_path: Path to video file
        fps_sample: Frames per second to sample
        progress_callback: Function to call with progress (0-1)
        max_duration: Maximum seconds to process
        prefer_cloud: Try cloud extraction first (default True)
        force_local: Skip cloud entirely (default False)
    
    Returns:
        List of game states
    """
    # Check for cloud availability
    has_cloud_key = bool(
        os.getenv("GOOGLE_API_KEY") or 
        os.getenv("GEMINI_API_KEY")
    )
    
    # Try cloud extraction first (v2 with improved accuracy)
    if prefer_cloud and has_cloud_key and not force_local:
        try:
            print("[VideoProcessor] Attempting cloud extraction v2 (Gemini 1.5 Flash)...")
            from cv.cloud_extractor_v2 import extract_frames_cloud_v2
            
            # Use 1.0 fps for better accuracy (was 0.5)
            actual_fps = max(fps_sample, 1.0)
            
            states = extract_frames_cloud_v2(
                video_path=video_path,
                fps_sample=actual_fps,
                progress_callback=progress_callback,
                max_duration=max_duration
            )
            
            if states:
                print(f"[VideoProcessor] Cloud extraction v2 successful: {len(states)} states")
                return states  # v2 already applies validation
            else:
                print("[VideoProcessor] Cloud returned no states, falling back to local...")
                
        except ImportError as e:
            print(f"[VideoProcessor] Cloud unavailable (missing package): {e}")
        except Exception as e:
            print(f"[VideoProcessor] Cloud extraction failed: {e}")
            import traceback
            traceback.print_exc()
            print("[VideoProcessor] Falling back to local processing...")
    
    # Try local parallel processing
    try:
        print("[VideoProcessor] Using local parallel processing...")
        from cv.video_processor_parallel import process_video_parallel
        
        states = process_video_parallel(
            video_path=video_path,
            fps_sample=fps_sample,
            progress_callback=progress_callback,
            max_duration=max_duration
        )
        
        if states:
            print(f"[VideoProcessor] Local parallel successful: {len(states)} states")
            return states  # Already smoothed in parallel processor
            
    except Exception as e:
        print(f"[VideoProcessor] Local parallel failed: {e}")
        print("[VideoProcessor] Falling back to sequential processing...")
    
    # Final fallback: sequential processing
    print("[VideoProcessor] Using local sequential processing (slowest)...")
    from cv.video_processor import process_video as process_sequential
    
    states = process_sequential(
        video_path=video_path,
        fps_sample=fps_sample,
        progress_callback=progress_callback,
        max_duration=max_duration
    )
    
    return states


def _apply_smoothing(states: List[dict]) -> List[dict]:
    """Apply smoothing pass to cloud-extracted states."""
    from cv.video_processor import smooth_state
    
    if not states:
        return []
    
    smoothed = []
    last_valid_p1 = 0
    last_valid_p2 = 0
    last_valid_p1_stocks = 3
    last_valid_p2_stocks = 3
    running_max_p1 = 0
    running_max_p2 = 0
    
    for state in states:
        # Track raw max before smoothing
        raw_p1 = state.get("p1_percent")
        raw_p2 = state.get("p2_percent")
        if raw_p1 is not None and raw_p1 > running_max_p1 and raw_p1 <= 250:
            running_max_p1 = raw_p1
        if raw_p2 is not None and raw_p2 > running_max_p2 and raw_p2 <= 250:
            running_max_p2 = raw_p2
        
        # Apply smoothing
        state = smooth_state(
            state, last_valid_p1, last_valid_p2,
            last_valid_p1_stocks, last_valid_p2_stocks,
            running_max_p1, running_max_p2
        )
        
        # Update tracking values
        if state["p1_percent"] is not None:
            last_valid_p1 = state["p1_percent"]
        if state["p2_percent"] is not None:
            last_valid_p2 = state["p2_percent"]
        if state["p1_stocks"] is not None:
            last_valid_p1_stocks = state["p1_stocks"]
        if state["p2_stocks"] is not None:
            last_valid_p2_stocks = state["p2_stocks"]
        
        smoothed.append(state)
    
    return smoothed


# Configuration helpers
def get_processing_mode() -> str:
    """Get the current processing mode that will be used."""
    has_cloud = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
    
    if has_cloud:
        return "cloud"
    else:
        return "local"


def estimate_processing_time(video_duration_seconds: float) -> dict:
    """Estimate processing time for different modes."""
    frames = video_duration_seconds * 0.5  # At 0.5 fps
    
    return {
        "cloud": {
            "time_seconds": 20 + (frames / 15) * 3,  # ~3s per batch of 15
            "cost_usd": frames * 0.002,
        },
        "local_parallel": {
            "time_seconds": frames * 2,  # ~2s per frame with 4 workers
            "cost_usd": 0,
        },
        "local_sequential": {
            "time_seconds": frames * 4,  # ~4s per frame
            "cost_usd": 0,
        }
    }

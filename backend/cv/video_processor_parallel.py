"""
Parallel video processor using chunked processing with overlap.
Significantly faster than sequential processing while maintaining accuracy.
"""
import cv2
import os
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Callable, Optional
import threading

sys.path.insert(0, str(Path(__file__).parent.parent))

from cv.state_detector import detect_game_state, is_gameplay_frame
from cv.video_processor import smooth_state  # reuse existing smoothing logic


@dataclass
class ChunkResult:
    """Result from processing a single chunk."""
    chunk_idx: int
    start_time: float
    end_time: float
    states: List[dict]  # Raw states before smoothing
    

@dataclass 
class ChunkSpec:
    """Specification for a chunk to process."""
    chunk_idx: int
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    is_first: bool
    is_last: bool


def process_video_parallel(
    video_path: str,
    fps_sample: float = 0.5,
    progress_callback: Callable[[float], None] = None,
    max_duration: int = None,
    num_workers: int = None,
    chunk_duration: float = 45.0,  # seconds per chunk
    overlap_duration: float = 5.0,  # seconds of overlap between chunks
) -> List[dict]:
    """
    Extract frames from video using parallel chunk processing.
    
    Args:
        video_path: Path to video file
        fps_sample: Frames per second to sample
        progress_callback: Function to call with progress (0-1)
        max_duration: Maximum seconds of video to process
        num_workers: Number of parallel workers (default: CPU count)
        chunk_duration: Duration of each chunk in seconds
        overlap_duration: Overlap between chunks in seconds
    
    Returns:
        List of game states, smoothed and in chronological order
    """
    # Get video properties
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / video_fps
    cap.release()
    
    print(f"[ParallelProcessor] Video: {duration:.1f}s, {total_frames} frames, {video_fps:.1f} fps")
    
    if max_duration:
        duration = min(duration, max_duration)
        total_frames = int(duration * video_fps)
        print(f"[ParallelProcessor] Limiting to {max_duration}s")
    
    # Calculate frame interval for sampling
    frame_interval = int(video_fps / fps_sample) if fps_sample < video_fps else 1
    print(f"[ParallelProcessor] Sampling every {frame_interval} frames ({fps_sample} fps)")
    
    # Determine number of workers
    if num_workers is None:
        import multiprocessing
        num_workers = min(multiprocessing.cpu_count(), 8)
    
    # Create chunk specifications
    chunks = _create_chunks(
        total_frames=total_frames,
        video_fps=video_fps,
        chunk_duration=chunk_duration,
        overlap_duration=overlap_duration
    )
    
    print(f"[ParallelProcessor] Processing {len(chunks)} chunks with {num_workers} workers")
    
    # Progress tracking
    progress_lock = threading.Lock()
    chunks_completed = [0]
    total_chunks = len(chunks)
    
    def update_progress():
        with progress_lock:
            chunks_completed[0] += 1
            if progress_callback:
                # Reserve last 10% for smoothing pass
                progress_callback(0.9 * chunks_completed[0] / total_chunks)
    
    # Process chunks in parallel
    chunk_results: List[ChunkResult] = [None] * len(chunks)
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(
                _process_chunk,
                video_path,
                chunk,
                frame_interval,
                video_fps
            ): chunk.chunk_idx
            for chunk in chunks
        }
        
        for future in as_completed(futures):
            chunk_idx = futures[future]
            try:
                result = future.result()
                chunk_results[chunk_idx] = result
                update_progress()
                print(f"[ParallelProcessor] Chunk {chunk_idx + 1}/{len(chunks)} done: {len(result.states)} states")
            except Exception as e:
                print(f"[ParallelProcessor] Chunk {chunk_idx} failed: {e}")
                # Store empty result to maintain order
                chunk_results[chunk_idx] = ChunkResult(
                    chunk_idx=chunk_idx,
                    start_time=chunks[chunk_idx].start_time,
                    end_time=chunks[chunk_idx].end_time,
                    states=[]
                )
    
    # Merge chunks, handling overlaps
    print("[ParallelProcessor] Merging chunks...")
    merged_states = _merge_chunks(chunk_results, chunks, overlap_duration)
    print(f"[ParallelProcessor] Merged into {len(merged_states)} states")
    
    # Apply sequential smoothing pass
    print("[ParallelProcessor] Applying smoothing pass...")
    smoothed_states = _apply_smoothing(merged_states)
    print(f"[ParallelProcessor] Final: {len(smoothed_states)} game states")
    
    if progress_callback:
        progress_callback(1.0)
    
    return smoothed_states


def _create_chunks(
    total_frames: int,
    video_fps: float,
    chunk_duration: float,
    overlap_duration: float
) -> List[ChunkSpec]:
    """Create chunk specifications with overlap."""
    chunks = []
    duration = total_frames / video_fps
    
    # Effective chunk step (chunk duration minus overlap)
    step_duration = chunk_duration - overlap_duration
    
    start_time = 0.0
    chunk_idx = 0
    
    while start_time < duration:
        end_time = min(start_time + chunk_duration, duration)
        
        chunks.append(ChunkSpec(
            chunk_idx=chunk_idx,
            start_frame=int(start_time * video_fps),
            end_frame=int(end_time * video_fps),
            start_time=start_time,
            end_time=end_time,
            is_first=(chunk_idx == 0),
            is_last=(end_time >= duration)
        ))
        
        start_time += step_duration
        chunk_idx += 1
        
        # Safety check to prevent infinite loop
        if chunk_idx > 1000:
            break
    
    return chunks


def _process_chunk(
    video_path: str,
    chunk: ChunkSpec,
    frame_interval: int,
    video_fps: float
) -> ChunkResult:
    """Process a single chunk of the video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    # Seek to start of chunk
    cap.set(cv2.CAP_PROP_POS_FRAMES, chunk.start_frame)
    
    states = []
    frame_num = chunk.start_frame
    
    while frame_num < chunk.end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Only process every nth frame
        if (frame_num - chunk.start_frame) % frame_interval == 0:
            timestamp = frame_num / video_fps
            
            # Skip non-gameplay frames
            if not is_gameplay_frame(frame):
                frame_num += 1
                continue
            
            state = detect_game_state(frame, timestamp)
            if state:
                # Mark which chunk this came from (for merge logic)
                state["_chunk_idx"] = chunk.chunk_idx
                state["_in_overlap"] = (
                    (not chunk.is_first and timestamp < chunk.start_time + 5.0) or
                    (not chunk.is_last and timestamp > chunk.end_time - 5.0)
                )
                states.append(state)
        
        frame_num += 1
    
    cap.release()
    
    return ChunkResult(
        chunk_idx=chunk.chunk_idx,
        start_time=chunk.start_time,
        end_time=chunk.end_time,
        states=states
    )


def _merge_chunks(
    results: List[ChunkResult],
    chunks: List[ChunkSpec],
    overlap_duration: float
) -> List[dict]:
    """
    Merge chunk results, intelligently handling overlaps.
    
    Strategy for overlaps:
    - For frames in overlap regions, we have data from two chunks
    - Prefer the frame from the chunk where it's NOT at the boundary
    - This gives us better context (the OCR had more surrounding frames)
    - If both have data, prefer the one with higher confidence (more non-null values)
    """
    # Collect all states with their timestamps
    all_states = []
    for result in results:
        if result and result.states:
            all_states.extend(result.states)
    
    # Sort by timestamp
    all_states.sort(key=lambda s: s["timestamp"])
    
    # Deduplicate overlapping timestamps
    # For each timestamp, pick the best state
    merged = []
    i = 0
    
    while i < len(all_states):
        current = all_states[i]
        timestamp = current["timestamp"]
        
        # Collect all states at this timestamp (from different chunks)
        same_time_states = [current]
        j = i + 1
        while j < len(all_states) and abs(all_states[j]["timestamp"] - timestamp) < 0.1:
            same_time_states.append(all_states[j])
            j += 1
        
        # Pick the best state
        if len(same_time_states) == 1:
            best = same_time_states[0]
        else:
            # Score each state by data quality
            def score_state(s):
                score = 0
                if s.get("p1_percent") is not None:
                    score += 2
                if s.get("p2_percent") is not None:
                    score += 2
                if s.get("p1_stocks") is not None:
                    score += 1
                if s.get("p2_stocks") is not None:
                    score += 1
                # Prefer non-overlap regions
                if not s.get("_in_overlap", False):
                    score += 3
                return score
            
            best = max(same_time_states, key=score_state)
        
        # Clean up internal markers
        best_clean = {k: v for k, v in best.items() if not k.startswith("_")}
        merged.append(best_clean)
        
        i = j
    
    return merged


def _apply_smoothing(states: List[dict]) -> List[dict]:
    """Apply sequential smoothing pass to merged states."""
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


# Convenience function to replace the original
def process_video(video_path: str, fps_sample: float = 0.5, progress_callback=None, max_duration: int = None):
    """
    Drop-in replacement for the original process_video function.
    Uses parallel processing for faster extraction.
    """
    return process_video_parallel(
        video_path=video_path,
        fps_sample=fps_sample,
        progress_callback=progress_callback,
        max_duration=max_duration
    )


if __name__ == "__main__":
    # Test with a sample video
    import sys
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        
        def progress(p):
            print(f"Progress: {p*100:.1f}%")
        
        states = process_video_parallel(video_path, progress_callback=progress)
        print(f"\nExtracted {len(states)} game states")
        
        # Print first few states
        for s in states[:5]:
            print(f"  {s['timestamp']}s: P1={s['p1_percent']}% P2={s['p2_percent']}%")

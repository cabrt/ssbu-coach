#!/usr/bin/env python3
"""
Benchmark script to compare sequential vs parallel video processing.
Run with: python benchmark_processing.py <video_path>
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def benchmark_sequential(video_path: str, max_duration: int = 30):
    """Benchmark original sequential processing."""
    from cv.video_processor import process_video
    
    print(f"\n{'='*60}")
    print("SEQUENTIAL PROCESSING")
    print(f"{'='*60}")
    
    start = time.time()
    states = process_video(video_path, fps_sample=0.5, max_duration=max_duration)
    elapsed = time.time() - start
    
    print(f"Time: {elapsed:.1f}s")
    print(f"States extracted: {len(states)}")
    print(f"Speed: {elapsed/len(states):.2f}s per frame" if states else "N/A")
    
    return elapsed, len(states)


def benchmark_parallel(video_path: str, max_duration: int = 30, num_workers: int = None):
    """Benchmark parallel processing."""
    from cv.video_processor_parallel import process_video_parallel
    import multiprocessing
    
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()
    
    print(f"\n{'='*60}")
    print(f"PARALLEL PROCESSING ({num_workers} workers)")
    print(f"{'='*60}")
    
    start = time.time()
    states = process_video_parallel(
        video_path, 
        fps_sample=0.5, 
        max_duration=max_duration,
        num_workers=num_workers
    )
    elapsed = time.time() - start
    
    print(f"Time: {elapsed:.1f}s")
    print(f"States extracted: {len(states)}")
    print(f"Speed: {elapsed/len(states):.2f}s per frame" if states else "N/A")
    
    return elapsed, len(states)


def main():
    if len(sys.argv) < 2:
        print("Usage: python benchmark_processing.py <video_path> [max_duration_seconds]")
        print("\nExample: python benchmark_processing.py ../data/videos/test.mp4 30")
        sys.exit(1)
    
    video_path = sys.argv[1]
    max_duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    print(f"Video: {video_path}")
    print(f"Processing first {max_duration} seconds")
    
    # Run benchmarks
    seq_time, seq_states = benchmark_sequential(video_path, max_duration)
    par_time, par_states = benchmark_parallel(video_path, max_duration)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Sequential: {seq_time:.1f}s ({seq_states} states)")
    print(f"Parallel:   {par_time:.1f}s ({par_states} states)")
    
    if seq_time > 0 and par_time > 0:
        speedup = seq_time / par_time
        print(f"\nSpeedup: {speedup:.2f}x faster")
        print(f"Time saved: {seq_time - par_time:.1f}s ({(1 - par_time/seq_time)*100:.0f}%)")


if __name__ == "__main__":
    main()

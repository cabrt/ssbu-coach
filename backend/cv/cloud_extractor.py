"""
Cloud-based frame extraction using Gemini 1.5 Flash.
Processes frames in batches for maximum speed and efficiency.

Expected performance:
- 90 frames in ~5 batches of 18 frames each
- ~20-30 seconds total vs 4-6 minutes with local OCR
- Cost: ~$0.15-0.25 per video
"""
import cv2
import base64
import json
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import google.generativeai
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[CloudExtractor] google-generativeai not installed. Run: pip install google-generativeai")


@dataclass
class FrameBatch:
    """A batch of frames to process together."""
    batch_idx: int
    frames: List[tuple]  # List of (timestamp, frame_data) tuples
    start_time: float
    end_time: float


@dataclass
class ExtractionResult:
    """Result from extracting game state from frames."""
    states: List[dict]
    processing_time: float
    tokens_used: int
    cost_estimate: float


def extract_frames_cloud(
    video_path: str,
    fps_sample: float = 0.5,
    progress_callback: Callable[[float], None] = None,
    max_duration: int = None,
    batch_size: int = 15,  # Frames per API call (Gemini handles up to 16 images well)
    max_parallel_batches: int = 3,  # Concurrent API calls
) -> List[dict]:
    """
    Extract game states from video using Gemini 1.5 Flash.
    
    Args:
        video_path: Path to video file
        fps_sample: Frames per second to sample (default 0.5 = 1 frame every 2 seconds)
        progress_callback: Function to call with progress (0-1)
        max_duration: Maximum seconds of video to process
        batch_size: Number of frames per API call
        max_parallel_batches: Maximum concurrent API calls
    
    Returns:
        List of game states with timestamps, percents, stocks
    """
    if not GEMINI_AVAILABLE:
        raise ImportError("google-generativeai package required. Run: pip install google-generativeai")
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable required")
    
    genai.configure(api_key=api_key)
    
    # Extract frames from video
    print(f"[CloudExtractor] Extracting frames from {video_path}")
    frames = _extract_video_frames(video_path, fps_sample, max_duration)
    print(f"[CloudExtractor] Extracted {len(frames)} frames")
    
    if not frames:
        return []
    
    # Create batches
    batches = _create_batches(frames, batch_size)
    print(f"[CloudExtractor] Created {len(batches)} batches of ~{batch_size} frames each")
    
    # Process batches in parallel
    all_states = []
    total_tokens = 0
    start_time = time.time()
    
    completed_batches = 0
    total_batches = len(batches)
    
    with ThreadPoolExecutor(max_workers=max_parallel_batches) as executor:
        futures = {
            executor.submit(_process_batch_gemini, batch): batch.batch_idx
            for batch in batches
        }
        
        for future in as_completed(futures):
            batch_idx = futures[future]
            try:
                result = future.result()
                all_states.extend(result.states)
                total_tokens += result.tokens_used
                
                completed_batches += 1
                if progress_callback:
                    progress_callback(completed_batches / total_batches)
                
                print(f"[CloudExtractor] Batch {batch_idx + 1}/{total_batches}: {len(result.states)} states, {result.processing_time:.1f}s")
                
            except Exception as e:
                print(f"[CloudExtractor] Batch {batch_idx} failed: {e}")
                completed_batches += 1
    
    # Sort by timestamp
    all_states.sort(key=lambda s: s["timestamp"])
    
    elapsed = time.time() - start_time
    cost = _estimate_cost(total_tokens)
    
    print(f"[CloudExtractor] Complete: {len(all_states)} states in {elapsed:.1f}s")
    print(f"[CloudExtractor] Tokens: {total_tokens}, Estimated cost: ${cost:.3f}")
    
    return all_states


def _extract_video_frames(
    video_path: str,
    fps_sample: float,
    max_duration: Optional[int]
) -> List[tuple]:
    """Extract frames from video at specified sample rate."""
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
            
            # Quick check for non-gameplay frames (mostly black)
            if _is_likely_gameplay(frame):
                # Resize for API efficiency (720p max)
                frame_resized = _resize_frame(frame, max_width=1280)
                frames.append((timestamp, frame_resized))
        
        frame_num += 1
    
    cap.release()
    return frames


def _is_likely_gameplay(frame) -> bool:
    """Quick check if frame looks like gameplay (not loading/menu)."""
    import numpy as np
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    return mean_brightness > 20  # Skip very dark frames


def _resize_frame(frame, max_width: int = 1280) -> bytes:
    """Resize frame and encode as JPEG bytes."""
    h, w = frame.shape[:2]
    if w > max_width:
        scale = max_width / w
        frame = cv2.resize(frame, (max_width, int(h * scale)))
    
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return buffer.tobytes()


def _create_batches(frames: List[tuple], batch_size: int) -> List[FrameBatch]:
    """Create batches of frames for parallel processing."""
    batches = []
    
    for i in range(0, len(frames), batch_size):
        batch_frames = frames[i:i + batch_size]
        batches.append(FrameBatch(
            batch_idx=len(batches),
            frames=batch_frames,
            start_time=batch_frames[0][0],
            end_time=batch_frames[-1][0]
        ))
    
    return batches


def _process_batch_gemini(batch: FrameBatch) -> ExtractionResult:
    """Process a batch of frames using Gemini 1.5 Flash."""
    start_time = time.time()
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Build the prompt with all frame images
    prompt_parts = [
        """Analyze these Super Smash Bros Ultimate gameplay frames and extract the game state from each.

For EACH frame, extract:
1. Player 1 (P1/left side) damage percent (the number shown, e.g., "42" or "127.5")
2. Player 2 (P2/right side) damage percent
3. Player 1 stock count (number of character icons remaining, usually 1-3)
4. Player 2 stock count

The damage percentages are typically shown in large colored numbers (red/orange) near the bottom of the screen.
Stock icons are small character portraits, usually below or near the damage percent.

IMPORTANT: 
- Return ONLY valid JSON, no other text
- If you can't read a value clearly, use null
- Timestamps are provided for each frame

Return a JSON array with one object per frame:
```json
[
  {"timestamp": 0.0, "p1_percent": 42, "p2_percent": 18, "p1_stocks": 3, "p2_stocks": 3},
  {"timestamp": 2.0, "p1_percent": 58, "p2_percent": 18, "p1_stocks": 3, "p2_stocks": 3},
  ...
]
```

Here are the frames with their timestamps:
"""
    ]
    
    # Add each frame with its timestamp
    for timestamp, frame_bytes in batch.frames:
        prompt_parts.append(f"\n--- Frame at {timestamp:.1f}s ---")
        prompt_parts.append({
            "mime_type": "image/jpeg",
            "data": base64.b64encode(frame_bytes).decode('utf-8')
        })
    
    prompt_parts.append("\n\nNow extract the game state from each frame. Return ONLY the JSON array:")
    
    # Call Gemini API
    try:
        response = model.generate_content(
            prompt_parts,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low temperature for consistent extraction
                max_output_tokens=2000,
            )
        )
        
        # Parse response
        response_text = response.text.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        states = json.loads(response_text)
        
        # Validate and clean states
        cleaned_states = []
        for state in states:
            cleaned = {
                "timestamp": round(float(state.get("timestamp", 0)), 2),
                "p1_percent": _parse_percent(state.get("p1_percent")),
                "p2_percent": _parse_percent(state.get("p2_percent")),
                "p1_stocks": _parse_stocks(state.get("p1_stocks")),
                "p2_stocks": _parse_stocks(state.get("p2_stocks")),
                "p1_character": None,  # Could be extracted but not critical
                "p2_character": None,
            }
            cleaned_states.append(cleaned)
        
        # Estimate tokens (rough: ~250 tokens per image + response)
        tokens_used = len(batch.frames) * 260 + len(response_text) // 4
        
        return ExtractionResult(
            states=cleaned_states,
            processing_time=time.time() - start_time,
            tokens_used=tokens_used,
            cost_estimate=_estimate_cost(tokens_used)
        )
        
    except json.JSONDecodeError as e:
        print(f"[CloudExtractor] JSON parse error: {e}")
        print(f"[CloudExtractor] Response was: {response_text[:500]}...")
        return ExtractionResult(
            states=[],
            processing_time=time.time() - start_time,
            tokens_used=0,
            cost_estimate=0
        )
    except Exception as e:
        print(f"[CloudExtractor] API error: {e}")
        raise


def _parse_percent(value) -> Optional[float]:
    """Parse percent value, handling various formats."""
    if value is None:
        return None
    
    try:
        if isinstance(value, (int, float)):
            percent = float(value)
        else:
            # Handle string formats like "42%", "42.5", etc.
            cleaned = str(value).replace('%', '').strip()
            percent = float(cleaned)
        
        # Sanity check
        if 0 <= percent <= 300:
            return percent
        return None
    except (ValueError, TypeError):
        return None


def _parse_stocks(value) -> Optional[int]:
    """Parse stock count value."""
    if value is None:
        return None
    
    try:
        stocks = int(value)
        if 0 <= stocks <= 3:
            return stocks
        return None
    except (ValueError, TypeError):
        return None


def _estimate_cost(tokens: int) -> float:
    """Estimate API cost based on token usage.
    
    Gemini 1.5 Flash pricing (as of 2024):
    - Input: $0.075 per 1M tokens
    - Output: $0.30 per 1M tokens
    - Images: ~258 tokens per image
    
    Rough estimate: $0.0001 per image + response
    """
    # Very rough estimate
    return tokens * 0.0001 / 1000


# Convenience function for drop-in replacement
def process_video(
    video_path: str,
    fps_sample: float = 0.5,
    progress_callback: Callable[[float], None] = None,
    max_duration: int = None
) -> List[dict]:
    """
    Drop-in replacement for local video processor.
    Uses Gemini 1.5 Flash for cloud-based extraction.
    """
    return extract_frames_cloud(
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
        
        states = extract_frames_cloud(video_path, progress_callback=progress)
        print(f"\nExtracted {len(states)} game states")
        
        for s in states[:10]:
            print(f"  {s['timestamp']}s: P1={s['p1_percent']}% ({s['p1_stocks']} stocks) | P2={s['p2_percent']}% ({s['p2_stocks']} stocks)")

#!/usr/bin/env python3
"""
One-time migration script to add game_states to existing saved analyses.
This allows instant loading instead of re-processing the video every time.
"""
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from cv.video_processor import process_video

SAVED_ANALYSES_DIR = Path(__file__).parent.parent / "data" / "saved_analyses"

def migrate_analysis(json_path: Path):
    """Add game_states to a saved analysis if missing."""
    print(f"\n[Migrating] {json_path.name}")
    
    with open(json_path) as f:
        data = json.load(f)
    
    # Check if already has game_states
    if data.get("game_states"):
        print(f"  Already has {len(data['game_states'])} game_states, skipping")
        return
    
    video_path = data.get("video_path")
    if not video_path or not os.path.exists(video_path):
        print(f"  Video not found: {video_path}, skipping")
        return
    
    print(f"  Processing video: {video_path}")
    game_states = process_video(video_path)
    print(f"  Extracted {len(game_states)} game states")
    
    data["game_states"] = game_states
    
    with open(json_path, "w") as f:
        json.dump(data, f)
    
    print(f"  Saved!")

def main():
    print("=== Migrating saved analyses to include game_states ===")
    
    json_files = list(SAVED_ANALYSES_DIR.glob("*.json"))
    print(f"Found {len(json_files)} saved analyses")
    
    for json_path in json_files:
        try:
            migrate_analysis(json_path)
        except Exception as e:
            print(f"  ERROR: {e}")
    
    print("\n=== Migration complete ===")

if __name__ == "__main__":
    main()

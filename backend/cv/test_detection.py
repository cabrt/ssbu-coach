#!/usr/bin/env python3
"""
Test script to visualize and debug game state detection on sample frames.
Usage: python test_detection.py <image_path>
"""

import cv2
import sys
import numpy as np
from pathlib import Path

# add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cv.state_detector import (
    detect_game_state, detect_layout, get_scaled_region, crop_region,
    count_stock_icons
)
from cv.ocr import read_percent


def visualize_detection(image_path: str, output_path: str = None):
    """
    Run detection on an image and visualize the results.
    Draws bounding boxes around detected regions.
    """
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Could not load image {image_path}")
        return
    
    h, w = frame.shape[:2]
    print(f"Image size: {w}x{h}")
    
    # detect layout
    regions, base_w, base_h = detect_layout(frame)
    scale_x, scale_y = w / base_w, h / base_h
    print(f"Detected layout: {base_w}x{base_h}, scale: {scale_x:.2f}x{scale_y:.2f}")
    print(f"Using regions: {list(regions.keys())}")
    
    # create visualization
    vis = frame.copy()
    
    # draw percent regions
    colors = {
        "p1_percent": (0, 255, 0),    # green
        "p2_percent": (0, 255, 0),
        "p1_stocks": (255, 0, 0),     # blue
        "p2_stocks": (255, 0, 0),
        "timer": (0, 255, 255),       # yellow
    }
    
    for region_name in ["p1_percent", "p2_percent", "p1_stocks", "p2_stocks", "timer"]:
        if region_name in regions:
            region = get_scaled_region(regions[region_name], scale_x, scale_y)
            x, y, rw, rh = region
            color = colors.get(region_name, (255, 255, 255))
            cv2.rectangle(vis, (x, y), (x + rw, y + rh), color, 2)
            cv2.putText(vis, region_name, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # run detection
    state = detect_game_state(frame, 0.0)
    
    print("\n=== Detection Results ===")
    if state:
        print(f"P1 Percent: {state['p1_percent']}")
        print(f"P2 Percent: {state['p2_percent']}")
        print(f"P1 Stocks: {state['p1_stocks']}")
        print(f"P2 Stocks: {state['p2_stocks']}")
        print(f"P1 Character: {state['p1_character']}")
        print(f"P2 Character: {state['p2_character']}")
        
        # add text overlay to visualization
        y_offset = 30
        cv2.putText(vis, f"P1: {state['p1_percent']}% | {state['p1_stocks']} stocks", 
                    (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(vis, f"P2: {state['p2_percent']}% | {state['p2_stocks']} stocks", 
                    (10, y_offset + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        print("No valid game state detected")
    
    # save cropped regions for inspection
    print("\n=== Saving region crops ===")
    output_dir = Path(image_path).parent / "debug_crops"
    output_dir.mkdir(exist_ok=True)
    
    for region_name in ["p1_percent", "p2_percent", "p1_stocks", "p2_stocks"]:
        if region_name in regions:
            region = get_scaled_region(regions[region_name], scale_x, scale_y)
            crop = crop_region(frame, region)
            crop_path = output_dir / f"{region_name}.jpg"
            cv2.imwrite(str(crop_path), crop)
            print(f"Saved {crop_path}")
    
    # save visualization
    if output_path is None:
        output_path = str(Path(image_path).parent / "debug_visualization.jpg")
    cv2.imwrite(output_path, vis)
    print(f"\nSaved visualization to {output_path}")
    
    return state


def test_stock_detection(image_path: str):
    """
    Detailed test of stock icon detection.
    """
    frame = cv2.imread(image_path)
    if frame is None:
        return
    
    h, w = frame.shape[:2]
    regions, base_w, base_h = detect_layout(frame)
    scale_x, scale_y = w / base_w, h / base_h
    
    print("\n=== Stock Detection Debug ===")
    
    for player in ["p1", "p2"]:
        region = get_scaled_region(regions[f"{player}_stocks"], scale_x, scale_y)
        crop = crop_region(frame, region)
        
        print(f"\n{player.upper()} Stocks Region: {region}")
        print(f"Crop shape: {crop.shape}")
        
        # run stock counting
        count = count_stock_icons(frame, regions, player, scale_x, scale_y)
        print(f"Detected stocks: {count}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_detection.py <image_path>")
        print("\nExample:")
        print("  python test_detection.py ../data/frames/sample_frame.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    visualize_detection(image_path)
    test_stock_detection(image_path)

import cv2
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cv.ocr import read_percent
from cv.character_detector import detect_characters

def is_gameplay_frame(frame) -> bool:
    """
    Quick check if this frame looks like actual gameplay vs menu/loading/transition.
    Uses simple heuristics to skip non-game frames.
    """
    h, w = frame.shape[:2]
    
    # check if frame is mostly black (loading/transition)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    if mean_brightness < 20:
        return False
    
    # check for color variance (gameplay has more color diversity than menus)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    if np.mean(saturation) < 30:
        return False
    
    return True

# UI element positions for different layouts
# All coordinates are base resolution, scaled at runtime

# Tournament overlay format (like GOML) - HUD at bottom center
# Based on analysis of actual tournament streams
# Base resolution: 1280x720 (scales to any 16:9)
# Layout: [P1 portrait][P1 %][name]  ...center logo...  [P2 portrait][P2 %][name]
#                [P1 stocks]                                   [P2 stocks]
# VERIFIED from GOML frames - stock dots are small colored dots below player names
UI_REGIONS_TOURNAMENT_720P = {
    "p1_percent": (310, 595, 160, 70),    # P1 percent - shifted LEFT and wider for 3-digit numbers
    "p2_percent": (780, 595, 140, 70),    # P2 percent - wider for 3-digit numbers
    "p1_stocks": (365, 697, 55, 18),      # P1 stock dots - yellow dots at bottom of HUD
    "p2_stocks": (772, 697, 55, 18),      # P2 stock dots - blue dots at bottom of HUD
    "timer": (1100, 20, 100, 45),         # top-right timer
    "stock_icon_width": 12,               # small dots, ~12px each
    "stock_spacing": 3,                   # gap between dots
}

# Tournament overlay for 1080p streams (scaled from 720p by 1.5x)
UI_REGIONS_TOURNAMENT_1080P = {
    "p1_percent": (465, 893, 240, 105),   # scaled from 720p (310,595,160,70) * 1.5
    "p2_percent": (1170, 893, 210, 105),  # scaled from 720p (780,595,140,70) * 1.5  
    "p1_stocks": (548, 1046, 83, 27),     # scaled from 720p
    "p2_stocks": (1158, 1046, 83, 27),    # scaled from 720p
    "timer": (1650, 30, 150, 68),
    "stock_icon_width": 18,
    "stock_spacing": 5,
}

# Standard 720p in-game HUD (no stream overlay)
# HUD is at the far left/right edges of screen
UI_REGIONS_720P = {
    "p1_percent": (85, 600, 130, 70),
    "p2_percent": (1065, 600, 130, 70),
    "p1_stocks": (50, 610, 80, 50),
    "p2_stocks": (1150, 610, 80, 50),
    "timer": (590, 25, 100, 45),
    "stock_icon_width": 20,
    "stock_spacing": 2,
}

# Standard 1080p in-game HUD (no stream overlay)
UI_REGIONS_1080P = {
    "p1_percent": (127, 900, 195, 105),
    "p2_percent": (1598, 900, 195, 105),
    "p1_stocks": (75, 915, 120, 75),
    "p2_stocks": (1725, 915, 120, 75),
    "timer": (885, 38, 150, 68),
    "stock_icon_width": 30,
    "stock_spacing": 5,
}

# VGBootCamp style overlay (HUD closer to center, facecams in corners)
# Based on actual VGC tournament footage analysis
UI_REGIONS_VGC_1080P = {
    "p1_percent": (500, 920, 200, 90),    # P1 percent left of center
    "p2_percent": (1300, 920, 240, 90),   # P2 percent right of center
    "p1_stocks": (500, 1010, 120, 35),    # Stock icons below percent
    "p2_stocks": (1300, 1010, 120, 35),
    "timer": (1780, 10, 140, 60),         # Top-right timer
    "stock_icon_width": 25,
    "stock_spacing": 5,
}

# VGBootCamp 720p (scaled from 1080p by 0.667)
UI_REGIONS_VGC_720P = {
    "p1_percent": (333, 613, 133, 60),
    "p2_percent": (867, 613, 160, 60),
    "p1_stocks": (333, 673, 80, 23),
    "p2_stocks": (867, 673, 80, 23),
    "timer": (1187, 7, 93, 40),
    "stock_icon_width": 17,
    "stock_spacing": 3,
}

def detect_game_state(frame, timestamp: float) -> dict:
    """
    Extract game state from a single frame.
    Returns dict with percents, stocks, positions, etc.
    Tries multiple layout types if the first one fails.
    """
    h, w = frame.shape[:2]
    
    # Try different layouts in order of likelihood
    if h <= 800:
        layouts_to_try = [
            (UI_REGIONS_TOURNAMENT_720P, 1280, 720),
            (UI_REGIONS_VGC_720P, 1280, 720),
            (UI_REGIONS_720P, 1280, 720),
        ]
    else:
        layouts_to_try = [
            (UI_REGIONS_TOURNAMENT_1080P, 1920, 1080),
            (UI_REGIONS_VGC_1080P, 1920, 1080),
            (UI_REGIONS_1080P, 1920, 1080),
        ]
    
    best_state = None
    best_score = 0
    
    for regions, base_w, base_h in layouts_to_try:
        scale_x, scale_y = w / base_w, h / base_h
        
        state = {
            "timestamp": round(timestamp, 2),
            "p1_percent": None,
            "p2_percent": None,
            "p1_stocks": None,
            "p2_stocks": None,
            "p1_character": None,
            "p2_character": None,
        }
        
        # read percent values using OCR
        p1_region = get_scaled_region(regions["p1_percent"], scale_x, scale_y)
        p2_region = get_scaled_region(regions["p2_percent"], scale_x, scale_y)
        
        p1_crop = crop_region(frame, p1_region)
        p2_crop = crop_region(frame, p2_region)
        
        state["p1_percent"] = read_percent(p1_crop)
        state["p2_percent"] = read_percent(p2_crop)
        
        # count stocks
        state["p1_stocks"] = count_stock_icons(frame, regions, "p1", scale_x, scale_y)
        state["p2_stocks"] = count_stock_icons(frame, regions, "p2", scale_x, scale_y)
        
        # Score this layout - prefer layouts that detect both percents
        score = 0
        if state["p1_percent"] is not None:
            score += 2
        if state["p2_percent"] is not None:
            score += 2
        if state["p1_stocks"] is not None:
            score += 1
        if state["p2_stocks"] is not None:
            score += 1
        
        if score > best_score:
            best_score = score
            best_state = state
            
        # If we got both percents, use this layout
        if state["p1_percent"] is not None and state["p2_percent"] is not None:
            break
    
    # Detect characters (only if we have a valid state)
    if best_state and best_score > 0:
        chars = detect_characters(frame)
        best_state["p1_character"] = chars.get("p1_character")
        best_state["p2_character"] = chars.get("p2_character")
        return best_state
    
    return None


def detect_layout(frame) -> tuple:
    """
    Detect which HUD layout is being used (tournament overlay vs standard).
    Returns (regions_dict, base_width, base_height).
    
    Detection strategy:
    1. Check for HUD elements in center-bottom (tournament) vs edges (standard)
    2. Look for character portraits and percent numbers
    """
    h, w = frame.shape[:2]
    aspect_ratio = w / h
    
    # only support 16:9 aspect ratio
    if not (1.7 < aspect_ratio < 1.8):
        # non-standard aspect, try tournament layout as default
        if h <= 800:
            return UI_REGIONS_TOURNAMENT_720P, 1280, 720
        else:
            return UI_REGIONS_TOURNAMENT_1080P, 1920, 1080
    
    # check for tournament overlay by looking for colorful HUD in center-bottom
    # standard in-game HUD is at far left/right edges
    
    is_tournament = _detect_tournament_overlay(frame)
    
    if h <= 800:
        # 720p or scaled
        if is_tournament:
            return UI_REGIONS_TOURNAMENT_720P, 1280, 720
        else:
            return UI_REGIONS_720P, 1280, 720
    else:
        # 1080p or higher
        if is_tournament:
            return UI_REGIONS_TOURNAMENT_1080P, 1920, 1080
        else:
            return UI_REGIONS_1080P, 1920, 1080


def _detect_tournament_overlay(frame) -> bool:
    """
    Detect if the frame has a tournament overlay (HUD in center)
    vs standard in-game HUD (at edges).
    """
    h, w = frame.shape[:2]
    
    # sample center-bottom region where tournament HUD would be
    # tournament overlays have character portraits and percents near center
    center_left = int(w * 0.2)
    center_right = int(w * 0.8)
    bottom_start = int(h * 0.75)
    
    center_region = frame[bottom_start:, center_left:center_right]
    
    # sample edge regions where standard HUD would be
    left_edge = frame[bottom_start:, :int(w * 0.15)]
    right_edge = frame[bottom_start:, int(w * 0.85):]
    
    # analyze color content - HUD elements are typically colorful
    def get_color_score(region):
        if region.size == 0:
            return 0
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        # high saturation = colorful (HUD elements)
        sat = hsv[:, :, 1]
        val = hsv[:, :, 2]
        # count pixels that are both colorful and bright
        colorful_bright = np.sum((sat > 80) & (val > 100))
        return colorful_bright / region.size * 100
    
    center_score = get_color_score(center_region)
    edge_score = (get_color_score(left_edge) + get_color_score(right_edge)) / 2
    
    # also check for edge density (text/numbers)
    def get_edge_score(region):
        if region.size == 0:
            return 0
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return np.sum(edges > 0) / edges.size * 100
    
    center_edges = get_edge_score(center_region)
    edge_edges = (get_edge_score(left_edge) + get_edge_score(right_edge)) / 2
    
    # tournament overlay: more content in center
    # standard HUD: more content at edges
    center_total = center_score + center_edges
    edge_total = edge_score + edge_edges
    
    # if center has significantly more visual content, it's tournament
    return center_total > edge_total * 1.2

def get_scaled_region(region, scale_x, scale_y):
    x, y, w, h = region
    return (int(x * scale_x), int(y * scale_y), int(w * scale_x), int(h * scale_y))

def crop_region(frame, region):
    x, y, w, h = region
    return frame[y:y+h, x:x+w]

def count_stock_icons(frame, regions: dict, player: str, scale_x, scale_y) -> int:
    """
    Count stock icons (character head portraits) for a player.
    
    Stock icons in Smash Ultimate are small character head portraits arranged
    horizontally. Each player starts with 3 and loses them from right to left.
    """
    region_key = f"{player}_stocks"
    region = get_scaled_region(regions[region_key], scale_x, scale_y)
    crop = crop_region(frame, region)
    
    if crop is None or crop.size == 0:
        return None
    
    crop_h, crop_w = crop.shape[:2]
    
    # get expected icon dimensions from config
    icon_width = int(regions.get("stock_icon_width", 25) * scale_x)
    icon_spacing = int(regions.get("stock_spacing", 4) * scale_x)
    
    # try multiple detection methods and pick most reliable
    results = []
    
    # method 1: detect distinct colored regions (character heads are colorful)
    count1 = _count_by_colored_blobs(crop, icon_width)
    if count1 is not None:
        results.append(count1)
    
    # method 2: analyze horizontal profile for distinct peaks
    count2 = _count_by_horizontal_profile(crop, icon_width, icon_spacing)
    if count2 is not None:
        results.append(count2)
    
    # method 3: detect by edge contours with shape filtering
    count3 = _count_by_contours(crop, icon_width, scale_x, scale_y)
    if count3 is not None:
        results.append(count3)
    
    if not results:
        return None
    
    # return the most common result (mode), biased toward 3 if tied
    # (more likely to have 3 stocks than fewer at any given moment)
    from collections import Counter
    counts = Counter(results)
    if counts:
        # if there's a tie including 3, prefer 3
        max_count = max(counts.values())
        candidates = [k for k, v in counts.items() if v == max_count]
        return max(candidates)  # prefer higher stock count in ties
    
    return None


def _count_by_colored_blobs(crop, expected_icon_width: int) -> int:
    """
    Count stock icons by finding distinct colored blobs.
    Character head icons are typically colorful with distinct outlines.
    """
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    
    # look for pixels with moderate-to-high saturation and value
    # this captures the colorful character art but ignores dark backgrounds
    lower = np.array([0, 30, 60])
    upper = np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    
    # morphological operations to clean up and separate icons
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # filter contours by size - should be roughly icon-sized
    min_area = (expected_icon_width * 0.5) ** 2
    max_area = (expected_icon_width * 2.5) ** 2
    
    valid_contours = []
    for c in contours:
        area = cv2.contourArea(c)
        if min_area < area < max_area:
            x, y, w, h = cv2.boundingRect(c)
            # icon should be roughly square-ish (not super wide or tall)
            aspect = max(w, h) / (min(w, h) + 0.001)
            if aspect < 2.5:
                valid_contours.append((x, c))
    
    # sort by x position and merge nearby contours (same icon)
    if not valid_contours:
        return 0
    
    valid_contours.sort(key=lambda x: x[0])
    
    # count distinct icons by checking x-position gaps
    icon_count = 1
    last_x = valid_contours[0][0]
    
    for x, c in valid_contours[1:]:
        # if there's a significant gap, it's a new icon
        if x - last_x > expected_icon_width * 0.7:
            icon_count += 1
        last_x = x
    
    return min(icon_count, 3)


def _count_by_horizontal_profile(crop, expected_icon_width: int, expected_spacing: int) -> int:
    """
    Count stock icons by analyzing the horizontal intensity profile.
    Icons create peaks in the profile, gaps create valleys.
    """
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    
    # compute vertical sum (horizontal profile)
    profile = np.sum(gray, axis=0).astype(float)
    
    if len(profile) < 10:
        return None
    
    # smooth the profile
    kernel_size = max(3, expected_icon_width // 4)
    if kernel_size % 2 == 0:
        kernel_size += 1
    profile_smooth = cv2.GaussianBlur(profile.reshape(1, -1), (kernel_size, 1), 0).flatten()
    
    # find peaks (icon locations)
    # a peak is a local maximum above threshold
    threshold = np.mean(profile_smooth) + np.std(profile_smooth) * 0.3
    
    peaks = []
    for i in range(1, len(profile_smooth) - 1):
        if profile_smooth[i] > threshold:
            if profile_smooth[i] >= profile_smooth[i-1] and profile_smooth[i] >= profile_smooth[i+1]:
                # check it's a significant peak, not noise
                if len(peaks) == 0 or i - peaks[-1] > expected_icon_width * 0.5:
                    peaks.append(i)
    
    return min(len(peaks), 3) if peaks else 0


def _count_by_contours(crop, expected_icon_width: int, scale_x: float, scale_y: float) -> int:
    """
    Count stock icons using edge detection and contour analysis.
    """
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    
    # apply edge detection
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 30, 100)
    
    # dilate to connect edge fragments
    kernel = np.ones((2, 2), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)
    
    # find contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # filter by area
    min_area = (expected_icon_width * 0.3) ** 2
    max_area = (expected_icon_width * 3) ** 2
    
    valid_xs = []
    for c in contours:
        area = cv2.contourArea(c)
        if min_area < area < max_area:
            x, y, w, h = cv2.boundingRect(c)
            valid_xs.append(x + w // 2)  # center x
    
    if not valid_xs:
        return 0
    
    # cluster x positions to count distinct icons
    valid_xs.sort()
    icon_count = 1
    last_x = valid_xs[0]
    
    for x in valid_xs[1:]:
        if x - last_x > expected_icon_width * 0.6:
            icon_count += 1
            last_x = x
    
    return min(icon_count, 3)

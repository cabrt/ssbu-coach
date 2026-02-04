import cv2
import numpy as np
from pathlib import Path

# character portrait regions relative to 1280x720
# these capture the character render at the bottom of the screen
PORTRAIT_REGIONS_720P = {
    "p1": (200, 580, 100, 100),   # x, y, w, h - left side character (e.g., Cloud)
    "p2": (700, 570, 110, 110),   # right side character (e.g., Wolf)
}

# known character color profiles (dominant colors in portraits)
# HSV hue ranges: red=0-10,170-180, orange=10-25, yellow=25-40, green=40-80, blue=80-130, purple=130-160, pink=160-170
CHARACTER_COLORS = {
    "mario": {"hue": (0, 15), "sat_min": 100},
    "cloud": {"hue": (15, 45), "sat_min": 30},      # blonde hair
    "fox": {"hue": (10, 30), "sat_min": 80},
    "wolf": {"hue": (0, 180), "sat_min": 0, "sat_max": 60},  # gray/desaturated
    "pikachu": {"hue": (20, 40), "sat_min": 150},
    "kirby": {"hue": (150, 175), "sat_min": 80},
    "link": {"hue": (35, 70), "sat_min": 50},
    "samus": {"hue": (10, 30), "sat_min": 100},
    "joker": {"hue": (0, 180), "sat_min": 0, "sat_max": 40},  # mostly black
    "roy": {"hue": (0, 20), "sat_min": 80},         # red hair
    "marth": {"hue": (100, 130), "sat_min": 50},    # blue hair
}

def detect_characters(frame) -> dict:
    """
    Detect characters from their UI portraits.
    Returns dict with p1_character and p2_character.
    """
    h, w = frame.shape[:2]
    
    if h <= 720:
        regions = PORTRAIT_REGIONS_720P
        base_w, base_h = 1280, 720
    else:
        # scale for 1080p
        regions = {k: tuple(int(v * 1.5) for v in vals) 
                   for k, vals in PORTRAIT_REGIONS_720P.items()}
        base_w, base_h = 1920, 1080
    
    scale_x, scale_y = w / base_w, h / base_h
    
    result = {
        "p1_character": None,
        "p2_character": None,
    }
    
    for player in ["p1", "p2"]:
        region = regions[player]
        x, y, rw, rh = [int(v * (scale_x if i % 2 == 0 else scale_y)) 
                       for i, v in enumerate(region)]
        
        portrait = frame[y:y+rh, x:x+rw]
        if portrait.size == 0:
            continue
        
        # analyze portrait colors
        character = identify_character(portrait)
        result[f"{player}_character"] = character
    
    return result

def identify_character(portrait) -> str:
    """
    Identify character from their portrait using color analysis.
    Returns character name or None if unknown.
    """
    if portrait is None or portrait.size == 0:
        return None
    
    # convert to HSV for color analysis
    hsv = cv2.cvtColor(portrait, cv2.COLOR_BGR2HSV)
    
    hue = hsv[:, :, 0].flatten()
    sat = hsv[:, :, 1].flatten()
    val = hsv[:, :, 2].flatten()
    
    # filter out very dark pixels (background)
    bright_mask = val > 50
    if np.sum(bright_mask) < 100:
        return None
    
    median_hue = np.median(hue[bright_mask])
    median_sat = np.median(sat[bright_mask])
    
    # match against known characters
    best_match = None
    best_score = float('inf')
    
    for char, props in CHARACTER_COLORS.items():
        hue_low, hue_high = props["hue"]
        sat_min = props.get("sat_min", 0)
        sat_max = props.get("sat_max", 255)
        
        # check if saturation is in range
        if not (sat_min <= median_sat <= sat_max):
            continue
        
        # check if hue is in range
        if hue_low <= median_hue <= hue_high:
            # calculate match score (lower is better)
            hue_center = (hue_low + hue_high) / 2
            score = abs(median_hue - hue_center)
            
            if score < best_score:
                best_score = score
                best_match = char
    
    return best_match

def extract_portrait(frame, player: str) -> np.ndarray:
    """Extract character portrait region for a player."""
    h, w = frame.shape[:2]
    
    if h <= 720:
        regions = PORTRAIT_REGIONS_720P
        base_w, base_h = 1280, 720
    else:
        regions = {k: tuple(int(v * 1.5) for v in vals) 
                   for k, vals in PORTRAIT_REGIONS_720P.items()}
        base_w, base_h = 1920, 1080
    
    scale_x, scale_y = w / base_w, h / base_h
    
    region = regions[player]
    x, y, rw, rh = [int(v * (scale_x if i % 2 == 0 else scale_y)) 
                   for i, v in enumerate(region)]
    
    return frame[y:y+rh, x:x+rw]

import cv2
import numpy as np
import re

# will use easyocr for better accuracy on stylized game text
_reader = None

def get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader

def read_percent(image, min_confidence: float = 0.4) -> float:
    """
    Read damage percent from a cropped image region.
    Returns the percent as a float (e.g., 13.8), or None if not detected.
    
    Args:
        image: Cropped image of percent region
        min_confidence: Minimum OCR confidence to accept (0-1)
    """
    if image is None or image.size == 0:
        return None
    
    reader = get_reader()
    
    # try multiple preprocessing approaches and pick best result
    results_all = []
    
    # approach 1: red/orange color mask (standard smash percent colors)
    result1 = _read_with_color_mask(image, reader)
    if result1:
        results_all.append(result1)
    
    # approach 2: high saturation mask (catches more color variations)
    result2 = _read_with_saturation_mask(image, reader)
    if result2:
        results_all.append(result2)
    
    # approach 3: simple grayscale threshold (fallback)
    result3 = _read_grayscale(image, reader)
    if result3:
        results_all.append(result3)
    
    if not results_all:
        return None
    
    # Pick the result with highest confidence
    best = max(results_all, key=lambda x: x[1])
    percent, confidence = best
    
    if confidence >= min_confidence:
        return percent
    
    return None


def _read_with_color_mask(image, reader) -> tuple:
    """Read percent using red/orange color extraction."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # red/orange hue mask (0-20 and 160-180 for red, expanded range)
    lower_red1 = np.array([0, 80, 80])
    upper_red1 = np.array([20, 255, 255])
    lower_red2 = np.array([160, 80, 80])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 | mask2
    
    # check if mask found anything
    if np.sum(mask) < 100:
        return None
    
    result = cv2.bitwise_and(image, image, mask=mask)
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    scaled = cv2.resize(thresh, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    
    return _extract_percent_from_image(scaled, reader)


def _read_with_saturation_mask(image, reader) -> tuple:
    """Read percent using high saturation mask (catches colored text)."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # high saturation mask - any brightly colored text
    lower = np.array([0, 100, 100])
    upper = np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    
    if np.sum(mask) < 100:
        return None
    
    result = cv2.bitwise_and(image, image, mask=mask)
    gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
    scaled = cv2.resize(thresh, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    
    return _extract_percent_from_image(scaled, reader)


def _read_grayscale(image, reader) -> tuple:
    """Fallback: read percent from grayscale - simple scaling works best."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # simple upscaling works better than adaptive threshold for game UI text
    scaled = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    
    return _extract_percent_from_image(scaled, reader)


def _extract_percent_from_image(processed_image, reader) -> tuple:
    """
    Extract percent value from preprocessed image.
    Returns (percent as float, confidence) tuple or None.
    """
    try:
        # include decimal point in allowlist (tournament overlays show 13.8%)
        results = reader.readtext(processed_image, allowlist='0123456789.%')
        
        if not results:
            return None
        
        # collect all text segments with their positions
        all_texts = []
        for (bbox, text, conf) in results:
            cleaned = text.replace('%', '').strip()
            if cleaned:
                all_texts.append((cleaned, conf, bbox))
        
        if not all_texts:
            return None
        
        # sort by x-coordinate (left to right)
        all_texts.sort(key=lambda x: x[2][0][0] if x[2] else 0)
        
        best_percent = None
        best_conf = 0
        
        # IMPORTANT: Handle the case where OCR splits "13.8" into "13" and "8"
        # Combine them back into a decimal number
        if len(all_texts) >= 2:
            first_text = all_texts[0][0]
            second_text = all_texts[1][0]
            
            # Check if this looks like a decimal split: ["13", "8"] or ["13", ".8"]
            first_nums = re.findall(r'\d+', first_text)
            second_nums = re.findall(r'\d+', second_text)
            
            if first_nums and second_nums:
                first_num = int(first_nums[0])
                second_num = int(second_nums[0])
                
                # If first is 1-3 digits and second is 1 digit, likely decimal split
                # Combine into a float: 13 and 8 -> 13.8
                if first_num <= 200 and 0 <= second_num <= 9:
                    combined = float(f"{first_num}.{second_num}")
                    avg_conf = (all_texts[0][1] + all_texts[1][1]) / 2
                    if avg_conf > best_conf:
                        best_percent = combined
                        best_conf = avg_conf
        
        # Also try each individual result
        for (text, conf, bbox) in all_texts:
            if not text:
                continue
            
            # Try to parse as a decimal number first (e.g., "13.8")
            if '.' in text:
                try:
                    decimal_val = float(text)
                    if 0 <= decimal_val <= 200:
                        if conf > best_conf:
                            best_percent = decimal_val
                            best_conf = conf
                        continue
                except ValueError:
                    pass
                
                # fallback: take integer part only
                parts = text.split('.')
                text = parts[0] if parts[0] else None
                if not text:
                    continue
            
            nums = re.findall(r'\d+', text)
            
            if nums:
                num_str = nums[0]
                
                # take first 5 digits max
                if len(num_str) > 5:
                    num_str = num_str[:5]
                
                if not num_str:
                    continue
                
                # SMASH ULTIMATE PERCENT FORMAT:
                # The display shows XX.Y% where the last digit is always the decimal/tenth.
                # When OCR captures all digits, we have:
                # - 3 digits (e.g., "138") → 13.8%  (tens + tenth)
                # - 4 digits (e.g., "1014") → 101.4%  (hundreds + tenth) or XX.Y + noise
                # - 5+ digits → likely has "%" noise at end
                #
                # Special cases:
                # - 2 digits (e.g., "13") → OCR missed decimal, treat as 13.0%
                # - 1 digit (e.g., "8") → could be 8.0% or just noise
                
                percent = None
                
                if len(num_str) == 2:
                    # 2 digits: OCR likely missed the decimal portion
                    # "13" from display "13.X%" → treat as 13.0%
                    # "72" from display "72.X%" → treat as 72.0%
                    percent = float(num_str)
                
                elif len(num_str) == 3:
                    # 3 digits: XX.Y% (10.0% to 99.9%)
                    main = int(num_str[:2])
                    decimal = int(num_str[2])
                    percent = float(f"{main}.{decimal}")
                
                elif len(num_str) == 4:
                    # 4 digits: Could be XXX.Y% (100.0% to 300.0%)
                    # OR could be XX.Y + "%" noise (more common case)
                    #
                    # The "%" symbol is often read as "5" or another digit.
                    # We need to distinguish:
                    # - "1014" from display "101.4%" → should be 101.4%
                    # - "1385" from display "13.8%" → should be 13.8% (5 is % noise)
                    #
                    # Heuristic: Only interpret as hundreds if first digit is "1" or "2"
                    # AND the resulting value would be 100-129 (very common) or 200+ (rare but valid)
                    # For ambiguous cases like 130-199, prefer XX.Y interpretation
                    first_digit = int(num_str[0])
                    first_three = int(num_str[:3])
                    
                    if first_digit == 1 and first_three <= 129:
                        # Clearly 100-129 range (common high percent)
                        decimal = int(num_str[3])
                        percent = float(f"{first_three}.{decimal}")
                    elif first_digit == 2:
                        # 200+ range (rare but valid)
                        decimal = int(num_str[3])
                        percent = float(f"{first_three}.{decimal}")
                    else:
                        # Likely XX.Y + noise (e.g., "1385" from "13.8%", "7255" from "72.5%")
                        main2 = int(num_str[:2])
                        decimal2 = int(num_str[2])
                        percent = float(f"{main2}.{decimal2}")
                
                elif len(num_str) == 5:
                    # 5 digits: Likely XXX.Y + noise OR XX.Y + double noise
                    first_digit = int(num_str[0])
                    first_three = int(num_str[:3])
                    
                    if first_digit == 1 and first_three <= 129:
                        # 100-129 range + noise
                        decimal = int(num_str[3])
                        percent = float(f"{first_three}.{decimal}")
                    elif first_digit == 2:
                        # 200+ range + noise
                        decimal = int(num_str[3])
                        percent = float(f"{first_three}.{decimal}")
                    else:
                        # XX.Y + double noise
                        main2 = int(num_str[:2])
                        decimal2 = int(num_str[2])
                        percent = float(f"{main2}.{decimal2}")
                
                elif len(num_str) == 1:
                    # Single digit - could be just the decimal part (noise)
                    # or a very low percent like 0%
                    percent = float(num_str)
                
                if percent is None:
                    continue
                
                # Penalize single-digit reads 1-9 (often just decimal parts)
                effective_conf = conf
                if 1 <= percent <= 9 and len(num_str) == 1:
                    effective_conf *= 0.4  # stronger penalty for suspicious single digits
                
                # sanity check: Smash percent realistically goes 0-200
                if 0 <= percent <= 200 and effective_conf > best_conf:
                    best_percent = percent
                    best_conf = effective_conf
        
        if best_percent is not None:
            return (best_percent, best_conf)
    except:
        pass
    
    return None

def read_timer(image) -> str:
    """Read game timer from cropped region."""
    if image is None or image.size == 0:
        return None
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    
    try:
        reader = get_reader()
        results = reader.readtext(thresh, allowlist='0123456789:')
        
        for (bbox, text, conf) in results:
            if ':' in text or len(text) >= 3:
                return text
    except:
        pass
    
    return None

"""
Hitbox reference image fetcher for SSBU move identification.

Downloads hitbox GIF animations from ultimateframedata.com on demand,
extracts the active hitbox frame, and provides reference images for
GPT-4o vision to compare against gameplay footage.
"""

import re
import os
import logging
from pathlib import Path
from io import BytesIO
from typing import Optional

import requests
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

_UFD_BASE = "https://ultimateframedata.com"
_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "hitbox_cache"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Map our internal move names to UFD GIF suffixes
_MOVE_TO_SUFFIX = {
    "jab": "Jab1",
    "jab combo": "Jab1",
    "ftilt": "FTilt",
    "utilt": "UTilt",
    "dtilt": "DTilt",
    "dash attack": "DashAttack",
    "fsmash": "FSmash",
    "usmash": "USmash",
    "dsmash": "DSmash",
    "nair": "NAir",
    "fair": "FAir",
    "bair": "BAir",
    "uair": "UAir",
    "dair": "DAir",
    "fthrow": "FThrow",
    "bthrow": "BThrow",
    "uthrow": "UThrow",
    "dthrow": "DThrow",
}

# Map our character keys to UFD URL slugs
# Characters whose key matches the slug directly don't need an entry
_CHAR_TO_SLUG = {
    "banjo": "banjo_and_kazooie",
    "bowser jr": "bowser_jr",
    "captain falcon": "captain_falcon",
    "charizard": "charizard",
    "dark pit": "dark_pit",
    "dark samus": "dark_samus",
    "diddy kong": "diddy_kong",
    "donkey kong": "donkey_kong",
    "dr. mario": "dr_mario",
    "dr mario": "dr_mario",
    "duck hunt": "duck_hunt",
    "ice climbers": "ice_climbers",
    "ivysaur": "ivysaur",
    "king dedede": "king_dedede",
    "king k. rool": "king_k_rool",
    "king k rool": "king_k_rool",
    "little mac": "little_mac",
    "mega man": "mega_man",
    "meta knight": "meta_knight",
    "mii brawler": "mii_brawler",
    "mii gunner": "mii_gunner",
    "mii swordfighter": "mii_swordfighter",
    "mr. game & watch": "mr_game_and_watch",
    "mr game and watch": "mr_game_and_watch",
    "game and watch": "mr_game_and_watch",
    "pac-man": "pac_man",
    "pac man": "pac_man",
    "piranha plant": "piranha_plant",
    "r.o.b.": "rob",
    "rob": "rob",
    "rosalina": "rosalina_and_luma",
    "rosalina and luma": "rosalina_and_luma",
    "squirtle": "squirtle",
    "toon link": "toon_link",
    "wii fit trainer": "wii_fit_trainer",
    "young link": "young_link",
    "zero suit samus": "zero_suit_samus",
}

# Cache: slug -> {move_suffix -> gif_url}
_gif_url_cache: dict[str, dict[str, str]] = {}


def _get_slug(character: str) -> str:
    """Convert character name to UFD URL slug."""
    char_key = character.strip().lower()
    if char_key in _CHAR_TO_SLUG:
        return _CHAR_TO_SLUG[char_key]
    # Default: replace spaces/dots with underscores
    return re.sub(r'[.\s]+', '_', char_key).strip('_')


def _scrape_gif_urls(slug: str) -> dict[str, str]:
    """Scrape all hitbox GIF URLs from a character's UFD page."""
    if slug in _gif_url_cache:
        return _gif_url_cache[slug]

    url = f"{_UFD_BASE}/{slug}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch UFD page for {slug}: {e}")
        _gif_url_cache[slug] = {}
        return {}

    # Extract all GIF paths
    pattern = rf'hitboxes/{re.escape(slug)}/([^"]+\.gif)'
    matches = re.findall(pattern, resp.text, re.IGNORECASE)

    # Build mapping: GIF filename (without prefix) -> full URL
    url_map = {}
    for filename in set(matches):
        full_url = f"{_UFD_BASE}/hitboxes/{slug}/{filename}"
        # Strip the character prefix to get the move suffix
        # e.g., "CloudBAir.gif" -> "BAir"
        base = filename.rsplit('.', 1)[0]  # Remove .gif
        # Find where the move suffix starts (after character prefix)
        for suffix in _MOVE_TO_SUFFIX.values():
            if base.endswith(suffix) or base.lower().endswith(suffix.lower()):
                url_map[suffix] = full_url
                break

    _gif_url_cache[slug] = url_map
    logger.info(f"Scraped {len(url_map)} hitbox GIF URLs for {slug}")
    return url_map


def _download_gif(url: str, cache_path: Path) -> Optional[Path]:
    """Download a GIF and save to cache."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(resp.content)
        return cache_path
    except Exception as e:
        logger.warning(f"Failed to download GIF {url}: {e}")
        return None


def _extract_hitbox_frame(gif_path: Path) -> Optional[Path]:
    """
    Extract the frame showing the active hitbox from a GIF.
    Looks for the frame with the most red/colored (hitbox indicator) pixels.
    Saves as PNG and returns the path.
    """
    png_path = gif_path.with_suffix('.png')
    if png_path.exists():
        return png_path

    try:
        img = Image.open(gif_path)
    except Exception as e:
        logger.warning(f"Failed to open GIF {gif_path}: {e}")
        return None

    best_frame = 0
    best_score = 0

    for i in range(img.n_frames):
        img.seek(i)
        frame = img.convert('RGBA')
        arr = np.array(frame)
        # Detect hitbox colors: red, purple/magenta, yellow, blue circles
        r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
        visible = a > 100
        # Red hitboxes (high R, low G, low B)
        red = visible & (r > 170) & (g < 100) & (b < 100)
        # Purple/magenta hitboxes (high R, low G, high B)
        purple = visible & (r > 140) & (g < 80) & (b > 140)
        # Yellow hitboxes (high R, high G, low B)
        yellow = visible & (r > 180) & (g > 150) & (b < 80)
        # Blue hitboxes
        blue = visible & (r < 80) & (g < 80) & (b > 170)

        score = int(red.sum() + purple.sum() + yellow.sum() + blue.sum())
        if score > best_score:
            best_score = score
            best_frame = i

    if best_score == 0:
        # No hitbox colors found — just use middle frame
        best_frame = img.n_frames // 2

    img.seek(best_frame)
    # Convert to RGB (drop alpha, use gray background)
    frame = img.convert('RGBA')
    bg = Image.new('RGBA', frame.size, (100, 100, 100, 255))
    composite = Image.alpha_composite(bg, frame)
    composite = composite.convert('RGB')

    # Resize to reasonable size for API (max 512px on longest side)
    max_dim = 512
    w, h = composite.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        composite = composite.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    composite.save(png_path, 'PNG', optimize=True)
    return png_path


def get_hitbox_image(character: str, move_name: str) -> Optional[Path]:
    """
    Get the active hitbox reference image for a character's move.
    Downloads from UFD on first request, caches locally.

    Args:
        character: Character name (e.g., "cloud", "Captain Falcon")
        move_name: Our internal move name (e.g., "bair", "dash attack")

    Returns:
        Path to PNG image, or None if unavailable.
    """
    move_key = move_name.strip().lower()
    suffix = _MOVE_TO_SUFFIX.get(move_key)
    if not suffix:
        return None

    slug = _get_slug(character)

    # Check cache first
    png_path = _CACHE_DIR / slug / f"{suffix}.png"
    if png_path.exists():
        return png_path

    gif_path = _CACHE_DIR / slug / f"{suffix}.gif"
    if not gif_path.exists():
        # Scrape URL and download
        url_map = _scrape_gif_urls(slug)
        gif_url = url_map.get(suffix)
        if not gif_url:
            return None
        if not _download_gif(gif_url, gif_path):
            return None

    return _extract_hitbox_frame(gif_path)


def get_candidate_hitbox_images(
    character: str, move_candidates: list[tuple[str, float]]
) -> list[tuple[str, float, Optional[Path]]]:
    """
    For a list of candidate moves (from get_candidate_moves), fetch hitbox
    reference images for each.

    Args:
        character: Character name
        move_candidates: List of (move_name, damage) from get_candidate_moves

    Returns:
        List of (move_name, damage, image_path_or_None)
    """
    results = []
    for name, dmg in move_candidates:
        img_path = get_hitbox_image(character, name)
        results.append((name, dmg, img_path))
    return results

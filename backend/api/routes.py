from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
import uuid
import shutil
import sys
from pathlib import Path

# add backend dir to path for imports
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from cv.video_processor import process_video
from analysis.coaching import generate_coaching
from analysis.characters import ALL_CHARACTERS

router = APIRouter()

@router.get("/characters")
async def get_characters():
    """Return list of all Smash Ultimate characters."""
    return {"characters": ALL_CHARACTERS}

UPLOAD_DIR = Path(__file__).parent.parent.parent / "data" / "videos"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SAVED_ANALYSES_DIR = Path(__file__).parent.parent.parent / "data" / "saved_analyses"
SAVED_ANALYSES_DIR.mkdir(parents=True, exist_ok=True)

# store analysis results in memory (would use db in production)
analyses = {}

# Load any previously saved analyses on startup
import json
for f in SAVED_ANALYSES_DIR.glob("*.json"):
    try:
        with open(f) as fp:
            data = json.load(fp)
            video_id = data.get("video_id")
            if video_id:
                analyses[video_id] = data
    except:
        pass

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...), 
    background_tasks: BackgroundTasks = None,
    player_char: str = None,
    opponent_char: str = None,
    you_are_p1: str = "true"
):
    """
    you_are_p1: "true" if you are the left/red player (P1), "false" if you are the right/blue player (P2).
    Coaching will be framed from your perspective.
    """
    if not file.filename.endswith(('.mp4', '.mov', '.webm')):
        raise HTTPException(400, "Only video files allowed")
    
    video_id = str(uuid.uuid4())[:8]
    video_path = UPLOAD_DIR / f"{video_id}.mp4"
    
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    is_p1 = you_are_p1.lower() not in ("false", "0", "no")
    
    analyses[video_id] = {"status": "processing", "progress": 0}
    background_tasks.add_task(run_analysis, video_id, str(video_path), player_char, opponent_char, is_p1)
    
    return {"video_id": video_id, "status": "processing"}

@router.get("/status/{video_id}")
async def get_status(video_id: str):
    if video_id not in analyses:
        raise HTTPException(404, "Video not found")
    data = analyses[video_id]
    return {
        "status": data.get("status"),
        "progress": data.get("progress", 0),
        "eta_seconds": data.get("eta_seconds"),
    }

@router.get("/results/{video_id}")
async def get_results(video_id: str):
    if video_id not in analyses:
        raise HTTPException(404, "Video not found")
    
    analysis = analyses[video_id]
    if analysis["status"] != "complete":
        return {
            "status": analysis["status"], 
            "progress": analysis.get("progress", 0),
            "eta_seconds": analysis.get("eta_seconds"),
        }
    
    return analysis

def _run_analysis_sync(video_id: str, video_path: str, player_char: str = None, opponent_char: str = None, you_are_p1: bool = True):
    """Synchronous analysis function to run in thread pool."""
    import time
    import cv2
    try:
        # Get video duration for ETA calculation
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        cap.release()
        
        # Estimate total time based on video duration (roughly 2-3x video length)
        estimated_total_seconds = max(duration * 2.5, 60)  # at least 60 seconds
        start_time = time.time()
        
        # extract game states from video (0-70% of progress)
        analyses[video_id]["status"] = "extracting"
        analyses[video_id]["estimated_total"] = estimated_total_seconds
        analyses[video_id]["start_time"] = start_time
        
        def extraction_progress(p):
            elapsed = time.time() - start_time
            progress = int(p * 70)
            # Calculate ETA based on extraction rate
            if p > 0.1:
                extraction_eta = (elapsed / p) * (1 - p)  # time for rest of extraction
                analysis_eta = estimated_total_seconds * 0.3  # estimate 30% for analysis
                total_eta = int(extraction_eta + analysis_eta)
            else:
                total_eta = int(estimated_total_seconds - elapsed)
            
            analyses[video_id]["progress"] = progress
            analyses[video_id]["eta_seconds"] = max(0, total_eta)
        
        game_states = process_video(video_path, progress_callback=extraction_progress)
        
        # generate coaching feedback (70-100% of progress)
        analyses[video_id]["status"] = "analyzing"
        analyses[video_id]["progress"] = 70
        
        # Estimate remaining time for analysis phase
        elapsed = time.time() - start_time
        analysis_eta = max(30, int((estimated_total_seconds - elapsed) * 0.5))
        analyses[video_id]["eta_seconds"] = analysis_eta
        
        # Update progress incrementally during analysis
        analyses[video_id]["progress"] = 75
        coaching = generate_coaching(game_states, player_char=player_char, opponent_char=opponent_char, you_are_p1=you_are_p1)
        
        analyses[video_id]["progress"] = 85
        analyses[video_id]["eta_seconds"] = 30
        
        # Enhance key tips with Vision API context (damage taken and combos)
        coaching = enhance_tips_with_vision(
            coaching, video_path, player_char, opponent_char, you_are_p1
        )
        
        analyses[video_id]["progress"] = 95
        analyses[video_id]["eta_seconds"] = 5
        
        analyses[video_id] = {
            "status": "complete",
            "progress": 100,
            "eta_seconds": 0,
            "video_id": video_id,
            "video_path": video_path,  # store for frame extraction
            "game_states": game_states,
            "coaching": coaching,
            "player_char": player_char,
            "opponent_char": opponent_char,
            "you_are_p1": you_are_p1,
        }
    except Exception as e:
        import traceback
        analyses[video_id] = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


def enhance_tips_with_vision(coaching: dict, video_path: str, player_char: str, opponent_char: str, you_are_p1: bool) -> dict:
    """
    Enhance damage_taken and combo tips with Vision API analysis.
    Analyzes frames to identify specific moves and provide detailed context.
    """
    import os
    import cv2
    import base64
    
    if not os.getenv("OPENAI_API_KEY") or not video_path or not os.path.exists(video_path):
        return coaching
    
    from openai import OpenAI
    client = OpenAI()
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    enhanced_tips = []
    
    for tip in coaching.get("tips", []):
        tip_type = tip.get("type", "")
        timestamp = tip.get("timestamp", 0)
        
        # Only enhance damage_taken and combo tips
        if tip_type not in ["damage_taken", "combo"]:
            enhanced_tips.append(tip)
            continue
        
        try:
            # Extract frame at this timestamp
            frame_num = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            
            if not ret:
                enhanced_tips.append(tip)
                continue
            
            # Resize for API
            h, w = frame.shape[:2]
            if w > 1280:
                scale = 1280 / w
                frame = cv2.resize(frame, (1280, int(h * scale)))
            
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Different prompts for damage taken vs combos
            if tip_type == "damage_taken":
                prompt = f"""Analyze this Super Smash Bros Ultimate frame. The player ({player_char}) just took damage from the opponent ({opponent_char}).

Based on what you see:
1. What move did {opponent_char} use to hit {player_char}? (be specific - e.g., "forward air", "down smash", "grab into down throw")
2. What situation led to getting hit? (e.g., "landed on a shield", "recovered low to ledge", "jumped predictably")
3. How could {player_char} have avoided or escaped this?

Respond in 2-3 sentences max, directly addressing the player. Start with what hit them."""

            else:  # combo
                prompt = f"""Analyze this Super Smash Bros Ultimate frame. The player ({player_char}) is performing a combo on the opponent ({opponent_char}).

Based on what you see:
1. What moves is {player_char} using in this combo? List them if visible.
2. What's a good follow-up or extension from this position?
3. Any tips to optimize this combo for more damage or a kill?

Respond in 2-3 sentences max, directly addressing the player. Be specific about moves."""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a Smash Ultimate coach analyzing gameplay frames. Give specific, actionable advice. Be concise."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame_base64}"}}
                    ]}
                ],
                max_tokens=200
            )
            
            enhanced_message = response.choices[0].message.content.strip()
            
            # Combine original tip with enhanced context
            original_msg = tip.get("message", "")
            tip["message"] = f"{original_msg}\n\n{enhanced_message}"
            tip["enhanced"] = True
            
        except Exception as e:
            # If enhancement fails, keep original tip
            print(f"Vision enhancement failed for tip at {timestamp}s: {e}")
        
        enhanced_tips.append(tip)
    
    cap.release()
    coaching["tips"] = enhanced_tips
    return coaching


async def run_analysis(video_id: str, video_path: str, player_char: str = None, opponent_char: str = None, you_are_p1: bool = True):
    """Run analysis in a thread pool to avoid blocking the event loop."""
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_analysis_sync, video_id, video_path, player_char, opponent_char, you_are_p1)

def update_progress(video_id: str, progress: float):
    if video_id in analyses:
        analyses[video_id]["progress"] = int(progress * 100)


@router.get("/suggestion-at-time/{video_id}")
async def get_suggestion_at_time(video_id: str, time: float = 0):
    """
    Get a contextually-aware AI suggestion by analyzing the actual video frame.
    Uses OpenAI Vision to see what's happening and give specific advice.
    """
    if video_id not in analyses:
        raise HTTPException(404, "Video not found")
    data = analyses[video_id]
    if data["status"] != "complete":
        raise HTTPException(400, "Analysis not complete")
    
    game_states = data.get("game_states") or []
    video_path = data.get("video_path")
    
    # find state closest to requested time
    if game_states:
        best = min(game_states, key=lambda s: abs(s["timestamp"] - time))
        t = best["timestamp"]
        p1 = best.get("p1_percent")
        p2 = best.get("p2_percent")
        s1 = best.get("p1_stocks")
        s2 = best.get("p2_stocks")
    else:
        t = time
        p1 = p2 = s1 = s2 = None
    
    # normalize to "you" vs "opponent"
    you_are_p1 = data.get("you_are_p1", True)
    if you_are_p1:
        your_pct, opp_pct = p1, p2
        your_stocks, opp_stocks = s1, s2
    else:
        your_pct, opp_pct = p2, p1
        your_stocks, opp_stocks = s2, s1
    
    player_char = data.get("player_char") or "unknown"
    opponent_char = data.get("opponent_char") or "unknown"
    
    try:
        from openai import OpenAI
        import os
        import cv2
        import base64
        
        if not os.getenv("OPENAI_API_KEY"):
            return {"suggestion": f"At {int(t)}s: You {your_pct or '?'}%, opponent {opp_pct or '?'}%.", "timestamp": t}
        
        client = OpenAI()
        
        # extract frame from video at this timestamp
        frame_base64 = None
        if video_path and os.path.exists(video_path):
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_num = int(time * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # resize for faster upload (720p max)
                h, w = frame.shape[:2]
                if w > 1280:
                    scale = 1280 / w
                    frame = cv2.resize(frame, (1280, int(h * scale)))
                
                # encode as base64
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # build context with detailed character identification
        # Character visual descriptors for common Smash characters
        char_descriptors = {
            "cloud": "spiky blonde hair, large Buster Sword, dark outfit with one sleeve, blue glow when Limit is charged",
            "wolf": "gray wolf anthropomorphic, purple/dark outfit, has a blaster, pointed ears, walks on two legs",
            "mario": "red cap with M, blue overalls, mustache",
            "link": "green tunic or blue Champion tunic, pointed ears, sword and shield",
            "pikachu": "small yellow mouse, red cheeks, lightning bolt tail",
            "fox": "orange fox anthropomorphic, green outfit, blaster",
            "falco": "blue bird anthropomorphic, red outfit",
            "marth": "blue hair, tiara, blue cape, thin sword",
            "roy": "red hair, red cape, fire sword",
            "joker": "black coat, mask, dark hair",
            "sephiroth": "very long silver hair, black coat, extremely long thin sword",
            "yoshi": "green dinosaur, large nose, red saddle on back, can flutter jump",
            "kirby": "small pink puffball, round, can copy abilities",
            "donkey kong": "large brown gorilla, red tie with DK initials",
            "samus": "orange/red power suit, arm cannon, visor helmet",
            "zelda": "princess with long ears, elegant dress, uses magic",
            "peach": "pink dress, blonde hair, crown, floats",
            "bowser": "large turtle/dragon, spiky shell, red hair, breathes fire",
            "captain falcon": "blue racing suit, helmet with falcon visor, muscular",
            "ness": "boy with red cap, striped shirt, uses PSI/psychic powers",
            "jigglypuff": "round pink pokemon, big eyes, can put opponents to sleep",
            "ice climbers": "two small climbers in parkas, one blue one pink, with hammers",
            "sheik": "ninja in blue bodysuit, wrapped face, throws needles",
            "ganondorf": "large dark-skinned man, red hair, dark armor, powerful punches",
            "mewtwo": "purple/white psychic pokemon, long tail, floats",
            "mr. game & watch": "flat black 2D silhouette character",
            "meta knight": "small blue masked warrior with cape and sword, bat wings",
            "pit": "angel boy with white wings, uses bow that splits into blades",
            "wario": "fat man in yellow/purple, big mustache, motorcycle",
            "snake": "military soldier, bandana, uses explosives and guns",
            "ike": "muscular swordsman, blue hair, huge two-handed sword",
            "lucario": "blue jackal-like pokemon, uses aura powers",
            "rob": "robot with spinning top and gyro, boxy body",
            "lucas": "blonde boy with striped shirt, uses PSI powers",
            "sonic": "blue hedgehog, very fast, spiky hair/quills",
            "diddy kong": "small monkey with red cap and shirt, uses peanut popgun",
            "olimar": "tiny astronaut with pikmin (small colored creatures)",
            "villager": "round-headed villager, can pocket items, uses tools",
            "mega man": "blue robot boy, arm cannon, uses various weapons",
            "wii fit trainer": "fitness instructor in yoga poses, white/gray",
            "rosalina": "tall princess with star companion (Luma)",
            "little mac": "small boxer with green gloves and black tank top",
            "greninja": "blue frog ninja pokemon, uses water attacks",
            "palutena": "goddess with long green hair, staff, uses light",
            "pac-man": "yellow circle character, eats pellets",
            "robin": "tactician with white/black hair, uses magic tomes and sword",
            "shulk": "blonde boy with large red glowing sword (Monado)",
            "bowser jr": "small bowser in clown car/koopa clown",
            "duck hunt": "dog and duck duo, 8-bit style attacks",
            "ryu": "muscular martial artist in white gi, red headband",
            "ken": "blonde martial artist in red gi, flame kicks",
            "corrin": "dragon shapeshifter with chainsaw-sword, can transform limbs",
            "bayonetta": "tall witch in black, guns on hands and feet, long black hair",
            "inkling": "squid kid that shoots ink, can become squid",
            "ridley": "large purple space dragon, very long tail",
            "simon": "vampire hunter with whip, leather armor",
            "richter": "vampire hunter with whip, blue outfit",
            "king k rool": "large crocodile king with crown and belly armor",
            "isabelle": "dog secretary from Animal Crossing, uses fishing rod",
            "incineroar": "wrestling fire cat pokemon, uses wrestling moves",
            "piranha plant": "potted plant with big teeth",
            "hero": "anime swordsman with shield, uses magic spells",
            "banjo": "bear with bird in backpack",
            "terry": "blonde martial artist in red jacket, cap says 'Fatal Fury'",
            "byleth": "teacher with various weapons, green/blue hair",
            "min min": "fighter with extendable ARMS (spring arms)",
            "steve": "blocky minecraft character, uses blocks and tools",
            "kazuya": "martial artist in red gloves, can transform into devil",
            "sora": "boy with spiky brown hair, giant key weapon (Keyblade)",
            "pyra": "red-haired girl with large flaming sword",
            "mythra": "blonde girl with light sword, fast attacks",
        }
        
        player_desc = char_descriptors.get(player_char.lower(), f"the {player_char} character model")
        opp_desc = char_descriptors.get(opponent_char.lower(), f"the {opponent_char} character model")
        
        context = f"""Analyze this Super Smash Bros. Ultimate gameplay frame.

CHARACTER VISUAL IDENTIFICATION:
- {player_char.upper()}: {player_desc}
- {opponent_char.upper()}: {opp_desc}

DAMAGE VALUES (use to help identify characters):
- {player_char}: ~{your_pct or '?'}%
- {opponent_char}: ~{opp_pct or '?'}%

LOOK CAREFULLY at the frame and determine:
1. Who is being HIT or in hitstun (body bent/stretched, hit effects visible)?
2. Who is ATTACKING (arm/weapon extended, attack animation)?
3. Who is GRABBING vs being GRABBED (grabber has arms forward, grabbed character is held)?
4. Who is SHIELDING (bubble around them) vs approaching?

IMPORTANT VISUAL CUES:
- A character being thrown will be held by the opponent or tumbling
- Hitstun = character's body is stretched/bent, often with hit sparks
- Attacking = weapon/limb extended toward opponent
- A character can be grounded while being hit (doesn't mean they're attacking)

Respond with ONLY a coaching tip for {player_char} (2-3 sentences). Do NOT include character identification or analysis steps in your response."""

        if frame_base64:
            # use vision model
            system_msg = f"""You are a Super Smash Bros Ultimate coach giving advice to a {player_char} player.

CRITICAL - Identify characters by their visual appearance:
- {player_char.upper()}: {player_desc}
- {opponent_char.upper()}: {opp_desc}

Before responding, carefully determine:
1. Who is HITTING vs who is BEING HIT (look for hit effects, hitstun poses)
2. Who is GRABBING vs who is BEING GRABBED
3. Who is attacking vs defending

OUTPUT FORMAT: Give ONLY a coaching tip (2-3 sentences). No bullet points, no character identification sections, no step-by-step analysis. Just the advice."""

            r = client.chat.completions.create(
                model="gpt-4o",  # vision-capable model
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": [
                        {"type": "text", "text": context},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame_base64}"}}
                    ]}
                ],
                max_tokens=200
            )
        else:
            # fallback to text-only
            r = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You give Smash Ultimate tips. Be brief."},
                    {"role": "user", "content": f"At {int(t)}s: {player_char} at {your_pct or '?'}% vs {opponent_char} at {opp_pct or '?'}%. Give a general tip."}
                ],
                max_tokens=80
            )
        
        text = (r.choices[0].message.content or "").strip()
        
        # Clean up the response - remove markdown formatting and identification sections
        import re
        
        # Remove double asterisks (bold markdown)
        text = re.sub(r'\*\*', '', text)
        
        # Remove numbered list prefixes like "1. " at start of lines
        text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # Remove bullet points
        text = re.sub(r'^[-•]\s*', '', text, flags=re.MULTILINE)
        
        # Remove "Character Identification:" or similar header lines
        text = re.sub(r'^(Character Identification|Cloud Identification|Wolf Identification|Positions|Actions|Coaching Tip)[:\s]*[-–]?\s*', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove lines that just identify character positions (e.g., "Cloud: Left side, grounded")
        text = re.sub(r'^(Cloud|Wolf|Mario|Link|Fox|Falco|Joker|Sephiroth|Marth|Roy|Pikachu|Yoshi|Kirby|Samus|Zelda|Peach|Bowser|Ness|Jigglypuff|Ganondorf|Mewtwo|Sonic|Snake|Ike|Lucario|Lucas|Villager|Mega Man|Little Mac|Greninja|Palutena|Robin|Shulk|Ryu|Ken|Corrin|Bayonetta|Inkling|Ridley|Simon|Richter|King K Rool|Isabelle|Incineroar|Piranha Plant|Hero|Banjo|Terry|Byleth|Min Min|Steve|Kazuya|Sora|Pyra|Mythra)[:\s]+[^.]*\.\s*', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Clean up multiple newlines
        text = re.sub(r'\n{2,}', ' ', text)
        text = re.sub(r'\n', ' ', text)
        
        # Clean up multiple spaces
        text = re.sub(r'\s{2,}', ' ', text)
        
        text = text.strip()
        
        return {"suggestion": text, "timestamp": t}
    except Exception as e:
        return {"suggestion": f"At {int(t)}s: You {your_pct or '?'}%, opponent {opp_pct or '?'}%.", "error": str(e), "timestamp": t}


@router.post("/save-analysis/{video_id}")
async def save_analysis(video_id: str, name: str = None):
    """Save an analysis for later viewing without re-processing."""
    if video_id not in analyses:
        raise HTTPException(404, "Video not found")
    
    data = analyses[video_id]
    if data.get("status") != "complete":
        raise HTTPException(400, "Analysis not complete")
    
    # Create a saveable version (INCLUDING game_states for instant loading)
    save_data = {
        "video_id": video_id,
        "name": name or f"Analysis {video_id}",
        "video_path": data.get("video_path"),
        "coaching": data.get("coaching"),
        "game_states": data.get("game_states", []),  # Include game_states!
        "player_char": data.get("player_char"),
        "opponent_char": data.get("opponent_char"),
        "you_are_p1": data.get("you_are_p1"),
        "saved_at": __import__('datetime').datetime.now().isoformat(),
        "status": "complete",
    }
    
    # Save to file
    save_path = SAVED_ANALYSES_DIR / f"{video_id}.json"
    with open(save_path, "w") as f:
        json.dump(save_data, f)
    
    return {"success": True, "video_id": video_id}


@router.get("/saved-analyses")
async def list_saved_analyses():
    """List all saved analyses."""
    saved = []
    for f in SAVED_ANALYSES_DIR.glob("*.json"):
        try:
            with open(f) as fp:
                data = json.load(fp)
                saved.append({
                    "video_id": data.get("video_id"),
                    "name": data.get("name"),
                    "player_char": data.get("player_char"),
                    "opponent_char": data.get("opponent_char"),
                    "you_are_p1": data.get("you_are_p1"),
                    "saved_at": data.get("saved_at"),
                })
        except:
            pass
    
    # Sort by saved_at descending
    saved.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
    return {"analyses": saved}


def _load_analysis_sync(video_id: str, you_are_p1_param: str = None):
    """Synchronous load function to run in thread pool."""
    save_path = SAVED_ANALYSES_DIR / f"{video_id}.json"
    if not save_path.exists():
        return None, "Saved analysis not found"
    
    with open(save_path) as f:
        data = json.load(f)
    
    # Use saved game_states if available - DO NOT re-extract (too slow)
    game_states = data.get("game_states", [])
    if game_states:
        print(f"[LoadAnalysis] Using cached game_states ({len(game_states)} states)")
    else:
        print(f"[LoadAnalysis] No game_states cached - suggestion-at-time may be limited")
    
    # Check if perspective needs to change
    original_p1 = data.get("you_are_p1", True)
    if you_are_p1_param is not None:
        new_p1 = you_are_p1_param.lower() not in ("false", "0", "no")
        
        # If perspective changed, need to regenerate coaching
        if new_p1 != original_p1 and game_states:
            # Swap characters for new perspective
            if new_p1:
                player = data.get("player_char")
                opponent = data.get("opponent_char")
            else:
                player = data.get("opponent_char")
                opponent = data.get("player_char")
            
            coaching = generate_coaching(game_states, player_char=player, opponent_char=opponent, you_are_p1=new_p1)
            data["coaching"] = coaching
            data["you_are_p1"] = new_p1
            data["player_char"] = player
            data["opponent_char"] = opponent
        elif new_p1 != original_p1 and not game_states:
            # Can't switch perspective without game_states - return error
            return None, "Cannot switch perspective for legacy saves without re-processing. Please re-analyze the video."
    
    return data, None


@router.get("/load-analysis/{video_id}")
async def load_saved_analysis(video_id: str, you_are_p1: str = None):
    """
    Load a saved analysis. Optionally switch perspective with you_are_p1.
    If you_are_p1 is different from original, re-generate coaching from other perspective.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    data, error = await loop.run_in_executor(None, _load_analysis_sync, video_id, you_are_p1)
    
    if error:
        raise HTTPException(404, error)
    
    # Store in memory for frame extraction and suggestions
    analyses[video_id] = data
    
    return data


@router.delete("/saved-analysis/{video_id}")
async def delete_saved_analysis(video_id: str):
    """Delete a saved analysis."""
    save_path = SAVED_ANALYSES_DIR / f"{video_id}.json"
    if save_path.exists():
        save_path.unlink()
    if video_id in analyses:
        del analyses[video_id]
    return {"success": True}


@router.get("/video/{video_id}")
async def get_video(video_id: str):
    """Serve a video file for playback."""
    # Check if video exists in analyses
    if video_id in analyses:
        video_path = analyses[video_id].get("video_path")
        if video_path and os.path.exists(video_path):
            return FileResponse(
                video_path,
                media_type="video/mp4",
                filename=os.path.basename(video_path)
            )
    
    # Check saved analyses
    save_path = SAVED_ANALYSES_DIR / f"{video_id}.json"
    if save_path.exists():
        with open(save_path) as f:
            data = json.load(f)
            video_path = data.get("video_path")
            if video_path and os.path.exists(video_path):
                return FileResponse(
                    video_path,
                    media_type="video/mp4",
                    filename=os.path.basename(video_path)
                )
    
    raise HTTPException(404, "Video not found")

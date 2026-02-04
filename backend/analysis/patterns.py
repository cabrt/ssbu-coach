def find_patterns(game_states: list) -> dict:
    """
    Detect interesting patterns in game state timeline.
    """
    patterns = {
        "damage_spikes": [],      # damage YOU took
        "damage_dealt": [],       # damage YOU dealt
        "stock_losses": [],
        "kills": [],              # opponent stock losses = your kills
        "long_neutral": [],
        "comebacks": [],
        "combos": [],
        "game_start": None,
        "game_end": None,
    }
    
    if len(game_states) < 2:
        return patterns
    
    # Helper function to find max percent in a lookback window from RAW data
    def get_raw_max_before(player: str, end_idx: int, lookback_frames: int = 60) -> float:
        """Find the max percent for a player in the raw data before the given index."""
        max_pct = 0
        start_idx = max(0, end_idx - lookback_frames)
        pct_key = f"{player}_percent"
        
        for j in range(start_idx, end_idx):
            if j < len(game_states):
                pct = game_states[j].get(pct_key)
                if pct is not None and pct > max_pct:
                    max_pct = pct
        return max_pct
    
    # Build index mapping from timestamp to raw data index
    timestamp_to_raw_idx = {state["timestamp"]: i for i, state in enumerate(game_states)}
    
    # first, smooth out the game states to reduce noise
    smoothed_states = smooth_game_states(game_states)
    
    # find when the game actually starts
    # game starts when BOTH players are at 0% with 3 stocks for 3+ consecutive frames
    # this skips character select, loading screens, and the "GO!" animation
    game_started = False
    game_start_time = 0
    consecutive_start_frames = 0
    
    for i, state in enumerate(smoothed_states):
        p1_percent = state.get("p1_percent") or 0
        p2_percent = state.get("p2_percent") or 0
        p1_stocks = state.get("p1_stocks")
        p2_stocks = state.get("p2_stocks")
        
        # game starts when BOTH players at 0% with 3 stocks
        if (p1_percent <= 5 and p2_percent <= 5 and 
            p1_stocks == 3 and p2_stocks == 3):
            consecutive_start_frames += 1
            if consecutive_start_frames >= 3:  # need 3 consecutive frames
                game_started = True
                # go back to first frame of this sequence
                game_start_time = smoothed_states[i - 2]["timestamp"]
                patterns["game_start"] = game_start_time
                break
        else:
            consecutive_start_frames = 0
    
    # fallback: if we never found clean start, look for first gameplay-like state
    # (at least one player with readable percent, after initial noise)
    if not game_started:
        for i, state in enumerate(smoothed_states):
            # skip first 5 seconds minimum (character select / loading)
            if state["timestamp"] < 5:
                continue
            p1_percent = state.get("p1_percent")
            p2_percent = state.get("p2_percent")
            p1_stocks = state.get("p1_stocks")
            p2_stocks = state.get("p2_stocks")
            # need at least some valid data
            if (p1_percent is not None or p2_percent is not None) and \
               (p1_stocks is not None or p2_stocks is not None):
                game_start_time = state["timestamp"]
                patterns["game_start"] = game_start_time
                break
    
    # track both players' damage over time
    prev_p1_percent = 0
    prev_p2_percent = 0
    confirmed_p1_stocks = 3
    confirmed_p2_stocks = 3
    game_over = False  # Set to True AFTER recording final death/kill
    neutral_start = None
    combo_start = None
    combo_damage = 0
    combo_hits = 0
    combo_from_percent = 0
    
    # track recent high percents for stock loss validation
    p1_max_recent_percent = 0
    p2_max_recent_percent = 0
    
    # track GLOBAL max percents (not reset on death) for accurate stats
    global_p1_max = 0
    global_p2_max = 0
    
    for i, state in enumerate(smoothed_states):
        # skip states before game started
        if state["timestamp"] < game_start_time:
            continue
            
        # use last known good value if current is None (handles OCR dropouts)
        p1_percent = state.get("p1_percent")
        p2_percent = state.get("p2_percent")
        
        if p1_percent is None:
            p1_percent = prev_p1_percent  # use last known
        if p2_percent is None:
            p2_percent = prev_p2_percent  # use last known
            
        p1_stocks = state.get("p1_stocks")
        p2_stocks = state.get("p2_stocks")
        timestamp = state["timestamp"]
        
        # track maximum percent reached (for validating stock losses)
        p1_max_recent_percent = max(p1_max_recent_percent, p1_percent)
        p2_max_recent_percent = max(p2_max_recent_percent, p2_percent)
        
        # track GLOBAL max (never resets, for accurate stats)
        global_p1_max = max(global_p1_max, p1_percent)
        global_p2_max = max(global_p2_max, p2_percent)
        
        # damage taken by p1 (you)
        p1_damage_taken = max(0, p1_percent - prev_p1_percent)
        # damage dealt to p2 (opponent)
        p2_damage_taken = max(0, p2_percent - prev_p2_percent)
        
        # detect damage spikes (you took significant damage QUICKLY)
        # "Quick" = 20%+ damage in a short time window without dealing damage back
        # Check recent history to see if this is truly rapid damage
        if (p1_damage_taken >= 20 and p1_damage_taken <= 80 and
            p1_percent > prev_p1_percent and
            p1_percent <= 180 and prev_p1_percent <= 180):
            # avoid spike at match start from OCR noise (0 -> big number)
            if not (prev_p1_percent == 0 and p1_percent > 60):
                # PERSISTENCE CHECK: new percent must hold for at least 1 more frame
                spike_confirmed = verify_damage_spike(smoothed_states, i, "p1", p1_percent)
                # QUICK CHECK: verify this is actually rapid damage, not gradual
                is_quick = verify_quick_damage(smoothed_states, i, "p1", prev_p1_percent, p1_percent)
                if spike_confirmed and is_quick:
                    patterns["damage_spikes"].append({
                        "timestamp": timestamp,
                        "damage": p1_damage_taken,
                        "from_percent": prev_p1_percent,
                        "to_percent": p1_percent
                    })
        
        # detect damage dealt spikes (you dealt significant damage)
        # Lower threshold to 15% to catch more events, cap at 80% to avoid OCR errors
        if (p2_damage_taken >= 15 and p2_damage_taken <= 80 and
            p2_percent > prev_p2_percent and
            p2_percent <= 200 and prev_p2_percent <= 200):
            if not (prev_p2_percent == 0 and p2_percent > 60):
                spike_confirmed = verify_damage_spike(smoothed_states, i, "p2", p2_percent)
                if spike_confirmed:
                    patterns["damage_dealt"].append({
                        "timestamp": timestamp,
                        "damage": p2_damage_taken,
                        "from_percent": prev_p2_percent,
                        "to_percent": p2_percent
                    })
        
        # detect combos (you dealt good damage in rapid succession)
        # A TRUE COMBO requires:
        # 1. 3+ hits (damage instances) in rapid succession
        # 2. No getting hit back in between (p1 damage stays same)
        # 3. Hits within ~5 seconds total
        capped_p2_damage = min(p2_damage_taken, 60) if p2_damage_taken > 0 else 0
        you_got_hit = p1_damage_taken > 5  # You took damage this frame
        
        if capped_p2_damage > 8:  # You dealt damage
            if you_got_hit:
                # You got hit while dealing damage - not a true combo, reset
                if combo_start and combo_hits >= 3 and combo_damage > 25:
                    patterns["combos"].append({
                        "start": combo_start,
                        "end": prev_timestamp if 'prev_timestamp' in dir() else timestamp,
                        "damage": min(combo_damage, 100),
                        "from_percent": combo_from_percent,
                        "to_percent": min(combo_from_percent + combo_damage, 200),
                        "hits": combo_hits
                    })
                combo_start = None
                combo_damage = 0
                combo_hits = 0
                combo_from_percent = 0
            else:
                # Continue or start combo
                if combo_start is None:
                    combo_start = timestamp
                    combo_from_percent = prev_p2_percent
                    combo_damage = capped_p2_damage
                    combo_hits = 1
                else:
                    # Check if too much time passed (>5 seconds = not a combo)
                    if timestamp - combo_start > 5:
                        # Save old combo if valid, start new one
                        if combo_hits >= 3 and combo_damage > 25:
                            patterns["combos"].append({
                                "start": combo_start,
                                "end": prev_timestamp if 'prev_timestamp' in dir() else timestamp,
                                "damage": min(combo_damage, 100),
                                "from_percent": combo_from_percent,
                                "to_percent": min(combo_from_percent + combo_damage, 200),
                                "hits": combo_hits
                            })
                        combo_start = timestamp
                        combo_from_percent = prev_p2_percent
                        combo_damage = capped_p2_damage
                        combo_hits = 1
                    else:
                        combo_damage += capped_p2_damage
                        combo_hits += 1
        elif you_got_hit:
            # You got hit without dealing damage - combo broken
            if combo_start and combo_hits >= 3 and combo_damage > 25:
                patterns["combos"].append({
                    "start": combo_start,
                    "end": prev_timestamp if 'prev_timestamp' in dir() else timestamp,
                    "damage": min(combo_damage, 100),
                    "from_percent": combo_from_percent,
                    "to_percent": min(combo_from_percent + combo_damage, 200),
                    "hits": combo_hits
                })
            combo_start = None
            combo_damage = 0
            combo_hits = 0
            combo_from_percent = 0
        else:
            # No damage either way - check if combo timed out
            if combo_start and timestamp - combo_start > 3:
                # Combo ended due to inactivity
                if combo_hits >= 3 and combo_damage > 25:
                    patterns["combos"].append({
                        "start": combo_start,
                        "end": prev_timestamp if 'prev_timestamp' in dir() else timestamp,
                        "damage": min(combo_damage, 100),
                        "from_percent": combo_from_percent,
                        "to_percent": min(combo_from_percent + combo_damage, 200),
                        "hits": combo_hits
                    })
                combo_start = None
                combo_damage = 0
                combo_hits = 0
                combo_from_percent = 0
        
        prev_timestamp = timestamp
        
        # GAME OVER CHECK: Skip if game already ended on a PREVIOUS frame
        # (game_over flag is set AFTER recording the final death, so the final event is captured)
        if game_over:
            continue
        
        # detect your stock losses - try stock count first, then percent-reset fallback
        stock_loss_detected = detect_stock_loss(
            smoothed_states, i, "p1", confirmed_p1_stocks, 
            p1_max_recent_percent, game_start_time
        )
        
        # Fallback: detect death by percent resetting to near 0 after being high
        percent_reset_death = detect_death_by_percent_reset(
            smoothed_states, i, "p1", p1_max_recent_percent, prev_p1_percent, p1_percent
        )
        
        if stock_loss_detected:
            # Use RAW max percent from lookback window (not smoothed) for accurate death percent
            raw_idx = timestamp_to_raw_idx.get(timestamp, i)
            raw_p1_max = get_raw_max_before("p1", raw_idx)
            actual_percent = raw_p1_max if raw_p1_max > 0 else p1_max_recent_percent
            patterns["stock_losses"].append({
                "timestamp": timestamp,
                "percent": actual_percent,
                "stocks_remaining": stock_loss_detected["new_stocks"]
            })
            confirmed_p1_stocks = stock_loss_detected["new_stocks"]
            p1_max_recent_percent = 0
            prev_p1_percent = 0
            # Mark game as over AFTER recording the final death
            if confirmed_p1_stocks == 0:
                game_over = True
        elif percent_reset_death:
            # Use fallback detection with raw max lookback
            confirmed_p1_stocks = max(0, confirmed_p1_stocks - 1)
            raw_idx = timestamp_to_raw_idx.get(timestamp, i)
            raw_p1_max = get_raw_max_before("p1", raw_idx)
            actual_percent = raw_p1_max if raw_p1_max > 0 else percent_reset_death["death_percent"]
            patterns["stock_losses"].append({
                "timestamp": timestamp,
                "percent": actual_percent,
                "stocks_remaining": confirmed_p1_stocks
            })
            p1_max_recent_percent = 0
            prev_p1_percent = 0
            # Mark game as over AFTER recording the final death
            if confirmed_p1_stocks == 0:
                game_over = True
        
        # detect opponent stock losses (your kills) 
        opp_stock_loss = detect_stock_loss(
            smoothed_states, i, "p2", confirmed_p2_stocks,
            p2_max_recent_percent, game_start_time
        )
        
        # Fallback for opponent deaths too
        opp_percent_reset = detect_death_by_percent_reset(
            smoothed_states, i, "p2", p2_max_recent_percent, prev_p2_percent, p2_percent
        )
        
        if opp_stock_loss:
            # Use RAW max percent from lookback window (not smoothed) for accurate kill percent
            raw_idx = timestamp_to_raw_idx.get(timestamp, i)
            raw_p2_max = get_raw_max_before("p2", raw_idx)
            actual_percent = raw_p2_max if raw_p2_max > 0 else p2_max_recent_percent
            patterns["kills"].append({
                "timestamp": timestamp,
                "opponent_percent": actual_percent,
                "opponent_stocks_remaining": opp_stock_loss["new_stocks"]
            })
            confirmed_p2_stocks = opp_stock_loss["new_stocks"]
            p2_max_recent_percent = 0
            prev_p2_percent = 0
            # Mark game as over AFTER recording the final kill
            if confirmed_p2_stocks == 0:
                game_over = True
        elif opp_percent_reset:
            confirmed_p2_stocks = max(0, confirmed_p2_stocks - 1)
            raw_idx = timestamp_to_raw_idx.get(timestamp, i)
            raw_p2_max = get_raw_max_before("p2", raw_idx)
            actual_percent = raw_p2_max if raw_p2_max > 0 else opp_percent_reset["death_percent"]
            patterns["kills"].append({
                "timestamp": timestamp,
                "opponent_percent": actual_percent,
                "opponent_stocks_remaining": confirmed_p2_stocks
            })
            p2_max_recent_percent = 0
            prev_p2_percent = 0
            # Mark game as over AFTER recording the final kill
            if confirmed_p2_stocks == 0:
                game_over = True
        
        # detect game end (someone has 0 stocks)
        if game_over:
            patterns["game_end"] = timestamp
        
        # SKIP fallback detection if game is already over
        if game_over:
            pass  # Skip fallback detection - game already ended
        else:
            # detect YOUR final death: when your percent goes to None while at high percent
            # This catches the game-ending death even if stock detection fails
            if (prev_p1_percent is not None and prev_p1_percent >= 60 and 
                state.get("p1_percent") is None):
                # Check if this is near the end of the video (within last 20% of frames)
                if i >= len(smoothed_states) * 0.8:
                    # This is likely the final death
                    if not patterns.get("stock_losses") or all(l["timestamp"] < timestamp - 5 for l in patterns["stock_losses"]):
                        patterns["stock_losses"].append({
                            "timestamp": timestamp,
                            "percent": prev_p1_percent,
                            "stocks_remaining": 0,  # final death
                            "is_game_ender": True
                        })
                        patterns["game_end"] = timestamp
                        game_over = True
            
            # detect OPPONENT final KO: when opponent percent goes to None while at high percent
            # This catches the game-ending kill even if stock detection fails  
            # BUT only if game hasn't ended from P1 death
            if not game_over:
                if (prev_p2_percent is not None and prev_p2_percent >= 60 and 
                    state.get("p2_percent") is None):
                    # Check if this is near the end of the video (within last 20% of frames)
                    if i >= len(smoothed_states) * 0.8:
                        # This is likely the final KO
                        if not patterns.get("kills") or all(k["timestamp"] < timestamp - 5 for k in patterns["kills"]):
                            patterns["kills"].append({
                                "timestamp": timestamp,
                                "opponent_percent": prev_p2_percent,
                                "opponent_stocks_remaining": 0,  # final KO
                                "is_game_winner": True
                            })
                            patterns["game_end"] = timestamp
                            game_over = True
        
        # detect long neutral (no significant damage for a while)
        total_damage = p1_damage_taken + p2_damage_taken
        
        if total_damage < 5:
            if neutral_start is None:
                neutral_start = timestamp
        else:
            if neutral_start and (timestamp - neutral_start) > 8:
                patterns["long_neutral"].append({
                    "start": neutral_start,
                    "end": timestamp,
                    "duration": timestamp - neutral_start
                })
            neutral_start = None
        
        prev_p1_percent = p1_percent
        prev_p2_percent = p2_percent
    
    # Deduplicate stock events - only keep one per actual stock loss
    # Stock events within 5 seconds of each other are the same event
    patterns["stock_losses"] = _deduplicate_events(patterns["stock_losses"], time_window=5.0)
    patterns["kills"] = _deduplicate_events(patterns["kills"], time_window=5.0)
    
    # Track global max percents (not affected by resets after deaths)
    patterns["p1_true_max_percent"] = global_p1_max
    patterns["p2_true_max_percent"] = global_p2_max
    
    return patterns


def _deduplicate_events(events: list, time_window: float = 5.0) -> list:
    """Remove duplicate events within a time window, keeping the first one."""
    if not events:
        return events
    
    # Sort by timestamp
    sorted_events = sorted(events, key=lambda x: x.get("timestamp", 0))
    
    deduplicated = []
    last_timestamp = -999
    
    for event in sorted_events:
        ts = event.get("timestamp", 0)
        # If this event is more than time_window after the last one, keep it
        if ts - last_timestamp > time_window:
            deduplicated.append(event)
            last_timestamp = ts
    
    return deduplicated


def smooth_game_states(game_states: list) -> list:
    """
    Apply temporal smoothing to reduce OCR noise in game states.
    Uses median filtering for percent values and mode for stock counts.
    """
    if len(game_states) < 3:
        return game_states
    
    smoothed = []
    window_size = 5  # larger window for more aggressive smoothing
    
    for i, state in enumerate(game_states):
        smoothed_state = state.copy()
        
        # get window of states around this one
        start_idx = max(0, i - window_size // 2)
        end_idx = min(len(game_states), i + window_size // 2 + 1)
        window = game_states[start_idx:end_idx]
        
        # smooth percent values using median
        p1_percents = [s.get("p1_percent") for s in window if s.get("p1_percent") is not None]
        p2_percents = [s.get("p2_percent") for s in window if s.get("p2_percent") is not None]
        
        if p1_percents:
            smoothed_state["p1_percent"] = int(sorted(p1_percents)[len(p1_percents) // 2])
        if p2_percents:
            smoothed_state["p2_percent"] = int(sorted(p2_percents)[len(p2_percents) // 2])
        
        # smooth stock counts using mode (most common value in window)
        p1_stocks = [s.get("p1_stocks") for s in window if s.get("p1_stocks") is not None]
        p2_stocks = [s.get("p2_stocks") for s in window if s.get("p2_stocks") is not None]
        
        if p1_stocks:
            smoothed_state["p1_stocks"] = max(set(p1_stocks), key=p1_stocks.count)
        if p2_stocks:
            smoothed_state["p2_stocks"] = max(set(p2_stocks), key=p2_stocks.count)
        
        smoothed.append(smoothed_state)
    
    return smoothed


def detect_death_by_percent_reset(game_states: list, current_idx: int, player: str,
                                   max_recent_percent: float, prev_percent: float, 
                                   current_percent: float) -> dict:
    """
    Detect death by observing percent dropping from high value to near 0.
    This is a fallback when stock counting is unreliable.
    
    Death indicators:
    1. Max recent percent was >= 60%
    2. Percent suddenly drops to <= 15%
    3. The low percent persists for at least 2 frames
    """
    if current_idx < 2 or current_idx >= len(game_states) - 2:
        return None
    
    # Need high percent before (at least 60%)
    if max_recent_percent < 60:
        return None
    
    # Current percent must be low (respawn = 0%)
    if current_percent is None or current_percent > 15:
        return None
    
    # Previous percent must have been reasonably high (not another recent death)
    if prev_percent is not None and prev_percent < 30:
        return None
    
    # Check that low percent persists (not just OCR noise)
    percent_key = f"{player}_percent"
    persist_count = 0
    for j in range(1, min(3, len(game_states) - current_idx)):
        future_state = game_states[current_idx + j]
        future_pct = future_state.get(percent_key)
        if future_pct is not None and future_pct <= 20:
            persist_count += 1
    
    if persist_count < 1:
        return None
    
    return {"death_percent": max_recent_percent}


def verify_quick_damage(game_states: list, current_idx: int, player: str, 
                        from_percent: float, to_percent: float) -> bool:
    """
    Verify that damage was taken QUICKLY - within a short time window.
    
    "Quick damage" means:
    1. The damage happened within ~5 seconds
    2. You didn't deal significant damage back during that window
    
    This prevents flagging gradual damage exchanges as "quick damage".
    """
    if current_idx < 1:
        return True  # Can't verify, assume quick
    
    damage_taken = to_percent - from_percent
    if damage_taken < 20:
        return False  # Not significant enough
    
    # Look back to find when damage started accumulating
    percent_key = f"{player}_percent"
    opponent_key = "p2_percent" if player == "p1" else "p1_percent"
    
    # Find the frame where percent was at from_percent
    start_idx = current_idx
    for j in range(1, min(15, current_idx)):  # Look back up to 15 frames (~15 seconds at 1fps)
        prev_state = game_states[current_idx - j]
        prev_pct = prev_state.get(percent_key)
        if prev_pct is not None and prev_pct <= from_percent + 5:
            start_idx = current_idx - j
            break
    
    # Calculate time window
    start_time = game_states[start_idx]["timestamp"]
    end_time = game_states[current_idx]["timestamp"]
    time_window = end_time - start_time
    
    # If damage took more than 5 seconds, it's not "quick"
    if time_window > 5:
        return False
    
    # Check if you dealt significant damage back during this window
    # If you did, this is an exchange, not getting comboed
    damage_dealt_back = 0
    for j in range(start_idx, current_idx + 1):
        if j > 0:
            curr_opp = game_states[j].get(opponent_key) or 0
            prev_opp = game_states[j - 1].get(opponent_key) or 0
            delta = max(0, curr_opp - prev_opp)
            if delta < 60:  # Cap to avoid OCR errors
                damage_dealt_back += delta
    
    # If you dealt back more than 30% of what you took, it's an exchange, not one-sided
    if damage_dealt_back > damage_taken * 0.3:
        return False
    
    return True


def verify_damage_spike(game_states: list, current_idx: int, player: str, expected_percent: int) -> bool:
    """
    Verify a damage spike is real by checking the new percent persists for at least 1 frame.
    This filters out single-frame OCR errors (e.g., 30 -> 65 -> 30 due to misread).
    """
    percent_key = f"{player}_percent"
    
    # check next 2 frames - the elevated percent should persist for at least 1
    frames_to_check = min(2, len(game_states) - current_idx - 1)
    if frames_to_check < 1:
        return False
    
    persisting_count = 0
    tolerance = 20  # allow some variation
    
    for j in range(1, frames_to_check + 1):
        future_state = game_states[current_idx + j]
        future_percent = future_state.get(percent_key)
        if future_percent is not None:
            # percent should stay near the elevated level (within tolerance)
            # OR continue increasing (took more damage)
            if future_percent >= expected_percent - tolerance:
                persisting_count += 1
    
    # only need 1 frame of persistence now (less strict)
    return persisting_count >= 1


def detect_stock_loss(game_states: list, current_idx: int, player: str, 
                      confirmed_stocks: int, max_recent_percent: int,
                      game_start_time: float) -> dict:
    """
    Detect if a stock loss actually occurred with multiple validation checks.
    Returns dict with new_stocks if confirmed, None otherwise.
    
    Validation criteria:
    1. Stock count decreased from confirmed value
    2. Player had meaningful percent before (>= 50%)
    3. Stock decrease persists for 4+ frames
    4. Percent MUST reset to <15% after the loss
    5. Stock was higher for 2+ frames before this point
    """
    if current_idx < 3 or current_idx >= len(game_states) - 4:
        return None
    
    state = game_states[current_idx]
    timestamp = state["timestamp"]
    
    stocks_key = f"{player}_stocks"
    percent_key = f"{player}_percent"
    
    current_stocks = state.get(stocks_key)
    current_percent = state.get(percent_key) or 0
    
    if current_stocks is None:
        return None
    
    # check if stocks decreased from our confirmed count
    if current_stocks >= confirmed_stocks:
        return None
    
    # validation 1: require meaningful percent before death (at least 50%)
    time_into_game = timestamp - game_start_time
    min_percent_required = 50 if time_into_game > 20 else 35
    if max_recent_percent < min_percent_required:
        return None
    # reject impossible death percent (OCR errors like 188%)
    if max_recent_percent > 180:
        return None
    
    # validation 2: check that stock was HIGHER for 2+ frames BEFORE this point
    prev_higher_count = 0
    for j in range(1, min(3, current_idx + 1)):
        prev_state = game_states[current_idx - j]
        prev_stocks = prev_state.get(stocks_key)
        if prev_stocks is not None and prev_stocks >= confirmed_stocks:
            prev_higher_count += 1
    if prev_higher_count < 2:
        return None
    
    # validation 3: check that the stock loss persists for 4+ frames AFTER
    frames_to_check = min(5, len(game_states) - current_idx - 1)
    persisting_low_stock = 0
    
    for j in range(1, frames_to_check + 1):
        future_state = game_states[current_idx + j]
        future_stocks = future_state.get(stocks_key)
        if future_stocks is not None and future_stocks <= current_stocks:
            persisting_low_stock += 1
    
    # require at least 4 frames confirming lower stock count
    if persisting_low_stock < 4:
        return None
    
    # validation 4: percent MUST reset to <15% within the next few frames
    percent_reset_confirmed = False
    for j in range(1, min(5, len(game_states) - current_idx)):
        future_state = game_states[current_idx + j]
        future_percent = future_state.get(percent_key)
        if future_percent is not None and future_percent < 15:
            percent_reset_confirmed = True
            break
    
    # if percent never reset to low, this is NOT a real stock loss
    if not percent_reset_confirmed:
        return None
    
    # all validations passed - this is a real stock loss
    return {
        "new_stocks": current_stocks,
        "death_percent": max_recent_percent
    }

def detect_combos(game_states: list) -> list:
    """
    Detect potential combo sequences based on rapid damage accumulation.
    This is a simplified version - real combo detection would need frame data.
    """
    combos = []
    combo_start = None
    combo_damage = 0
    
    for i, state in enumerate(game_states):
        if i == 0:
            continue
        
        prev = game_states[i-1]
        p2_percent = state.get("p2_percent") or 0
        prev_p2 = prev.get("p2_percent") or 0
        
        damage = p2_percent - prev_p2
        time_diff = state["timestamp"] - prev["timestamp"]
        
        # if we dealt damage quickly, might be a combo
        if damage > 0 and time_diff < 2:
            if combo_start is None:
                combo_start = prev["timestamp"]
                combo_damage = 0
            combo_damage += damage
        else:
            # combo ended
            if combo_start and combo_damage > 20:
                combos.append({
                    "start": combo_start,
                    "end": prev["timestamp"],
                    "damage": combo_damage
                })
            combo_start = None
            combo_damage = 0
    
    return combos

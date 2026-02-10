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
        "edgeguards": [],         # successful offstage plays (you edgeguarding opponent)
        "got_edgeguarded": [],    # when opponent edgeguarded you
        "recovery_moments": [],   # when you recovered after being hit offstage
        "momentum_swings": [],    # significant shifts in match momentum
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
    neutral_start_p1 = 0
    neutral_start_p2 = 0
    combo_start = None
    combo_damage = 0
    combo_hits = 0
    combo_from_percent = 0
    combo_end_percent = 0
    
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
        # CRITICAL: Use RAW data for max percent tracking, not smoothed
        # Smoothing can reduce brief spikes before death (e.g. 68% -> 38% median)
        # which causes deaths to fail validation
        raw_idx = timestamp_to_raw_idx.get(timestamp, i)
        if raw_idx < len(game_states):
            raw_p1_pct = game_states[raw_idx].get("p1_percent") or 0
            raw_p2_pct = game_states[raw_idx].get("p2_percent") or 0
            p1_max_recent_percent = max(p1_max_recent_percent, raw_p1_pct, p1_percent)
            p2_max_recent_percent = max(p2_max_recent_percent, raw_p2_pct, p2_percent)
        else:
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
                    # Use ACTUAL p2_percent, not calculated value
                    actual_to_percent = prev_p2_percent if prev_p2_percent else combo_from_percent + combo_damage
                    patterns["combos"].append({
                        "start": combo_start,
                        "end": prev_timestamp if 'prev_timestamp' in dir() else timestamp,
                        "damage": min(combo_damage, 100),
                        "from_percent": combo_from_percent,
                        "to_percent": actual_to_percent,
                        "hits": combo_hits
                    })
                combo_start = None
                combo_damage = 0
                combo_hits = 0
                combo_from_percent = 0
                combo_end_percent = 0
            else:
                # Continue or start combo
                if combo_start is None:
                    combo_start = timestamp
                    combo_from_percent = prev_p2_percent if prev_p2_percent else 0
                    combo_damage = capped_p2_damage
                    combo_hits = 1
                    combo_end_percent = p2_percent if p2_percent else combo_from_percent + capped_p2_damage
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
                                "to_percent": combo_end_percent,
                                "hits": combo_hits
                            })
                        combo_start = timestamp
                        combo_from_percent = prev_p2_percent if prev_p2_percent else 0
                        combo_damage = capped_p2_damage
                        combo_hits = 1
                        combo_end_percent = p2_percent if p2_percent else combo_from_percent + capped_p2_damage
                    else:
                        combo_damage += capped_p2_damage
                        combo_hits += 1
                        combo_end_percent = p2_percent if p2_percent else combo_end_percent + capped_p2_damage
        elif you_got_hit:
            # You got hit without dealing damage - combo broken
            if combo_start and combo_hits >= 3 and combo_damage > 25:
                patterns["combos"].append({
                    "start": combo_start,
                    "end": prev_timestamp if 'prev_timestamp' in dir() else timestamp,
                    "damage": min(combo_damage, 100),
                    "from_percent": combo_from_percent,
                    "to_percent": combo_end_percent if 'combo_end_percent' in dir() and combo_end_percent else prev_p2_percent,
                    "hits": combo_hits
                })
            combo_start = None
            combo_damage = 0
            combo_hits = 0
            combo_from_percent = 0
            combo_end_percent = 0
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
                        "to_percent": combo_end_percent if 'combo_end_percent' in dir() and combo_end_percent else prev_p2_percent,
                        "hits": combo_hits
                    })
                combo_start = None
                combo_damage = 0
                combo_hits = 0
                combo_from_percent = 0
                combo_end_percent = 0
        
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
                # Near end of video (last 25% of frames) - do not require frames after death
                if i >= len(smoothed_states) * 0.75:
                    # Add final death if no stock_loss within 2s of this timestamp
                    recent = [l for l in patterns.get("stock_losses", []) if l["timestamp"] >= timestamp - 2]
                    if not recent:
                        patterns["stock_losses"].append({
                            "timestamp": timestamp,
                            "percent": prev_p1_percent,
                            "stocks_remaining": 0,
                            "is_game_ender": True
                        })
                        patterns["game_end"] = timestamp
                        game_over = True
            
            # detect OPPONENT final KO: when opponent percent goes to None while at high percent
            if not game_over:
                if (prev_p2_percent is not None and prev_p2_percent >= 60 and 
                    state.get("p2_percent") is None):
                    if i >= len(smoothed_states) * 0.75:
                        recent = [k for k in patterns.get("kills", []) if k["timestamp"] >= timestamp - 2]
                        if not recent:
                            patterns["kills"].append({
                                "timestamp": timestamp,
                                "opponent_percent": prev_p2_percent,
                                "opponent_stocks_remaining": 0,
                                "is_game_winner": True
                            })
                            patterns["game_end"] = timestamp
                            game_over = True
        
        # EDGEGUARD DETECTION: Identify likely offstage kills vs center-stage kills
        # True edgeguards have specific characteristics we can infer without position data:
        # 1. Kill percent typically 50-140% (edgeguards kill earlier than center-stage)
        # 2. You didn't deal much damage RIGHT before the kill (not a combo finisher)
        # 3. Opponent's percent was relatively stable before the kill (they were recovering)
        if opp_stock_loss or opp_percent_reset:
            kill_percent = opp_stock_loss.get("death_percent") if opp_stock_loss else opp_percent_reset.get("death_percent", 0)
            if kill_percent is None:
                kill_percent = 0
            
            # Check damage you took recently (within 3 seconds) - trade detection
            your_damage_during_kill = 0
            lookback_start = max(0, i - 10)  # ~3 seconds at 3fps
            for j in range(lookback_start, i):
                if j > 0:
                    prev_your_pct = smoothed_states[j-1].get("p1_percent") or 0
                    curr_your_pct = smoothed_states[j].get("p1_percent") or 0
                    your_damage_during_kill += max(0, curr_your_pct - prev_your_pct)
            
            # Check damage you DEALT in the last 5 seconds - combo detection
            damage_dealt_before_kill = 0
            combo_lookback = max(0, i - 15)  # ~5 seconds at 3fps
            for j in range(combo_lookback, i):
                if j > 0:
                    prev_opp_pct = smoothed_states[j-1].get("p2_percent") or 0
                    curr_opp_pct = smoothed_states[j].get("p2_percent") or 0
                    damage_dealt_before_kill += max(0, curr_opp_pct - prev_opp_pct)
            
            # Edgeguard heuristics:
            # - Kill percent 50-145%: Edgeguards typically kill early due to offstage positioning
            #   Kills at 150%+ are usually center-stage finishers after opponent lived long
            # - Low damage dealt before: If you dealt 30%+ damage in combo, it's a combo finisher
            # - Low damage taken: Taking some damage is OK (small trades happen in edgeguards)
            is_edgeguard_percent = 50 <= kill_percent <= 145
            is_not_combo_kill = damage_dealt_before_kill < 30
            is_clean_kill = your_damage_during_kill <= 15  # Allow up to 15% (small trade)
            
            # Score-based detection: more criteria met = higher confidence
            edgeguard_score = 0
            if is_edgeguard_percent:
                edgeguard_score += 1
            if is_not_combo_kill:
                edgeguard_score += 1
            if is_clean_kill:
                edgeguard_score += 1
            if your_damage_during_kill < 5:  # Very clean = bonus
                edgeguard_score += 1
            
            # Require at least 3 criteria to call it an edgeguard
            if edgeguard_score >= 3:
                patterns["edgeguards"].append({
                    "timestamp": timestamp,
                    "opponent_percent": kill_percent,
                    "your_damage_taken": your_damage_during_kill,
                    "damage_dealt_before": damage_dealt_before_kill,
                    "is_likely_edgeguard": edgeguard_score >= 4,
                    "confidence": edgeguard_score
                })
        
        # RECOVERY TRACKING: After you lose a stock, track when you stabilize
        if stock_loss_detected or percent_reset_death:
            death_pct = stock_loss_detected.get("death_percent") if stock_loss_detected else percent_reset_death.get("death_percent", 0)
            if death_pct is None:
                death_pct = 0
            
            # Record the death moment for recovery tracking
            patterns["recovery_moments"].append({
                "timestamp": timestamp,
                "death_percent": death_pct,
                "stocks_remaining": confirmed_p1_stocks,
                "type": "respawn_start"
            })
            
            # OPPONENT EDGEGUARD DETECTION: When you die and opponent didn't take much damage
            # This means opponent successfully edgeguarded you
            opp_damage_during_your_death = 0
            lookback_start = max(0, i - 10)  # ~3 seconds at 3fps
            for j in range(lookback_start, i):
                if j > 0:
                    prev_opp_pct = smoothed_states[j-1].get("p2_percent") or 0
                    curr_opp_pct = smoothed_states[j].get("p2_percent") or 0
                    opp_damage_during_your_death += max(0, curr_opp_pct - prev_opp_pct)
            
            # Check damage opponent dealt to you before your death
            damage_taken_before_death = 0
            for j in range(lookback_start, i):
                if j > 0:
                    prev_your_pct = smoothed_states[j-1].get("p1_percent") or 0
                    curr_your_pct = smoothed_states[j].get("p1_percent") or 0
                    damage_taken_before_death += max(0, curr_your_pct - prev_your_pct)
            
            # Edgeguard heuristics (from opponent's perspective):
            # - Your death percent 50-145% (edgeguards kill earlier)
            # - Opponent didn't take damage (clean edgeguard)
            # - Opponent didn't deal much damage right before (not a combo kill)
            is_edgeguard_percent = 50 <= death_pct <= 145
            is_clean_for_opponent = opp_damage_during_your_death < 15
            is_not_combo = damage_taken_before_death < 30
            
            edgeguard_score = 0
            if is_edgeguard_percent:
                edgeguard_score += 1
            if is_clean_for_opponent:
                edgeguard_score += 1
            if is_not_combo:
                edgeguard_score += 1
            if opp_damage_during_your_death < 5:
                edgeguard_score += 1
            
            if edgeguard_score >= 3:
                patterns["got_edgeguarded"] = patterns.get("got_edgeguarded", [])
                patterns["got_edgeguarded"].append({
                    "timestamp": timestamp,
                    "your_death_percent": death_pct,
                    "opponent_damage_taken": opp_damage_during_your_death,
                    "damage_you_took_before": damage_taken_before_death,
                    "confidence": edgeguard_score
                })
        
        # MOMENTUM SWING DETECTION: Track when one player deals multiple hits without trading
        if p2_damage_taken > 10 and p1_damage_taken < 5:
            # You dealt damage without taking much back - positive momentum
            if not patterns["momentum_swings"] or (timestamp - patterns["momentum_swings"][-1].get("timestamp", 0)) > 5:
                patterns["momentum_swings"].append({
                    "timestamp": timestamp,
                    "type": "advantage",
                    "damage_dealt": p2_damage_taken,
                    "damage_taken": p1_damage_taken
                })
        elif p1_damage_taken > 20 and p2_damage_taken < 5:
            # You took heavy damage without dealing back - negative momentum
            if not patterns["momentum_swings"] or (timestamp - patterns["momentum_swings"][-1].get("timestamp", 0)) > 5:
                patterns["momentum_swings"].append({
                    "timestamp": timestamp,
                    "type": "disadvantage", 
                    "damage_dealt": p2_damage_taken,
                    "damage_taken": p1_damage_taken
                })
        
        # detect long neutral (no significant damage for a while)
        # IMPROVED: Stricter criteria - true neutral is usually 5-8 seconds max
        total_damage = p1_damage_taken + p2_damage_taken
        
        # Don't count neutral if:
        # 1. Either player is near 0% (likely respawning)
        # 2. Percents look stuck (same as previous - could be OCR error)
        # 3. Within 10 seconds of a stock loss (respawn invincibility + re-engagement)
        is_respawn_period = (p1_percent < 5 or p2_percent < 5)
        percents_look_stuck = (p1_percent == prev_p1_percent and p2_percent == prev_p2_percent)
        
        # Check if we're near a recent stock loss
        recent_stock_loss = False
        for sl in patterns.get("stock_losses", []):
            if abs(timestamp - sl["timestamp"]) < 10:
                recent_stock_loss = True
                break
        for k in patterns.get("kills", []):
            if abs(timestamp - k["timestamp"]) < 10:
                recent_stock_loss = True
                break
        
        # Also check if there's been ANY damage in the last few frames (OCR might miss some)
        recent_damage = False
        for j in range(max(0, i-5), i):
            s = smoothed_states[j]
            if j > 0:
                ps = smoothed_states[j-1]
                if (s.get("p1_percent") or 0) > (ps.get("p1_percent") or 0) + 3:
                    recent_damage = True
                if (s.get("p2_percent") or 0) > (ps.get("p2_percent") or 0) + 3:
                    recent_damage = True
        
        if total_damage < 3 and not is_respawn_period and not recent_stock_loss and not recent_damage:
            if neutral_start is None:
                neutral_start = timestamp
                neutral_start_p1 = p1_percent
                neutral_start_p2 = p2_percent
        else:
            # Threshold reduced from 8 to 6 seconds for more accurate neutral detection
            if neutral_start and (timestamp - neutral_start) > 6:
                # Additional validation: at least one player's percent should have changed
                # (indicates they were actually playing, not just OCR stuck)
                p1_moved = abs(p1_percent - neutral_start_p1) > 2
                p2_moved = abs(p2_percent - neutral_start_p2) > 2
                
                # Only record if there was some engagement (not totally stuck OCR)
                if p1_moved or p2_moved:
                    patterns["long_neutral"].append({
                        "start": neutral_start,
                        "end": timestamp,
                        "duration": timestamp - neutral_start
                    })
            neutral_start = None
            neutral_start_p1 = 0
            neutral_start_p2 = 0
        
        prev_p1_percent = p1_percent
        prev_p2_percent = p2_percent
    
    # Deduplicate stock events - only keep one per actual stock loss
    # NEVER remove the only final-stock event (0 stocks remaining)
    patterns["stock_losses"] = _deduplicate_events(
        patterns["stock_losses"], time_window=5.0, final_stock_key="stocks_remaining"
    )
    patterns["kills"] = _deduplicate_events(
        patterns["kills"], time_window=5.0, final_stock_key="opponent_stocks_remaining"
    )
    
    # Track global max percents (not affected by resets after deaths)
    patterns["p1_true_max_percent"] = global_p1_max
    patterns["p2_true_max_percent"] = global_p2_max

    # --- Phase tracking (additive, does not modify any existing detection) ---
    patterns["game_phases"] = _compute_game_phases(
        smoothed_states, patterns, game_start_time
    )
    patterns["after_death_phases"] = _compute_after_death_phases(
        smoothed_states, patterns, game_start_time
    )
    patterns["stage_control_timeline"] = _compute_stage_control(
        smoothed_states, game_start_time
    )

    return patterns


def _deduplicate_events(events: list, time_window: float = 5.0, final_stock_key: str = None) -> list:
    """
    Remove duplicate events within a time window, keeping the first one.
    NEVER remove the only final-stock event (stocks_remaining/opponent_stocks_remaining == 0).
    """
    if not events:
        return events
    
    # Sort by timestamp
    sorted_events = sorted(events, key=lambda x: x.get("timestamp", 0))
    final_events = [e for e in sorted_events if (final_stock_key and e.get(final_stock_key) == 0)]
    
    deduplicated = []
    last_timestamp = -999
    
    for event in sorted_events:
        ts = event.get("timestamp", 0)
        is_final = final_stock_key and event.get(final_stock_key) == 0
        # Always keep final-stock events (game-ender)
        if is_final:
            deduplicated.append(event)
            if ts > last_timestamp:
                last_timestamp = ts
            continue
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
        # CRITICAL: never smooth away 0 stocks (final death) - preserve raw 0 from validator
        p1_stocks = [s.get("p1_stocks") for s in window if s.get("p1_stocks") is not None]
        p2_stocks = [s.get("p2_stocks") for s in window if s.get("p2_stocks") is not None]
        if p1_stocks:
            mode_p1 = max(set(p1_stocks), key=p1_stocks.count)
            if state.get("p1_stocks") == 0:
                smoothed_state["p1_stocks"] = 0  # preserve final death
            else:
                smoothed_state["p1_stocks"] = mode_p1
        if p2_stocks:
            mode_p2 = max(set(p2_stocks), key=p2_stocks.count)
            if state.get("p2_stocks") == 0:
                smoothed_state["p2_stocks"] = 0  # preserve final kill
            else:
                smoothed_state["p2_stocks"] = mode_p2
        
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
    3. Stock decrease persists for 4+ frames (relaxed for end-of-video)
    4. Percent MUST reset to <15% after the loss (relaxed for final death)
    5. Stock was higher for 2+ frames before this point
    """
    if current_idx < 3:
        return None
    
    # Check if we're near the end of the video (last 10% of frames)
    near_end_of_video = current_idx >= len(game_states) * 0.9
    
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
    
    # validation 3: check that the stock loss persists for some frames AFTER
    frames_to_check = min(5, len(game_states) - current_idx - 1)
    persisting_low_stock = 0
    
    for j in range(1, frames_to_check + 1):
        future_state = game_states[current_idx + j]
        future_stocks = future_state.get(stocks_key)
        if future_stocks is not None and future_stocks <= current_stocks:
            persisting_low_stock += 1
    
    # Relaxed requirement near end of video (final death may not have many frames after)
    required_persisting = 1 if near_end_of_video else 4
    # At end of video we may have 0 future frames - still accept final death (current_stocks == 0)
    if near_end_of_video and current_stocks == 0 and frames_to_check < required_persisting:
        return {"new_stocks": 0, "death_percent": max_recent_percent}
    if persisting_low_stock < required_persisting and frames_to_check >= required_persisting:
        return None
    
    # If going to 0 stocks (final death), skip percent reset check - game ends
    if current_stocks == 0:
        return {"new_stocks": current_stocks, "death_percent": max_recent_percent}
    
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


# ---------------------------------------------------------------------------
# Game-phase helpers (Phase 2 of coaching upgrade)
# ---------------------------------------------------------------------------

def _compute_game_phases(
    smoothed_states: list, patterns: dict, game_start_time: float
) -> list:
    """
    Segment the match into phases: neutral, advantage, disadvantage, after_death.

    Phases are derived from the damage flow between existing events.
    A 3-second sliding window determines which player is dealing/taking damage.
    """
    if len(smoothed_states) < 3:
        return []

    # Collect death timestamps for after_death tagging (5-second windows)
    death_times = sorted(
        sl.get("timestamp", 0) for sl in patterns.get("stock_losses", [])
    )

    phases = []
    current_phase = "neutral"
    phase_start = game_start_time
    phase_dmg_dealt = 0.0
    phase_dmg_taken = 0.0
    WINDOW = 3.0  # seconds

    prev_p1 = 0
    prev_p2 = 0

    for i, state in enumerate(smoothed_states):
        ts = state["timestamp"]
        if ts < game_start_time:
            continue

        p1_pct = state.get("p1_percent") or 0
        p2_pct = state.get("p2_percent") or 0
        dmg_taken = max(0, p1_pct - prev_p1) if p1_pct >= prev_p1 else 0
        dmg_dealt = max(0, p2_pct - prev_p2) if p2_pct >= prev_p2 else 0
        # Cap per-frame deltas to reject OCR noise
        dmg_taken = min(dmg_taken, 60)
        dmg_dealt = min(dmg_dealt, 60)

        phase_dmg_dealt += dmg_dealt
        phase_dmg_taken += dmg_taken

        # Determine phase from damage flow
        in_after_death = any(0 <= (ts - dt) <= 5 for dt in death_times)
        if in_after_death:
            new_phase = "after_death"
        elif phase_dmg_dealt > phase_dmg_taken + 10:
            new_phase = "advantage"
        elif phase_dmg_taken > phase_dmg_dealt + 10:
            new_phase = "disadvantage"
        else:
            new_phase = "neutral"

        # Transition?
        if new_phase != current_phase and (ts - phase_start) >= 1.0:
            phases.append({
                "start": round(phase_start, 2),
                "end": round(ts, 2),
                "phase": current_phase,
                "damage_dealt": round(phase_dmg_dealt, 1),
                "damage_taken": round(phase_dmg_taken, 1),
            })
            current_phase = new_phase
            phase_start = ts
            phase_dmg_dealt = 0.0
            phase_dmg_taken = 0.0

        # Reset rolling counters on window boundary
        if (ts - phase_start) > WINDOW:
            phase_dmg_dealt *= 0.5
            phase_dmg_taken *= 0.5

        prev_p1 = p1_pct
        prev_p2 = p2_pct

    # Close final phase
    if smoothed_states:
        final_ts = smoothed_states[-1]["timestamp"]
        if final_ts > phase_start:
            phases.append({
                "start": round(phase_start, 2),
                "end": round(final_ts, 2),
                "phase": current_phase,
                "damage_dealt": round(phase_dmg_dealt, 1),
                "damage_taken": round(phase_dmg_taken, 1),
            })

    return phases


def _compute_after_death_phases(
    smoothed_states: list, patterns: dict, game_start_time: float
) -> list:
    """
    For each stock loss, track what happened in the next 5 seconds:
    damage taken, damage dealt, time to first interaction, behavior tag.
    """
    stock_losses = patterns.get("stock_losses", [])
    if not stock_losses or not smoothed_states:
        return []

    results = []
    for sl in stock_losses:
        # Skip final death (no respawn)
        if sl.get("stocks_remaining", 1) == 0:
            continue

        death_ts = sl.get("timestamp", 0)
        window_start = death_ts + 0.5  # skip death animation
        window_end = death_ts + 5.0

        dmg_taken = 0.0
        dmg_dealt = 0.0
        first_interaction_ts = None
        prev_p1 = None
        prev_p2 = None

        for state in smoothed_states:
            ts = state["timestamp"]
            if ts < window_start:
                prev_p1 = state.get("p1_percent") or 0
                prev_p2 = state.get("p2_percent") or 0
                continue
            if ts > window_end:
                break

            p1_pct = state.get("p1_percent") or 0
            p2_pct = state.get("p2_percent") or 0

            if prev_p1 is not None:
                dt = max(0, p1_pct - prev_p1) if p1_pct >= prev_p1 else 0
                dd = max(0, p2_pct - prev_p2) if p2_pct >= prev_p2 else 0
                dt = min(dt, 60)
                dd = min(dd, 60)
                dmg_taken += dt
                dmg_dealt += dd

                if first_interaction_ts is None and (dt > 3 or dd > 3):
                    first_interaction_ts = ts

            prev_p1 = p1_pct
            prev_p2 = p2_pct

        time_to_interact = (
            round(first_interaction_ts - death_ts, 2)
            if first_interaction_ts else None
        )

        # Classify behavior
        if dmg_taken > 25 and dmg_dealt < 10:
            behavior = "panic"
        elif dmg_dealt > dmg_taken + 10:
            behavior = "aggressive"
        elif dmg_taken < 10 and dmg_dealt < 10:
            behavior = "composed"
        else:
            behavior = "neutral"

        results.append({
            "death_timestamp": round(death_ts, 2),
            "damage_taken": round(dmg_taken, 1),
            "damage_dealt": round(dmg_dealt, 1),
            "time_to_first_interaction": time_to_interact,
            "behavior": behavior,
            "stocks_remaining": sl.get("stocks_remaining"),
        })

    return results


def _compute_stage_control(
    smoothed_states: list, game_start_time: float
) -> list:
    """
    Rolling 3-second damage-flow snapshot sampled every 1 second.
    Positive control_score = you dominating, negative = opponent dominating.
    """
    if len(smoothed_states) < 3:
        return []

    SAMPLE_INTERVAL = 1.0
    WINDOW = 3.0
    timeline = []

    # Pre-compute per-frame damage deltas
    deltas = []
    for i, state in enumerate(smoothed_states):
        if i == 0 or state["timestamp"] < game_start_time:
            deltas.append((state["timestamp"], 0.0, 0.0))
            continue
        prev = smoothed_states[i - 1]
        p1 = state.get("p1_percent") or 0
        p2 = state.get("p2_percent") or 0
        pp1 = prev.get("p1_percent") or 0
        pp2 = prev.get("p2_percent") or 0

        dt = min(60, max(0, p1 - pp1)) if p1 >= pp1 else 0
        dd = min(60, max(0, p2 - pp2)) if p2 >= pp2 else 0
        deltas.append((state["timestamp"], dd, dt))  # (ts, you_dealt, you_took)

    # Sample at 1-second intervals
    if not deltas:
        return []
    start_ts = max(game_start_time, deltas[0][0])
    end_ts = deltas[-1][0]
    sample_ts = start_ts

    while sample_ts <= end_ts:
        window_dealt = 0.0
        window_taken = 0.0
        for ts, dd, dt in deltas:
            if sample_ts - WINDOW <= ts <= sample_ts:
                window_dealt += dd
                window_taken += dt

        control = round(window_dealt - window_taken, 1)
        timeline.append({
            "timestamp": round(sample_ts, 2),
            "damage_dealt": round(window_dealt, 1),
            "damage_taken": round(window_taken, 1),
            "control_score": control,
        })
        sample_ts += SAMPLE_INTERVAL

    return timeline

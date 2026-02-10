"""
Character move damage reference tables for SSBU.

Used to ground vision analysis: given a damage delta between frames,
we can narrow down which moves could have been used.

Base damage values from Ultimate Frame Data. All matches we analyze are 1v1,
so we apply the 1.2x 1v1 multiplier at runtime for accurate matching.
"""

# 1v1 mode multiplier — SSBU applies 1.2x damage in all 1v1 matches
_1V1_MULTIPLIER = 1.2

# Auto-generated from Ultimate Frame Data (ultimateframedata.com)
# Source: github.com/alexandercarls/ultimateframedata.com-scraper
# Pyra/Mythra added manually (not in scraper dataset)
#
# Format: character_key -> list of (move_name, base_damage)
# These are BASE values. Use _get_1v1_moves() to get 1v1-adjusted values.
# Multi-hit moves show total base damage.
MOVE_DAMAGE = {
    "banjo": [
        ("ftilt", 9), ("utilt", 10), ("dtilt", 6), ("dash attack", 12),
        ("fsmash", 16), ("usmash", 6.1), ("dsmash", 15), ("jab combo", 8.2),
        ("nair", 5), ("fair", 15), ("bair", 6.4), ("uair", 7.4),
        ("dair", 12), ("egg firing", 5.4), ("breegull blaster", 3.2), ("wonderwing", 22),
        ("shock spring jump", 3), ("rear egg", 9), ("fthrow", 8.4), ("bthrow", 11.4),
        ("uthrow", 8.4), ("dthrow", 5.6),
    ],
    "bayonetta": [
        ("utilt", 7.5), ("dtilt", 6), ("dash attack", 10), ("fsmash", 16),
        ("usmash", 17), ("dsmash", 16), ("jab combo", 5), ("nair", 8),
        ("bair", 13), ("uair", 7.5), ("dair", 9), ("bullet climax", 1.3),
        ("bullet climax, full charge", 2.7), ("heel slide", 8), ("after burner kick", 7), ("after burner kick, down", 6.5),
        ("witch twist", 6.2), ("fthrow", 10), ("bthrow", 9), ("uthrow", 7.5),
        ("dthrow", 8),
    ],
    "bowser": [
        ("ftilt", 13), ("utilt", 11), ("dtilt", 8), ("dash attack", 12),
        ("fsmash", 23), ("usmash", 22), ("dsmash", 16), ("jab combo", 11),
        ("nair", 6), ("fair", 13), ("bair", 19), ("uair", 15),
        ("dair", 18), ("fire breath", 1.8), ("whirling fortress", 7), ("whirling fortress, air", 10),
        ("bowser bomb", 35), ("bowser bomb, air", 20), ("fthrow", 12), ("bthrow", 12),
        ("uthrow", 8.5), ("dthrow", 14),
    ],
    "bowser jr": [
        ("ftilt", 8), ("utilt", 6), ("dtilt", 8), ("dash attack", 5.8),
        ("fsmash", 12), ("usmash", 8.3), ("dsmash", 18), ("jab combo", 4),
        ("nair", 8), ("fair", 20), ("bair", 14), ("uair", 10),
        ("dair", 2.5), ("clown cannon", 20), ("clown kart dash", 7.3), ("spinout", 16.3),
        ("abandon ship", 18), ("hammer", 18), ("mechakoopa", 4), ("fthrow", 10),
        ("bthrow", 11), ("uthrow", 7), ("dthrow", 5.2),
    ],
    "captain falcon": [
        ("ftilt", 9), ("utilt", 11), ("dtilt", 10), ("dash attack", 10),
        ("fsmash", 20), ("usmash", 33), ("dsmash", 18), ("jab combo", 8),
        ("nair", 6), ("fair", 22), ("bair", 13), ("uair", 10),
        ("dair", 14), ("falcon punch", 28), ("raptor boost", 10), ("raptor boost, air", 10),
        ("falcon kick", 15), ("falcon kick, air", 15), ("fthrow", 7.5), ("bthrow", 7.5),
        ("uthrow", 9), ("dthrow", 6),
    ],
    "chrom": [
        ("ftilt", 10.9), ("utilt", 10.4), ("dtilt", 9), ("dash attack", 12),
        ("fsmash", 18), ("usmash", 13), ("dsmash", 14.2), ("jab", 6.5),
        ("nair", 6.6), ("fair", 9), ("bair", 10.9), ("uair", 7.6),
        ("dair", 14.2), ("flare blade", 58), ("double edged dance", 2.8), ("double edged dance neutral", 11.8),
        ("double edged dance up", 13), ("double edged dance down", 10), ("soaring slash", 19.5), ("fthrow", 5),
        ("bthrow", 5), ("uthrow", 6), ("dthrow", 5),
    ],
    "cloud": [
        ("ftilt", 11), ("utilt", 8), ("dtilt", 7), ("dash attack", 11),
        ("fsmash", 18), ("usmash", 13), ("dsmash", 14), ("jab combo", 8),
        ("nair", 8), ("fair", 14), ("bair", 13), ("uair", 11),
        ("dair", 13), ("blade beam", 8), ("limit blade beam", 11), ("cross slash", 13),
        ("limit cross slash", 18), ("climhazzard", 11), ("limit climhazzard", 4.5), ("finishing touch", 1),
        ("fthrow", 7), ("bthrow", 6), ("uthrow", 8.5), ("dthrow", 7),
    ],
    "corrin": [
        ("ftilt", 10.5), ("utilt", 9), ("dtilt", 7.5), ("dash attack", 3),
        ("fsmash", 15.2), ("usmash", 15), ("dsmash", 14), ("jab combo", 8.5),
        ("nair", 7), ("fair", 7.5), ("bair", 11), ("uair", 9),
        ("dair", 3), ("dragon fang shot", 15), ("chomp", 20), ("dragon lunge, pin", 7),
        ("dragon lunge, air", 15), ("dragon lunge, pin kick", 12), ("dragon lunge, back kick", 7), ("dragon ascent", 8.7),
    ],
    "daisy": [
        ("ftilt", 8), ("utilt", 10), ("dtilt", 7), ("dash attack", 6),
        ("fsmash", 18), ("usmash", 17), ("dsmash", 3), ("jab combo", 5),
        ("nair", 13), ("fair", 15), ("bair", 12), ("uair", 6),
        ("dair", 7), ("daisy bomber", 12), ("daisy bomber, air", 12), ("daisy parasol", 8),
        ("turnip pull", 35.9), ("fthrow", 8), ("bthrow", 11), ("uthrow", 8),
        ("dthrow", 8),
    ],
    "dark pit": [
        ("ftilt", 10), ("utilt", 5), ("dtilt", 6), ("dash attack", 11),
        ("fsmash", 10), ("usmash", 13), ("dsmash", 12), ("jab combo", 8),
        ("nair", 5.2), ("fair", 8.5), ("bair", 12), ("uair", 6.5),
        ("dair", 10), ("silver bow", 19.5), ("electroshock arm", 12), ("electrodash arm, air", 9.5),
        ("fthrow", 10), ("bthrow", 8), ("uthrow", 11), ("dthrow", 6),
    ],
    "dark samus": [
        ("ftilt", 10), ("utilt", 13), ("dtilt", 12), ("dash attack", 10),
        ("fsmash", 14), ("usmash", 9), ("dsmash", 12), ("jab combo", 11),
        ("nair", 10), ("fair", 9.6), ("bair", 14), ("uair", 8.2),
        ("dair", 14), ("charge shot", 31.1), ("charge shot, full charge", 28), ("homing missle", 8),
        ("super missle", 12), ("screw attack", 6), ("screw attack, air", 1), ("bomb", 5),
        ("fthrow", 10), ("bthrow", 10), ("uthrow", 12), ("dthrow", 8),
    ],
    "diddy kong": [
        ("ftilt", 10), ("utilt", 6), ("dtilt", 5.5), ("dash attack", 3),
        ("fsmash", 11), ("usmash", 8.5), ("dsmash", 15), ("jab combo", 7.5),
        ("nair", 6), ("fair", 10), ("bair", 9), ("uair", 7),
        ("dair", 13), ("peanut popgun", 20.3), ("peanut popgun, misfire", 23), ("monkey flip, attack", 14),
        ("rocketbarrel boost", 10), ("rocketbarrel boost, explosion", 18), ("fthrow", 9), ("bthrow", 12),
        ("uthrow", 5), ("dthrow", 7),
    ],
    "donkey kong": [
        ("ftilt", 9), ("utilt", 10), ("dtilt", 6), ("dash attack", 12),
        ("fsmash", 22), ("usmash", 19), ("dsmash", 17), ("jab combo", 10),
        ("nair", 12), ("fair", 16), ("bair", 13), ("uair", 13),
        ("dair", 16), ("giant punch", 37), ("giant punch, full charge", 28), ("headbutt", 10),
        ("spinning kong", 10.3), ("spinning kong, air", 8), ("hand slap", 14), ("hand slap, air", 6),
        ("bthrow", 11), ("uthrow", 9), ("dthrow", 7),
    ],
    "dr. mario": [
        ("ftilt", 8.2), ("utilt", 7.4), ("dtilt", 8.2), ("dash attack", 11.5),
        ("fsmash", 20.9), ("usmash", 16.4), ("dsmash", 14.1), ("jab combo", 9.3),
        ("nair", 9.4), ("fair", 17.6), ("bair", 14.1), ("uair", 10.2),
        ("dair", 14.1), ("megavitamin pill", 5.8), ("super sheet", 8.2), ("super jump punch", 14.1),
        ("dr. tornado", 3.5), ("fthrow", 9.4), ("bthrow", 12.9), ("uthrow", 8.2),
        ("dthrow", 5.8),
    ],
    "duck hunt": [
        ("ftilt", 8), ("utilt", 7), ("dtilt", 8), ("dash attack", 10),
        ("fsmash", 13), ("usmash", 12.5), ("dsmash", 6), ("jab combo", 8),
        ("nair", 11), ("fair", 10), ("bair", 12.5), ("uair", 9),
        ("dair", 10), ("trick shot", 12), ("clay shooting", 2), ("clay shooting, detonate", 3),
        ("wild gunman, leader in brown coat", 10), ("wild gunman, black suit", 9), ("wild gunman, sombrero guy", 11), ("wild gunman, short cowboy", 8),
        ("wild gunman, tall cowboy", 8), ("fthrow", 8), ("bthrow", 9), ("uthrow", 6),
        ("dthrow", 5),
    ],
    "falco": [
        ("ftilt", 6), ("utilt", 4), ("dtilt", 13), ("dash attack", 9),
        ("fsmash", 16), ("usmash", 17), ("dsmash", 15), ("jab combo", 3),
        ("nair", 9), ("fair", 8), ("bair", 13), ("uair", 9),
        ("dair", 13), ("blaster", 3), ("falco phantasm", 7), ("fire bird", 3),
        ("reflector", 5), ("fthrow", 7), ("bthrow", 9), ("uthrow", 8),
        ("dthrow", 5),
    ],
    "fox": [
        ("ftilt", 7), ("utilt", 8), ("dtilt", 8), ("dash attack", 6),
        ("fsmash", 14), ("usmash", 16), ("dsmash", 14), ("jab combo", 2.8),
        ("nair", 9), ("fair", 11.5), ("bair", 13), ("uair", 15),
        ("dair", 5.4), ("blaster", 3), ("fox illusion", 8), ("fire fox", 17.7),
        ("reflector", 2), ("fthrow", 7), ("bthrow", 4), ("uthrow", 4),
        ("dthrow", 3),
    ],
    "game & watch": [
        ("ftilt", 12), ("utilt", 7), ("dtilt", 9), ("dash attack", 10),
        ("fsmash", 18), ("usmash", 16), ("dsmash", 15), ("jab", 3),
        ("nair", 4), ("fair", 15), ("bair", 3), ("uair", 3),
        ("dair", 14.5), ("chef", 18), ("judge", 45), ("fire", 6),
        ("oil panic, overload", 48), ("fthrow", 8), ("bthrow", 8), ("uthrow", 12),
        ("dthrow", 4),
    ],
    "ganondorf": [
        ("ftilt", 14), ("utilt", 24), ("dtilt", 14), ("dash attack", 15),
        ("fsmash", 24), ("usmash", 24), ("dsmash", 20), ("jab", 11),
        ("nair", 7), ("fair", 18), ("bair", 18.5), ("uair", 13),
        ("dair", 19), ("warlock punch", 37), ("warlock punch, air", 40), ("flame choke, success", 12),
        ("flame choke, air success", 15), ("dark dive", 7), ("dark dive, grab success", 10.9), ("wizard's foot", 16),
        ("wizard's foot, air", 15), ("fthrow", 13), ("bthrow", 10), ("uthrow", 13),
        ("dthrow", 7),
    ],
    "greninja": [
        ("ftilt", 8.3), ("utilt", 4.5), ("dtilt", 4), ("dash attack", 8),
        ("fsmash", 14), ("usmash", 30), ("dsmash", 13), ("jab combo", 7),
        ("nair", 11), ("fair", 14), ("bair", 6), ("uair", 4.3),
        ("dair", 8), ("water shuriken", 23.8), ("shadow sneak", 12), ("hydro pump", 2),
        ("substitute, attack", 13), ("fthrow", 8), ("bthrow", 9), ("uthrow", 5),
        ("dthrow", 5),
    ],
    "hero": [
        ("utilt", 11), ("dtilt", 7), ("dash attack", 15), ("fsmash", 18),
        ("usmash", 16), ("dsmash", 13), ("jab combo", 10), ("nair", 9),
        ("fair", 12), ("bair", 14), ("uair", 7), ("dair", 16),
        ("frizz/frizzle/kafrizz", 19), ("zap/zapple/kazap", 4), ("woosh/swoosh/kaswoosh", 21), ("bang", 15.5),
        ("kaboom", 28), ("sizz", 13.5), ("sizzle", 25), ("whack", 1),
        ("thwack", 3), ("kamikazee", 50.1), ("magic burst", 18.9), ("heal", 11),
        ("flame slash", 22), ("kacrackle slash", 17), ("hatchet man", 35), ("metal slash", 1),
        ("fthrow", 7), ("bthrow", 9), ("uthrow", 7), ("dthrow", 6),
    ],
    "ice climbers": [
        ("ftilt", 9.1), ("utilt", 5.3), ("dtilt", 6), ("dash attack", 6),
        ("fsmash", 12.1), ("usmash", 11.1), ("dsmash", 13.1), ("jab combo", 5.5),
        ("nair", 7), ("fair", 12.1), ("bair", 10.1), ("uair", 9.1),
        ("dair", 8.1), ("ice shot", 3.5), ("squal hammer, both", 4), ("squal hammer, alone", 2),
        ("belay", 16), ("blizzard", 1.7), ("fthrow", 8), ("bthrow", 6),
        ("uthrow", 8), ("dthrow", 6),
    ],
    "ike": [
        ("ftilt", 12.5), ("utilt", 12), ("dtilt", 8), ("dash attack", 14),
        ("fsmash", 22), ("usmash", 17), ("dsmash", 44), ("jab combo", 10),
        ("nair", 7.5), ("fair", 11.5), ("bair", 14), ("uair", 11),
        ("dair", 15), ("eruption", 45), ("quickdraw", 13), ("aether", 16),
        ("fthrow", 7.5), ("bthrow", 7), ("uthrow", 7.5), ("dthrow", 7),
    ],
    "incineroar": [
        ("ftilt", 13), ("utilt", 9), ("dtilt", 9), ("dash attack", 13),
        ("fsmash", 20), ("usmash", 17), ("dsmash", 16), ("jab combo", 12),
        ("nair", 13), ("fair", 13), ("bair", 13), ("uair", 8),
        ("dair", 15), ("darkest lariat", 22), ("alolan whip, lariat attack", 20), ("alolan whip, back body drop", 12),
        ("failure", 4), ("cross chop", 30), ("revenge, counter attack", 2.4), ("fthrow", 12),
        ("bthrow", 14), ("uthrow", 12), ("dthrow", 9),
    ],
    "inkling": [
        ("ftilt", 9), ("utilt", 6), ("dtilt", 6), ("dash attack", 8),
        ("fsmash", 16), ("usmash", 29), ("dsmash", 12.5), ("jab combo", 7.5),
        ("nair", 7), ("fair", 10), ("bair", 10), ("uair", 6.5),
        ("dair", 12), ("splattershot", 0.3), ("splat roller", 15), ("super jump", 8),
        ("splat bomb", 15), ("fthrow", 8), ("bthrow", 9), ("uthrow", 6),
        ("dthrow", 7),
    ],
    "isabelle": [
        ("ftilt", 9), ("utilt", 8), ("dtilt", 13), ("dash attack", 10),
        ("fsmash", 17), ("usmash", 16), ("dsmash", 10), ("jab", 2),
        ("nair", 10), ("fair", 7), ("bair", 17), ("uair", 10),
        ("dair", 10), ("fishing rod, throw forward", 17), ("fishing rod, throw back", 14), ("fishing rod, throw up", 15),
        ("fishing rod, throw down", 15),
    ],
    "jigglypuff": [
        ("ftilt", 10), ("utilt", 9), ("dtilt", 10), ("dash attack", 12),
        ("fsmash", 16), ("usmash", 15), ("dsmash", 11), ("jab combo", 6),
        ("nair", 11), ("fair", 9), ("bair", 13), ("uair", 9),
        ("dair", 2), ("rollout", 20), ("pound", 11), ("rest", 20),
        ("fthrow", 10), ("bthrow", 10), ("uthrow", 8), ("dthrow", 12),
    ],
    "joker": [
        ("ftilt", 5), ("utilt", 6), ("dtilt", 6), ("dash attack", 8),
        ("fsmash", 14), ("usmash", 12), ("dsmash", 12), ("jab combo", 7.6),
        ("nair", 7), ("fair", 7), ("bair", 9), ("uair", 3.7),
        ("dair", 8), ("gun", 5), ("gun, dash forward", 6), ("gun, dash back", 5),
        ("from ground only", 6), ("from air only", 15.5), ("gun special, arsene", 6), ("gun special, dash forward", 7),
        ("gun special, dash back", 5), ("eiha", 2), ("eigaon", 4), ("air, grappling attack", 11),
        ("rebel's guard, counterattack", 2.4), ("fthrow", 8), ("bthrow", 10), ("uthrow", 7),
        ("dthrow", 7),
    ],
    "ken": [
        ("dash attack", 12), ("fsmash", 16), ("usmash", 17), ("dsmash", 16),
        ("jab combo", 26), ("nair", 6.5), ("fair", 14), ("bair", 16),
        ("uair", 6.5), ("dair", 12), ("hadouken", 6.8), ("tatsumaki senpukyaku", 3.4),
        ("tatsumaki senpukyaku, air", 3.4), ("shoryuken", 13), ("true shoryuken", 15.6), ("flame shoryuken", 16.7),
        ("true flame shoryuken", 20), ("focus attack", 17), ("input command", 30),
    ],
    "king dedede": [
        ("ftilt", 3), ("utilt", 10), ("dtilt", 10), ("dash attack", 16),
        ("fsmash", 25), ("usmash", 16), ("dsmash", 13), ("jab combo", 4.7),
        ("nair", 12), ("fair", 12), ("bair", 16), ("uair", 6),
        ("dair", 15), ("gordo throw", 14), ("super dedede jump", 32), ("jet hammer, partial charge", 40.8),
        ("jet hammer, full charge", 40), ("fthrow", 10), ("bthrow", 13), ("uthrow", 9),
        ("dthrow", 6),
    ],
    "king k. rool": [
        ("ftilt", 13), ("utilt", 11.5), ("dtilt", 13), ("dash attack", 15),
        ("fsmash", 19.9), ("usmash", 26), ("dsmash", 22), ("jab combo", 12),
        ("nair", 12), ("fair", 15), ("bair", 19), ("uair", 14),
        ("dair", 12), ("blunderbuss kannonball", 13), ("blunderbuss, second shot", 18), ("crownerang", 9),
        ("propellerpack", 3),
    ],
    "kirby": [
        ("ftilt", 8), ("utilt", 5), ("dtilt", 6), ("dash attack", 12),
        ("fsmash", 15), ("usmash", 15), ("dsmash", 14), ("jab combo", 3.4),
        ("nair", 10), ("fair", 5), ("bair", 13), ("uair", 9),
        ("dair", 2), ("inhale, copy/spit", 10), ("hammer", 28.8), ("hammer, full charge", 35),
        ("air", 16), ("final cutter", 18), ("stone", 14), ("stone, air", 18),
        ("fthrow", 7), ("bthrow", 8), ("uthrow", 10), ("dthrow", 3),
    ],
    "link": [
        ("ftilt", 13), ("utilt", 11), ("dtilt", 9), ("dash attack", 14),
        ("usmash", 17), ("dsmash", 16), ("jab combo", 10), ("nair", 11),
        ("fair", 10), ("bair", 7), ("uair", 15), ("dair", 18),
        ("hero's bow", 16), ("boomerang", 9.6), ("spin attack", 14), ("spin attack, air", 10),
        ("remote bomb, detonate", 7), ("fthrow", 5.5), ("bthrow", 5.5), ("uthrow", 7),
        ("dthrow", 6),
    ],
    "little mac": [
        ("ftilt", 8), ("utilt", 6.5), ("dtilt", 8), ("dash attack", 10),
        ("fsmash", 24), ("usmash", 21), ("dsmash", 13), ("jab combo", 8),
        ("nair", 2), ("fair", 5), ("bair", 6), ("uair", 5),
        ("dair", 5), ("straight lunge, partial charge", 28.6), ("straight lunge, full charge", 30), ("k.o. punch", 48),
        ("jolt haymaker", 14), ("jolt haymaker, air", 14), ("rising uppercut", 7), ("fthrow", 8),
        ("bthrow", 9), ("uthrow", 7), ("dthrow", 7),
    ],
    "lucario": [
        ("ftilt", 22.1), ("utilt", 9.6), ("dtilt", 3.3), ("dash attack", 16),
        ("fsmash", 20.8), ("usmash", 87.3), ("dsmash", 9.2), ("jab combo", 4.8),
        ("nair", 9.6), ("fair", 3.9), ("bair", 20.8), ("uair", 9.6),
        ("dair", 22.8), ("aura sphere", 4.5), ("aura sphere, full charge", 11.3), ("force palm", 8.6),
        ("force palm, grab", 8.5), ("extreme speed", 6.4), ("double team, counterattack", 8.2), ("fthrow", 13),
        ("bthrow", 6.6), ("uthrow", 22.8), ("dthrow", 4.6),
    ],
    "lucas": [
        ("ftilt", 11), ("utilt", 14.5), ("dtilt", 5), ("dash attack", 13),
        ("fsmash", 15), ("usmash", 23), ("dsmash", 17), ("jab combo", 7.5),
        ("nair", 6), ("fair", 12.5), ("bair", 12), ("uair", 11),
        ("dair", 5), ("pk freeze", 23), ("pk fire", 7), ("pk thunder", 3.2),
        ("pk thunder 2", 18.5), ("psi magnet", 8), ("fthrow", 10), ("bthrow", 10),
        ("uthrow", 10), ("dthrow", 11),
    ],
    "lucina": [
        ("ftilt", 11), ("utilt", 8), ("dtilt", 8.5), ("dash attack", 10.9),
        ("fsmash", 15), ("usmash", 17.2), ("dsmash", 14), ("jab combo", 8),
        ("nair", 8.5), ("fair", 10.5), ("bair", 11.8), ("uair", 11.4),
        ("dair", 14.2), ("shieldbreaker", 31.5), ("dancing blade", 2.8), ("dancing blade 2 neutral", 2.8),
        ("dancing blade 3 neutral", 3.3), ("dancing blade 4 neutral", 4.7), ("dancing blade 2 up", 2.8), ("dancing blade 3 up", 3.3),
        ("dancing blade 4 up", 5.6), ("dancing blade 3 down", 3.3), ("dancing blade 4 down", 6.2), ("dolphin slash", 11),
        ("fthrow", 4), ("bthrow", 4), ("uthrow", 5), ("dthrow", 4),
    ],
    "luigi": [
        ("ftilt", 9), ("utilt", 6), ("dtilt", 5), ("dash attack", 6),
        ("fsmash", 15), ("usmash", 14), ("dsmash", 15), ("jab combo", 8),
        ("nair", 12), ("fair", 8), ("bair", 14), ("uair", 11),
        ("dair", 10), ("fireball", 6), ("green missile", 52.1), ("super jump punch, ground", 25),
        ("super jump punch, air", 20), ("luigi cyclone", 6), ("fthrow", 9), ("bthrow", 10),
        ("uthrow", 8), ("dthrow", 6),
    ],
    "mario": [
        ("ftilt", 7), ("utilt", 5.5), ("dtilt", 7), ("dash attack", 8),
        ("fsmash", 17.7), ("usmash", 14), ("dsmash", 12), ("jab combo", 7.9),
        ("nair", 8), ("fair", 14), ("bair", 10.5), ("uair", 7),
        ("dair", 6.8), ("fireball", 5), ("cape", 7), ("super jump punch", 8.6),
        ("fthrow", 8), ("bthrow", 11), ("uthrow", 7), ("dthrow", 5),
    ],
    "marth": [
        ("ftilt", 12), ("utilt", 9), ("dtilt", 10), ("dash attack", 12),
        ("fsmash", 18), ("usmash", 17), ("dsmash", 17), ("jab combo", 11),
        ("nair", 9.5), ("fair", 11.5), ("bair", 12.5), ("uair", 13),
        ("dair", 15), ("shieldbreaker", 32), ("dancing blade", 3), ("dancing blade 2 neutral", 3),
        ("dancing blade 3 neutral", 4), ("dancing blade 4 neutral", 6), ("dancing blade 2 up", 3), ("dancing blade 3 up", 4),
        ("dancing blade 4 up", 7), ("dancing blade 3 down", 4), ("dancing blade 4 down", 11), ("dolphin slash", 11),
        ("fthrow", 4), ("bthrow", 4), ("uthrow", 5), ("dthrow", 4),
    ],
    "mega man": [
        ("ftilt", 4), ("utilt", 17), ("dtilt", 8), ("dash attack", 5.2),
        ("fsmash", 11.5), ("usmash", 9.5), ("dsmash", 17), ("jab", 4),
        ("nair", 4), ("fair", 8.5), ("bair", 5), ("uair", 6),
        ("dair", 14), ("metal blade", 5), ("crash bomber", 5), ("leaf shield", 1.5),
        ("leaf shield, throw", 3.8), ("fthrow", 8), ("bthrow", 11), ("uthrow", 7),
        ("dthrow", 4.5),
    ],
    "meta knight": [
        ("utilt", 7), ("dtilt", 5), ("dash attack", 7), ("fsmash", 16),
        ("usmash", 5), ("dsmash", 13), ("nair", 10), ("fair", 4.5),
        ("bair", 5.5), ("uair", 4), ("dair", 6), ("mach tornado", 12),
        ("drill rush", 4.1), ("shuttle loop", 9), ("shuttle loop, air", 6), ("dimensional cape, attack", 16),
        ("fthrow", 9), ("bthrow", 10), ("uthrow", 10), ("dthrow", 3.5),
    ],
    "mewtwo": [
        ("ftilt", 11), ("utilt", 7), ("dtilt", 5), ("dash attack", 12),
        ("fsmash", 20), ("usmash", 12), ("dsmash", 16), ("jab", 3),
        ("nair", 5.6), ("fair", 13), ("bair", 13), ("uair", 12),
        ("dair", 14), ("shadow ball", 27.4), ("shadow ball, fully charged", 25), ("disable", 1),
        ("fthrow", 5), ("bthrow", 10), ("uthrow", 12), ("dthrow", 9),
    ],
    "mii brawler": [
        ("ftilt", 8.5), ("utilt", 6), ("dtilt", 8), ("dash attack", 11),
        ("fsmash", 18), ("usmash", 14), ("dsmash", 13), ("jab combo", 2.8),
        ("nair", 10), ("fair", 6), ("bair", 12), ("uair", 9),
        ("dair", 13), ("shot put", 15), ("flashing mach punch", 9.9), ("exploding side kick", 28),
        ("onslaught", 8.5), ("onslaught, air", 8.5), ("burning dropkick", 13), ("suplex, success", 18),
        ("soaring axe kick", 4), ("helicopter kick", 10.5), ("thrust uppercut", 9.8), ("head-on assault", 36),
        ("head-on assault, air", 16), ("feint jump, kick", 10), ("fthrow", 9), ("bthrow", 9),
        ("uthrow", 11), ("dthrow", 6),
    ],
    "mii gunner": [
        ("ftilt", 13), ("utilt", 10), ("dtilt", 14), ("dash attack", 11),
        ("fsmash", 9.3), ("usmash", 12.5), ("dsmash", 14), ("jab combo", 8),
        ("nair", 10), ("fair", 8), ("bair", 13), ("uair", 5.8),
        ("dair", 15), ("charge blast", 30), ("laser blaze", 5), ("grenade launch", 7.8),
        ("flame pillar", 2.7), ("stealth burst", 18), ("homing", 7.5), ("super", 14.5),
        ("lunar launch", 7), ("cannon jump kick", 9), ("echo reflector", 2), ("bomb drop", 11),
        ("absorbing vortex", 4), ("fthrow", 7), ("bthrow", 10), ("uthrow", 10),
        ("dthrow", 7),
    ],
    "mii swordfighter": [
        ("ftilt", 12), ("utilt", 7), ("dtilt", 8), ("dash attack", 10),
        ("fsmash", 16), ("usmash", 7), ("dsmash", 15), ("jab combo", 11),
        ("nair", 8), ("fair", 5), ("bair", 14), ("uair", 16),
        ("dair", 6.5), ("gale strike", 13), ("shuriken of light", 6.5), ("blurring blade", 29.9),
        ("airborne assault", 12), ("gale stab", 18.5), ("chakram", 8), ("stone scabbard", 5),
        ("skyward slash dash", 4), ("hero's spin", 19.6), ("air", 23), ("reversal slash", 6),
        ("power thrust", 15), ("fthrow", 6), ("bthrow", 6), ("uthrow", 5),
        ("dthrow", 4),
    ],
    "mythra": [
        ("jab combo", 7), ("ftilt", 7), ("utilt", 6), ("dtilt", 5),
        ("dash attack", 10), ("fsmash", 11), ("usmash", 13), ("dsmash", 11),
        ("nair", 8), ("fair", 7), ("bair", 10), ("uair", 7),
        ("dair", 9), ("lightning buster", 8), ("photon edge", 14), ("ray of punishment", 12),
        ("fthrow", 8), ("bthrow", 6), ("uthrow", 5), ("dthrow", 3),
    ],
    "ness": [
        ("ftilt", 10), ("utilt", 7), ("dtilt", 4.5), ("dash attack", 4),
        ("fsmash", 22), ("usmash", 13), ("dsmash", 10), ("jab combo", 7.5),
        ("nair", 11), ("fair", 7), ("bair", 15), ("uair", 7.5), ("dair", 12),
        ("pk flash", 27), ("pk fire", 1), ("pk thunder", 12), ("pk thunder 2", 25),
        ("psi magnet", 4), ("fthrow", 11), ("bthrow", 11), ("uthrow", 10),
        ("dthrow", 6),
    ],
    "olimar": [
        ("ftilt", 11), ("utilt", 4.6), ("dtilt", 6), ("dash attack", 7),
        ("jab combo", 8), ("nair", 2), ("fair", 13.6), ("bair", 17.2),
        ("uair", 14.4), ("dair", 14.4), ("pikmin throw", 6), ("fthrow", 38.5),
        ("bthrow", 49.5), ("uthrow", 43.9), ("dthrow", 43.9),
    ],
    "pac-man": [
        ("ftilt", 8), ("utilt", 6.5), ("dtilt", 6), ("dash attack", 6),
        ("fsmash", 16), ("usmash", 17), ("dsmash", 13), ("jab combo", 8),
        ("nair", 10), ("fair", 7.6), ("bair", 11.8), ("uair", 10),
        ("dair", 9), ("bonus fruit, throw", 71.8), ("power pellet (travel | dash", 21), ("pac-jump", 15),
        ("fire hydrant", 13), ("fthrow", 8), ("bthrow", 11), ("uthrow", 5),
        ("dthrow", 7.5),
    ],
    "palutena": [
        ("ftilt", 7), ("utilt", 2.5), ("dtilt", 8.5), ("dash attack", 11),
        ("fsmash", 16), ("usmash", 16), ("dsmash", 15), ("jab", 3),
        ("nair", 6.4), ("fair", 10), ("bair", 12), ("uair", 6),
        ("dair", 11), ("autoreticle", 3.5), ("explosive flame", 7), ("fthrow", 9),
        ("bthrow", 10), ("uthrow", 8), ("dthrow", 5),
    ],
    "peach": [
        ("ftilt", 8), ("utilt", 10), ("dtilt", 7), ("dash attack", 6),
        ("fsmash", 18), ("usmash", 17), ("dsmash", 3), ("jab combo", 5),
        ("nair", 13), ("fair", 15), ("bair", 12), ("uair", 6),
        ("dair", 7), ("peach bomber", 12), ("peach bomber, air", 12), ("peach parasol", 8),
        ("turnip pull", 35.9), ("fthrow", 8), ("bthrow", 11), ("uthrow", 8),
        ("dthrow", 8),
    ],
    "pichu": [
        ("ftilt", 8), ("utilt", 5), ("dtilt", 6), ("dash attack", 8),
        ("fsmash", 10), ("usmash", 14), ("dsmash", 9.5), ("jab", 1.2),
        ("nair", 7), ("fair", 3.5), ("bair", 2.5), ("uair", 4),
        ("dair", 29), ("thunderjolt", 10), ("skull bash", 37), ("thunder", 18),
        ("fthrow", 7.5), ("bthrow", 9), ("uthrow", 10), ("dthrow", 8),
    ],
    "pikachu": [
        ("ftilt", 10), ("utilt", 5), ("dtilt", 6), ("dash attack", 11),
        ("fsmash", 18), ("usmash", 14), ("dsmash", 3), ("jab", 1.4),
        ("nair", 5.2), ("fair", 6.1), ("bair", 8.5), ("uair", 6),
        ("dair", 29), ("thunderjolt", 6), ("skull bash", 21.4), ("quick attack", 3),
        ("thunder", 15), ("fthrow", 4), ("bthrow", 9), ("uthrow", 8),
        ("dthrow", 5),
    ],
    "piranha plant": [
        ("utilt", 9), ("dtilt", 7), ("dash attack", 10), ("fsmash", 19),
        ("usmash", 15), ("dsmash", 14), ("jab combo", 9), ("nair", 3),
        ("fair", 11), ("bair", 14.5), ("uair", 8), ("dair", 11),
        ("ptooie", 18), ("piranhacopter", 5.2), ("long stem strike", 34.4), ("footstool attack", 4),
    ],
    "pit": [
        ("ftilt", 10), ("utilt", 5), ("dtilt", 6), ("dash attack", 11),
        ("fsmash", 10), ("usmash", 13), ("dsmash", 12), ("jab combo", 8),
        ("nair", 5.2), ("fair", 8.5), ("bair", 12), ("uair", 6.5),
        ("dair", 10), ("palutena's bow", 11.8), ("upperdash arm", 11), ("upperdash arm, air", 9),
        ("fthrow", 10), ("bthrow", 8), ("uthrow", 11), ("dthrow", 6),
    ],
    "pokemon trainer": [
        ("ftilt (sq)", 5), ("utilt (sq)", 5), ("dtilt (sq)", 9), ("dash attack (sq)", 8),
        ("fsmash (sq)", 15), ("usmash (sq)", 26), ("dsmash (sq)", 13), ("jab combo (sq)", 7.5),
        ("nair (sq)", 10), ("fair (sq)", 7), ("bair (sq)", 9), ("uair (sq)", 7),
        ("dair (sq)", 5.5), ("withdraw (sq)", 13.9), ("waterfall (sq)", 4.3), ("fthrow (sq)", 8),
        ("bthrow (sq)", 8), ("uthrow (sq)", 7), ("dthrow (sq)", 7), ("ftilt (ivy)", 2),
        ("utilt (ivy)", 7), ("dtilt (ivy)", 5.5), ("dash attack (ivy)", 12), ("fsmash (ivy)", 16),
        ("usmash (ivy)", 17), ("dsmash (ivy)", 12), ("jab combo (ivy)", 4), ("nair (ivy)", 3),
        ("fair (ivy)", 12), ("bair (ivy)", 6), ("uair (ivy)", 15), ("dair (ivy)", 10),
        ("bullet seed (ivy)", 8.8), ("razor leaf (ivy)", 8), ("vinewhip (ivy)", 13), ("fthrow (ivy)", 10),
        ("bthrow (ivy)", 12), ("uthrow (ivy)", 9), ("dthrow (ivy)", 7), ("ftilt (char)", 11),
        ("utilt (char)", 8), ("dtilt (char)", 10), ("dash attack (char)", 13), ("fsmash (char)", 19),
        ("usmash (char)", 16), ("dsmash (char)", 16), ("jab combo (char)", 10), ("nair (char)", 12),
        ("fair (char)", 13), ("bair (char)", 16), ("uair (char)", 13), ("dair (char)", 14),
        ("flamethrower (char)", 2), ("flare blitz (char)", 24), ("fly (char)", 5), ("fthrow (char)", 10),
        ("bthrow (char)", 10), ("uthrow (char)", 11), ("dthrow (char)", 1),
    ],
    "pyra": [
        ("jab combo", 9), ("ftilt", 13), ("utilt", 10), ("dtilt", 10),
        ("dash attack", 14), ("fsmash", 22), ("usmash", 19), ("dsmash", 17),
        ("nair", 11), ("fair", 14), ("bair", 16), ("uair", 11),
        ("dair", 14), ("flame nova", 10), ("blazing end", 16), ("prominence revolt", 17),
        ("fthrow", 8), ("bthrow", 9), ("uthrow", 8), ("dthrow", 5),
    ],
    "richter": [
        ("ftilt", 12), ("utilt", 10), ("dash attack", 3.5), ("fsmash", 18),
        ("usmash", 16), ("jab combo", 4), ("nair", 5), ("fair", 24),
        ("bair", 24), ("uair", 24), ("dair", 12), ("axe", 15),
        ("cross", 8), ("uppercut", 9.5), ("holy water", 2.9), ("holy water explosion", 1.4),
        ("fthrow", 7), ("bthrow", 7), ("uthrow", 10), ("dthrow", 8),
    ],
    "ridley": [
        ("ftilt", 13), ("utilt", 9), ("dtilt", 9), ("dash attack", 12),
        ("fsmash", 20), ("usmash", 17), ("dsmash", 16), ("jab combo", 8.5),
        ("nair", 12), ("fair", 7), ("bair", 16), ("uair", 14),
        ("dair", 14), ("plasma breath", 4.5), ("wing blitz", 16),
    ],
    "rob": [
        ("ftilt", 8), ("utilt", 5), ("dtilt", 5), ("dash attack", 7),
        ("fsmash", 15), ("usmash", 17), ("dsmash", 5), ("jab combo", 6),
        ("nair", 9.5), ("fair", 7), ("bair", 15), ("uair", 5.5),
        ("dair", 12), ("robo beam", 22), ("arm rotor", 4.5), ("arm rotor, mashing", 4.5),
        ("gyro", 25), ("fthrow", 8), ("bthrow", 10), ("uthrow", 12),
        ("dthrow", 5),
    ],
    "robin": [
        ("ftilt", 7.5), ("utilt", 7.5), ("dtilt", 6), ("dash attack", 10),
        ("fsmash", 16), ("usmash", 15), ("dsmash", 15), ("jab combo", 8.5),
        ("nair", 11.5), ("fair", 12.5), ("bair", 15), ("uair", 13),
        ("dair", 11), ("thunder/elthunder/arcthunder", 11), ("vortex", 16.4), ("thoron", 2.6),
        ("arcfire", 7.3), ("elwind", 7), ("fthrow", 8), ("bthrow", 11),
        ("uthrow", 9), ("dthrow", 6),
    ],
    "rosalina": [
        ("ftilt", 7.5), ("utilt", 10), ("dtilt", 5.5), ("dash attack", 4),
        ("fsmash", 12), ("usmash", 12), ("dsmash", 9), ("jab combo", 33),
        ("nair", 10), ("fair", 5), ("bair", 11), ("uair", 10),
        ("dair", 8), ("luma shot", 21), ("star bits", 3), ("fthrow", 9),
        ("bthrow", 11), ("uthrow", 7), ("dthrow", 9),
    ],
    "roy": [
        ("ftilt", 12.5), ("utilt", 12), ("dtilt", 11), ("dash attack", 13),
        ("fsmash", 20), ("usmash", 13), ("dsmash", 17), ("jab", 7.5),
        ("nair", 23.5), ("fair", 11), ("bair", 12), ("uair", 9),
        ("dair", 15), ("flare blade", 58), ("double edged dance", 3), ("double edged dance neutral", 13),
        ("double edged dance up", 14), ("double edged dance down", 11), ("blazer", 14.6), ("fthrow", 5),
        ("bthrow", 5), ("uthrow", 6), ("dthrow", 5),
    ],
    "ryu": [
        ("dash attack", 12), ("fsmash", 17.5), ("usmash", 17), ("dsmash", 16),
        ("jab combo", 30), ("nair", 8), ("fair", 14), ("bair", 16),
        ("uair", 6), ("dair", 12), ("hadouken", 8.7), ("shakunetsu hadouken", 6.1),
        ("tatsumaki senpukyaku", 12.7), ("tatsumaki senpukyaku, air", 11.6), ("shoryuken", 15), ("true shoryuken", 18),
        ("focus attack", 17), ("fthrow", 9), ("bthrow", 12), ("uthrow", 8),
        ("dthrow", 9),
    ],
    "samus": [
        ("ftilt", 10), ("utilt", 13), ("dtilt", 12), ("dash attack", 10),
        ("fsmash", 14), ("usmash", 9), ("dsmash", 12), ("jab combo", 11),
        ("nair", 10), ("fair", 9.6), ("bair", 14), ("uair", 8.2),
        ("dair", 14), ("charge shot", 31.1), ("charge shot, full charge", 28), ("homing missle", 8),
        ("super missle", 12), ("screw attack", 6), ("screw attack, air", 1), ("bomb", 5),
        ("fthrow", 10), ("bthrow", 10), ("uthrow", 12), ("dthrow", 8),
    ],
    "sheik": [
        ("ftilt", 3), ("utilt", 4), ("dtilt", 4.5), ("dash attack", 7),
        ("fsmash", 8), ("usmash", 15), ("dsmash", 6), ("jab combo", 3.6),
        ("nair", 6), ("fair", 4.5), ("bair", 7.5), ("uair", 5),
        ("dair", 12), ("needle storm", 1.5), ("needle storm, full charge", 1.5), ("burst grenade", 13.6),
        ("vanish", 12), ("bouncing fish", 11), ("fthrow", 7), ("bthrow", 7),
        ("uthrow", 6), ("dthrow", 6),
    ],
    "shulk": [
        ("ftilt", 13.5), ("utilt", 10), ("dtilt", 9.5), ("dash attack", 12.5),
        ("fsmash", 30), ("usmash", 18), ("dsmash", 89), ("jab combo", 8.5),
        ("nair", 8.5), ("fair", 8), ("bair", 12.5), ("uair", 10.5),
        ("dair", 11.5), ("back slash", 16), ("air slash", 6), ("air slash 2", 5.5),
        ("fthrow", 8), ("bthrow", 9), ("uthrow", 7), ("dthrow", 5.5),
    ],
    "simon": [
        ("ftilt", 12), ("utilt", 10), ("dash attack", 3.5), ("fsmash", 18),
        ("usmash", 16), ("jab combo", 4), ("nair", 5), ("fair", 24),
        ("bair", 24), ("uair", 24), ("dair", 12), ("axe", 15),
        ("cross", 8), ("uppercut", 9.5), ("holy water", 2.9), ("holy water explosion", 1.4),
        ("fthrow", 7), ("bthrow", 7), ("uthrow", 10), ("dthrow", 8),
    ],
    "snake": [
        ("utilt", 14.5), ("dtilt", 12), ("dash attack", 11), ("fsmash", 22),
        ("usmash", 18), ("dsmash", 14), ("jab combo", 11), ("nair", 15),
        ("fair", 15), ("bair", 16), ("uair", 14), ("dair", 17),
        ("neutral throw, smash throw, underhand throw", 23.9), ("nikita", 14), ("cypher", 6), ("c4 detonate/explosion", 17),
        ("fthrow", 9), ("bthrow", 9), ("uthrow", 11), ("dthrow", 9),
    ],
    "sonic": [
        ("ftilt", 7), ("utilt", 8), ("dtilt", 6), ("dash attack", 6),
        ("fsmash", 14), ("usmash", 8), ("dsmash", 12), ("jab combo", 7.5),
        ("nair", 12), ("fair", 3.8), ("bair", 14), ("uair", 11),
        ("dair", 8), ("homing attack", 27), ("spin dash", 10.9), ("spring jump", 4),
        ("spin charge", 8.2), ("spin dash/spin charge, jump", 6), ("fthrow", 7), ("bthrow", 7),
        ("uthrow", 6), ("dthrow", 6),
    ],
    "terry": [
        ("ftilt", 13), ("utilt", 11), ("dtilt", 3), ("dash attack", 13),
        ("fsmash", 18), ("usmash", 18), ("dsmash", 12), ("jab combo", 11),
        ("nair", 7), ("fair", 11), ("bair", 15), ("uair", 5),
        ("dair", 17), ("power wave, ground", 8), ("power wave, air", 10), ("burning knuckle", 13),
        ("burning knuckle, input", 16), ("crack shoot", 15), ("rising tackle", 20.3), ("charged input", 22.8),
        ("power dunk", 29), ("power geyser", 26), ("buster wolf", 25), ("fthrow", 10),
        ("bthrow", 10), ("uthrow", 6), ("dthrow", 8),
    ],
    "toon link": [
        ("ftilt", 9), ("utilt", 5), ("dtilt", 7), ("dash attack", 8),
        ("fsmash", 14), ("usmash", 13), ("dsmash", 13), ("jab combo", 8),
        ("nair", 8.5), ("fair", 13), ("bair", 8), ("uair", 14),
        ("dair", 16), ("hero's bow", 16), ("boomerang", 17.6), ("spin attack", 4),
        ("spin attack, air", 10), ("fthrow", 7), ("bthrow", 7), ("uthrow", 7),
        ("dthrow", 7),
    ],
    "villager": [
        ("ftilt", 9), ("utilt", 6), ("dtilt", 12), ("dash attack", 10),
        ("fsmash", 17), ("usmash", 8), ("dsmash", 6), ("jab combo", 2),
        ("nair", 9), ("fair", 7), ("bair", 9), ("uair", 13),
        ("dair", 13), ("lloid rocket", 7), ("timber tree grow/fall", 25), ("timber axe", 14),
        ("fthrow", 9), ("bthrow", 11), ("uthrow", 10), ("dthrow", 6),
    ],
    "wario": [
        ("ftilt", 13), ("utilt", 6), ("dtilt", 4), ("dash attack", 11),
        ("fsmash", 20), ("usmash", 17), ("dsmash", 13), ("jab combo", 9),
        ("nair", 6), ("fair", 7), ("bair", 12), ("uair", 13),
        ("dair", 5.3), ("wario bike", 12), ("wario bike, wheelie", 18), ("wario bike, turnaround", 7),
        ("corkscrew", 10), ("wario waft", 79), ("fthrow", 12), ("bthrow", 7),
        ("uthrow", 8), ("dthrow", 11),
    ],
    "wii fit trainer": [
        ("ftilt", 11), ("utilt", 10), ("dtilt", 13.5), ("dash attack", 10),
        ("fsmash", 15.5), ("usmash", 18), ("dsmash", 12), ("jab combo", 7),
        ("nair", 9), ("fair", 12), ("bair", 13.5), ("uair", 10),
        ("dair", 13), ("sun salutation", 25.7), ("sun salutation, full charge", 21), ("header", 15),
        ("super hoop", 5), ("fthrow", 10), ("bthrow", 9), ("uthrow", 8),
        ("dthrow", 7),
    ],
    "wolf": [
        ("ftilt", 6), ("utilt", 10), ("dtilt", 6), ("dash attack", 11),
        ("fsmash", 15), ("usmash", 12), ("dsmash", 16), ("jab combo", 8),
        ("nair", 12), ("fair", 9), ("bair", 15), ("uair", 12),
        ("dair", 15), ("blaster", 7), ("wolf flash", 15), ("fire wolf", 11.5),
        ("reflector", 4), ("fthrow", 9), ("bthrow", 11), ("uthrow", 7),
        ("dthrow", 8.5),
    ],
    "yoshi": [
        ("ftilt", 8), ("utilt", 7), ("dtilt", 5), ("dash attack", 11),
        ("fsmash", 15.5), ("usmash", 14), ("dsmash", 12), ("jab combo", 7),
        ("nair", 10), ("fair", 15), ("bair", 5.5), ("uair", 12),
        ("dair", 7.8), ("egg roll", 12.8), ("egg throw", 6), ("yoshi bomb, yoshi bomb air", 39),
        ("fthrow", 9), ("bthrow", 9), ("uthrow", 5), ("dthrow", 4),
    ],
    "young link": [
        ("ftilt", 12), ("utilt", 8), ("dtilt", 10), ("dash attack", 11),
        ("usmash", 11), ("dsmash", 13), ("jab combo", 7), ("nair", 10),
        ("fair", 8), ("bair", 7), ("uair", 12), ("dair", 18),
        ("fire arrow", 16), ("boomerang", 16), ("spin attack", 4), ("fthrow", 6),
        ("bthrow", 6), ("uthrow", 6), ("dthrow", 6),
    ],
    "zelda": [
        ("ftilt", 12), ("utilt", 7.2), ("dtilt", 5.5), ("dash attack", 12),
        ("fsmash", 14), ("usmash", 7.8), ("dsmash", 12), ("jab", 2.5),
        ("nair", 5), ("fair", 20), ("bair", 20), ("uair", 17),
        ("dair", 20), ("nayru's love", 5), ("din's fire", 17.5), ("farore's wind", 18),
        ("phantom slash", 18.8), ("fthrow", 10), ("bthrow", 12), ("uthrow", 11),
        ("dthrow", 3.5),
    ],
    "zero suit samus": [
        ("ftilt", 8), ("utilt", 7), ("dtilt", 8), ("dash attack", 8),
        ("fsmash", 27), ("usmash", 7.8), ("dsmash", 8), ("jab combo", 6),
        ("nair", 8), ("fair", 7), ("bair", 12), ("uair", 6.5),
        ("dair", 5.5), ("paralyzer", 6), ("plasma whip", 11.2), ("boost kick", 10.3),
        ("flip jump", 8), ("flip jump, kick", 14), ("fthrow", 9), ("bthrow", 8),
        ("uthrow", 10), ("dthrow", 8),
    ],
}



_AERIAL_NAMES = {"nair", "fair", "fair spike", "bair", "uair", "dair"}
_GROUND_NAMES = {
    "jab", "jab combo", "ftilt", "utilt", "dtilt", "dash attack",
    "fsmash", "usmash", "dsmash",
}
_THROW_NAMES = {"fthrow", "bthrow", "uthrow", "dthrow"}


def _get_1v1_moves(character: str):
    """Get a character's moves with 1v1-adjusted damage values."""
    char_key = character.strip().lower()
    base_moves = MOVE_DAMAGE.get(char_key)
    if not base_moves:
        return None
    return [(name, round(dmg * _1V1_MULTIPLIER, 1)) for name, dmg in base_moves]


def get_move_reference(character: str) -> str:
    """
    Format a character's move damage table as text for inclusion in a vision prompt.
    Returns empty string if character not in database.
    Damage values are 1v1-adjusted (1.2x base).
    """
    if not character:
        return ""

    moves = _get_1v1_moves(character)
    if not moves:
        return ""

    ground = [(n, d) for n, d in moves if n in _GROUND_NAMES]
    aerials = [(n, d) for n, d in moves if n in _AERIAL_NAMES]
    specials = [(n, d) for n, d in moves if n not in _GROUND_NAMES | _AERIAL_NAMES | _THROW_NAMES]
    throws = [(n, d) for n, d in moves if n in _THROW_NAMES]

    lines = [f"{character.title()} move damage (1v1, fresh — stale moves deal ~10% less, rage adds up to ~15% at high percent):"]
    if ground:
        lines.append("  Ground: " + ", ".join(f"{n} ({d}%)" for n, d in ground))
    if aerials:
        lines.append("  Aerials: " + ", ".join(f"{n} ({d}%)" for n, d in aerials))
    if specials:
        lines.append("  Specials: " + ", ".join(f"{n} ({d}%)" for n, d in specials))
    if throws:
        lines.append("  Throws: " + ", ".join(f"{n} ({d}%)" for n, d in throws))

    return "\n".join(lines)


def get_candidate_moves(character: str, damage: float, tolerance: float = 2.5,
                        attacker_percent: float = 0) -> list:
    """
    Given a damage delta, return moves that could have dealt that damage.
    Uses 1v1-adjusted values (1.2x base).
    Accounts for staling (~10% reduction) and rage (~1-1.15x scaling based on attacker percent).
    Returns candidates sorted by closeness to observed damage (best match first).
    """
    if not character or damage <= 0:
        return []

    moves = _get_1v1_moves(character)
    if not moves:
        return []

    # Rage multiplier: 1.0 at 0%, up to ~1.15 at 150%+
    rage_mult = 1.0 + min(0.15, max(0, attacker_percent) / 150 * 0.15)

    # Match window: stale (no rage) to fresh * rage_mult
    candidates = []
    for name, fresh_1v1 in moves:
        stale_dmg = fresh_1v1 * 0.9  # staling floor
        raged_dmg = fresh_1v1 * rage_mult  # rage ceiling
        if stale_dmg - tolerance <= damage <= raged_dmg + tolerance:
            # Score by closeness — midpoint of stale..raged range vs observed
            midpoint = (stale_dmg + raged_dmg) / 2
            closeness = abs(damage - midpoint)
            candidates.append((name, fresh_1v1, closeness))

    # Sort by closeness, return top 6 max to avoid overwhelming the prompt
    candidates.sort(key=lambda c: c[2])
    return [(name, dmg) for name, dmg, _ in candidates[:6]]


def identify_best_move(character: str, damage: float, attacker_percent: float = 0,
                       context: str = None) -> tuple:
    """
    Pick the single best move match for an observed damage delta.
    Uses damage matching + context hints (aerial vs grounded, combo vs kill).

    Args:
        character: Character name
        damage: Observed damage dealt
        attacker_percent: Attacker's percent (for rage calculation)
        context: Optional hint — "aerial", "grounded", "combo", "kill", "edgeguard"

    Returns:
        (move_name, base_1v1_damage, confidence) or ("unknown", damage, 0.0)
        confidence: 0.0-1.0 indicating how sure the match is
    """
    candidates = get_candidate_moves(character, damage, attacker_percent=attacker_percent)
    if not candidates:
        return ("unknown", damage, 0.0)

    if len(candidates) == 1:
        name, dmg = candidates[0]
        return (name, dmg, 0.9)

    # Score candidates with context hints
    scored = []
    for name, dmg in candidates:
        score = 0.0
        # Closeness to observed damage (primary signal)
        rage_mult = 1.0 + min(0.15, max(0, attacker_percent) / 150 * 0.15)
        expected = dmg * (0.95 + rage_mult) / 2  # midpoint of stale..raged
        closeness = 1.0 - min(1.0, abs(damage - expected) / max(damage, 1))
        score += closeness * 10

        # Context bonuses
        is_aerial = name in _AERIAL_NAMES
        is_ground = name in _GROUND_NAMES
        is_special = name not in _AERIAL_NAMES | _GROUND_NAMES | _THROW_NAMES
        is_smash = "smash" in name

        if context == "aerial" and is_aerial:
            score += 3
        elif context == "grounded" and is_ground:
            score += 3
        elif context == "combo" and (is_aerial or name in ("dtilt", "utilt", "ftilt", "dash attack")):
            score += 2  # combo starters/extenders are usually aerials or tilts
            if is_smash:
                score -= 3  # smash attacks don't combo
        elif context == "kill" and (is_smash or is_special or name in ("bair", "fair", "uair")):
            score += 2
        elif context == "edgeguard" and (is_aerial or is_special):
            score += 2

        scored.append((name, dmg, score))

    scored.sort(key=lambda x: -x[2])
    best_name, best_dmg, best_score = scored[0]
    second_score = scored[1][2] if len(scored) > 1 else 0

    # Confidence based on gap between best and second
    gap = best_score - second_score
    confidence = min(0.9, 0.4 + gap * 0.1)

    return (best_name, best_dmg, confidence)


def compute_damage_context(game_states, frame_times, you_are_p1=True):
    """
    Compute damage deltas between consecutive frame times using game_states.

    Returns list of dicts:
        [{from_time, to_time, your_pct_before, your_pct_after, opp_pct_before, opp_pct_after,
          damage_taken, damage_dealt}]
    """
    if not game_states or len(frame_times) < 2:
        return []

    def nearest_state(t):
        return min(game_states, key=lambda s: abs(s["timestamp"] - t))

    deltas = []
    for i in range(len(frame_times) - 1):
        s0 = nearest_state(frame_times[i])
        s1 = nearest_state(frame_times[i + 1])

        if you_are_p1:
            your_before, your_after = s0["p1_percent"], s1["p1_percent"]
            opp_before, opp_after = s0["p2_percent"], s1["p2_percent"]
        else:
            your_before, your_after = s0["p2_percent"], s1["p2_percent"]
            opp_before, opp_after = s0["p1_percent"], s1["p1_percent"]

        dmg_taken = max(0, your_after - your_before)
        dmg_dealt = max(0, opp_after - opp_before)

        # Only include if something happened
        if dmg_taken > 0 or dmg_dealt > 0:
            deltas.append({
                "from_time": frame_times[i],
                "to_time": frame_times[i + 1],
                "your_pct_before": your_before,
                "your_pct_after": your_after,
                "opp_pct_before": opp_before,
                "opp_pct_after": opp_after,
                "damage_taken": round(dmg_taken, 1),
                "damage_dealt": round(dmg_dealt, 1),
            })

    return deltas


def format_damage_deltas_for_prompt(
    deltas, player_char=None, opponent_char=None, event_type=None
):
    """
    Format damage deltas with identified moves as assertions for the vision prompt.
    Instead of listing candidates, picks the best match and states it as fact.
    """
    if not deltas:
        return ""

    # Map event types to context hints for move identification
    context_map = {
        "combo": "combo",
        "edgeguard": "edgeguard",
        "stock_taken": "kill",
        "stock_lost": "kill",
        "damage_taken": None,
        "damage_dealt": None,
    }
    context = context_map.get(event_type)

    lines = ["WHAT HAPPENED (from verified game data):"]

    for d in deltas:
        time_range = f"t={d['from_time']:.1f}s-{d['to_time']:.1f}s"

        if d["damage_dealt"] > 0 and player_char:
            move, base_dmg, conf = identify_best_move(
                player_char, d["damage_dealt"],
                attacker_percent=d["your_pct_before"],
                context=context,
            )
            if move != "unknown":
                qualifier = "" if conf >= 0.7 else " (likely)"
                lines.append(
                    f"  {time_range}: {player_char} hit with {move}{qualifier} "
                    f"— dealt {d['damage_dealt']}% "
                    f"(opponent: {d['opp_pct_before']}% → {d['opp_pct_after']}%)"
                )
            else:
                lines.append(
                    f"  {time_range}: {player_char} dealt {d['damage_dealt']}% "
                    f"(opponent: {d['opp_pct_before']}% → {d['opp_pct_after']}%)"
                )

        if d["damage_taken"] > 0 and opponent_char:
            move, base_dmg, conf = identify_best_move(
                opponent_char, d["damage_taken"],
                attacker_percent=d["opp_pct_before"],
                context=context,
            )
            if move != "unknown":
                qualifier = "" if conf >= 0.7 else " (likely)"
                lines.append(
                    f"  {time_range}: {opponent_char} hit with {move}{qualifier} "
                    f"— you took {d['damage_taken']}% "
                    f"(you: {d['your_pct_before']}% → {d['your_pct_after']}%)"
                )
            else:
                lines.append(
                    f"  {time_range}: You took {d['damage_taken']}% from {opponent_char} "
                    f"(you: {d['your_pct_before']}% → {d['your_pct_after']}%)"
                )

    return "\n".join(lines)

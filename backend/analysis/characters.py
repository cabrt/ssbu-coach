# Character-specific knowledge for Smash Ultimate coaching
# Complete roster with tips for all 89 fighters

CHARACTER_DATA = {
    # Original 8
    "mario": {
        "name": "Mario",
        "archetype": "all-rounder",
        "strengths": ["combo game", "edgeguarding", "frame data"],
        "weaknesses": ["range", "kill power", "recovery distance"],
        "key_moves": {"neutral": ["fireball", "fair", "nair"], "kill": ["fsmash", "up-b oos", "bair"], "combo_starters": ["up-tilt", "down-throw", "up-air"]},
        "tips_as": ["Up-tilt chains at low percent", "Up-B out of shield is frame 3", "Use fireballs to control neutral"],
        "tips_against": ["Respect up-B out of shield", "Don't get grabbed at low percent", "Outrange him"]
    },
    "donkey kong": {
        "name": "Donkey Kong",
        "archetype": "super heavyweight",
        "strengths": ["kill power", "cargo throw", "armor"],
        "weaknesses": ["recovery", "disadvantage", "speed"],
        "key_moves": {"neutral": ["bair", "fair", "hand slap"], "kill": ["fsmash", "cargo throw", "giant punch"], "combo_starters": ["cargo throw", "up-air", "down-tilt"]},
        "tips_as": ["Cargo throw to stage spike or up throw kills", "Bair is your best move", "Giant punch armor through attacks"],
        "tips_against": ["Juggle him - he's combo food", "Edgeguard aggressively", "Don't get grabbed near ledge"]
    },
    "link": {
        "name": "Link",
        "archetype": "zoner",
        "strengths": ["projectiles", "range", "kill power"],
        "weaknesses": ["speed", "recovery", "disadvantage"],
        "key_moves": {"neutral": ["bomb", "boomerang", "fair"], "kill": ["fsmash", "bair", "up-smash"], "combo_starters": ["bomb", "nair", "boomerang"]},
        "tips_as": ["Remote bomb is your best tool", "Z-drop bomb into aerials kills", "Boomerang controls space"],
        "tips_against": ["Catch his boomerang", "Rush him between projectiles", "Edgeguard his linear recovery"]
    },
    "samus": {
        "name": "Samus",
        "archetype": "zoner",
        "strengths": ["projectiles", "range", "kill power"],
        "weaknesses": ["speed", "disadvantage", "close range"],
        "key_moves": {"neutral": ["charge shot", "missile", "fair"], "kill": ["charge shot", "fsmash", "bair"], "combo_starters": ["nair", "down-throw", "bomb"]},
        "tips_as": ["Always have charge shot ready", "Zone with missiles", "Fair walls out approaches"],
        "tips_against": ["Get in close", "Bait charge shot", "Pressure her disadvantage"]
    },
    "dark samus": {
        "name": "Dark Samus",
        "archetype": "zoner",
        "strengths": ["projectiles", "range", "floaty"],
        "weaknesses": ["speed", "disadvantage", "close range"],
        "key_moves": {"neutral": ["charge shot", "missile", "fair"], "kill": ["charge shot", "fsmash", "bair"], "combo_starters": ["nair", "down-throw", "bomb"]},
        "tips_as": ["Slightly floatier than Samus", "Roll covers more distance", "Same gameplan as Samus"],
        "tips_against": ["Same as Samus", "Get in close", "Exploit disadvantage"]
    },
    "yoshi": {
        "name": "Yoshi",
        "archetype": "all-rounder",
        "strengths": ["air speed", "armor on double jump", "combo game"],
        "weaknesses": ["no recovery mixups", "grab game", "kill confirms"],
        "key_moves": {"neutral": ["egg throw", "nair", "fair"], "kill": ["fsmash", "dair", "up-smash"], "combo_starters": ["nair", "down-tilt", "egg throw"]},
        "tips_as": ["Double jump armor lets you escape combos", "Egg throw for neutral control", "Nair is your bread and butter"],
        "tips_against": ["He can't snap to ledge easily", "Respect double jump armor", "Grab beats his shield"]
    },
    "kirby": {
        "name": "Kirby",
        "archetype": "bait-and-punish",
        "strengths": ["edgeguarding", "crouch", "combos"],
        "weaknesses": ["range", "speed", "approach"],
        "key_moves": {"neutral": ["fair", "bair", "dtilt"], "kill": ["fsmash", "hammer", "dair"], "combo_starters": ["uptilt", "fair", "nair"]},
        "tips_as": ["Crouch under attacks", "Up-tilt chains into itself", "Go deep for edgeguards"],
        "tips_against": ["Outrange him", "Watch for inhale at ledge", "He's light - kill early"]
    },
    "fox": {
        "name": "Fox",
        "archetype": "rushdown",
        "strengths": ["speed", "combos", "frame data"],
        "weaknesses": ["light weight", "recovery", "kill power"],
        "key_moves": {"neutral": ["laser", "nair", "bair"], "kill": ["up-smash", "up-air", "bair"], "combo_starters": ["nair", "up-tilt", "down-throw"]},
        "tips_as": ["Laser for chip damage", "Up-tilt combos into itself", "Nair is incredibly versatile"],
        "tips_against": ["Fox dies early", "Crouch under lasers", "Edgeguard his linear recovery"]
    },
    "pikachu": {
        "name": "Pikachu",
        "archetype": "rushdown",
        "strengths": ["recovery", "combos", "edgeguarding"],
        "weaknesses": ["light weight", "kill power", "range"],
        "key_moves": {"neutral": ["tjolt", "nair", "fair"], "kill": ["thunder", "bair", "up-smash"], "combo_starters": ["nair loops", "down-throw", "up-air"]},
        "tips_as": ["Tjolt controls neutral", "Nair loops deal massive damage", "Recovery is incredible - go deep"],
        "tips_against": ["Pikachu is light", "Be patient edgeguarding", "Watch for nair loops"]
    },
    "luigi": {
        "name": "Luigi",
        "archetype": "grappler",
        "strengths": ["grab combos", "kill power", "frame data"],
        "weaknesses": ["neutral", "recovery", "approach"],
        "key_moves": {"neutral": ["fireball", "nair", "down-b"], "kill": ["grab combos", "up-b", "fsmash"], "combo_starters": ["grab", "down-tilt", "nair"]},
        "tips_as": ["Grab is your best friend", "0-death combos off grab", "Misfire can kill early"],
        "tips_against": ["Don't get grabbed", "Exploit his bad recovery", "Camp him out"]
    },
    "ness": {
        "name": "Ness",
        "archetype": "bait-and-punish",
        "strengths": ["aerials", "pk fire", "kill power"],
        "weaknesses": ["recovery", "disadvantage", "juggling"],
        "key_moves": {"neutral": ["pk fire", "fair", "bair"], "kill": ["bair", "pk thunder 2", "fsmash"], "combo_starters": ["down-throw", "pk fire", "nair"]},
        "tips_as": ["PK fire for traps", "Bair is your best kill move", "Magnet stalls and heals"],
        "tips_against": ["Hit pk thunder to gimp him", "Don't get stuck in pk fire", "Juggle him"]
    },
    "captain falcon": {
        "name": "Captain Falcon",
        "archetype": "rushdown",
        "strengths": ["speed", "combos", "hype factor"],
        "weaknesses": ["recovery", "range", "disadvantage"],
        "key_moves": {"neutral": ["nair", "bair", "raptor boost"], "kill": ["knee", "falcon punch", "up-air"], "combo_starters": ["nair", "down-throw", "raptor boost"]},
        "tips_as": ["Nair into knee is the dream", "Raptor boost through projectiles", "Down throw combos at low percent"],
        "tips_against": ["Edgeguard him", "Don't let him land", "Watch for grab at low percent"]
    },
    "jigglypuff": {
        "name": "Jigglypuff",
        "archetype": "bait-and-punish",
        "strengths": ["air mobility", "rest", "edgeguarding"],
        "weaknesses": ["lightest in the game", "range", "shield break death"],
        "key_moves": {"neutral": ["pound", "fair", "bair"], "kill": ["rest", "bair", "fsmash"], "combo_starters": ["up-air", "fair", "pound"]},
        "tips_as": ["Wall of pain with bair", "Rest off of sing or up-throw", "Never shield too much"],
        "tips_against": ["She dies at 60%", "Crouch rest", "Break her shield for free KO"]
    },
    "peach": {
        "name": "Peach",
        "archetype": "technical",
        "strengths": ["float aerials", "combos", "turnip"],
        "weaknesses": ["recovery distance", "kill confirms", "complex execution"],
        "key_moves": {"neutral": ["turnip", "float fair", "float nair"], "kill": ["fsmash", "bair", "bob-omb"], "combo_starters": ["float nair", "down-tilt", "turnip"]},
        "tips_as": ["Float cancel aerials are key", "Turnip combos into aerials", "Down-tilt combos at low percent"],
        "tips_against": ["Hit her out of float", "Watch for turnip pulls", "She's light - kill early"]
    },
    "daisy": {
        "name": "Daisy",
        "archetype": "technical",
        "strengths": ["float aerials", "combos", "turnip"],
        "weaknesses": ["recovery distance", "kill confirms", "complex execution"],
        "key_moves": {"neutral": ["turnip", "float fair", "float nair"], "kill": ["fsmash", "bair", "bob-omb"], "combo_starters": ["float nair", "down-tilt", "turnip"]},
        "tips_as": ["Same as Peach", "Slightly different turnip hitbox", "Blue toad is faster"],
        "tips_against": ["Same as Peach", "Float cancel pressure is oppressive", "She's light"]
    },
    "bowser": {
        "name": "Bowser",
        "archetype": "super heavyweight",
        "strengths": ["armor", "kill power", "weight"],
        "weaknesses": ["disadvantage", "combo food", "recovery"],
        "key_moves": {"neutral": ["fire breath", "fair", "bair"], "kill": ["fsmash", "up-b", "command grab"], "combo_starters": ["up-throw", "fair", "up-tilt"]},
        "tips_as": ["Tough guy armor ignores weak hits", "Side-b is a great mixup", "Fire breath racks damage"],
        "tips_against": ["He's huge - combo him", "Edgeguard his up-b", "Don't get command grabbed at ledge"]
    },
    # Melee newcomers
    "ice climbers": {
        "name": "Ice Climbers",
        "archetype": "technical",
        "strengths": ["desync combos", "two characters", "grab game"],
        "weaknesses": ["popo alone is bad", "recovery", "complex execution"],
        "key_moves": {"neutral": ["ice shot", "fair", "nair"], "kill": ["desync combos", "fsmash", "side-b"], "combo_starters": ["grab", "nair", "down-tilt"]},
        "tips_as": ["Desyncs enable 0-deaths", "Protect Nana at all costs", "Blizzard at ledge is strong"],
        "tips_against": ["Separate them - kill Nana", "Popo alone is free", "Edgeguard them"]
    },
    "sheik": {
        "name": "Sheik",
        "archetype": "rushdown",
        "strengths": ["speed", "frame data", "combos"],
        "weaknesses": ["kill power", "damage output", "light"],
        "key_moves": {"neutral": ["needle", "fair", "ftilt"], "kill": ["bouncing fish", "up-air", "bair"], "combo_starters": ["ftilt", "down-throw", "nair"]},
        "tips_as": ["Needles control neutral", "Fair strings into itself", "Bouncing fish for kills"],
        "tips_against": ["She struggles to kill", "Survive to high percent", "Trade hits - you win trades"]
    },
    "zelda": {
        "name": "Zelda",
        "archetype": "zoner",
        "strengths": ["phantom", "kill power", "recovery"],
        "weaknesses": ["speed", "disadvantage", "approach"],
        "key_moves": {"neutral": ["phantom", "fair", "nair"], "kill": ["sweetspot fair/bair", "up-b", "phantom"], "combo_starters": ["down-throw", "nair", "up-tilt"]},
        "tips_as": ["Phantom controls huge space", "Sweetspot fair/bair kill early", "Up-b out of shield"],
        "tips_against": ["Get past phantom", "She's slow - rush her down", "Bait the up-b"]
    },
    "dr. mario": {
        "name": "Dr. Mario",
        "archetype": "all-rounder",
        "strengths": ["kill power", "pill", "simple gameplan"],
        "weaknesses": ["recovery", "speed", "range"],
        "key_moves": {"neutral": ["pill", "fair", "nair"], "kill": ["fsmash", "bair", "up-b"], "combo_starters": ["down-throw", "up-tilt", "nair"]},
        "tips_as": ["Pills are better than fireballs", "Bair kills stupid early", "Cape can reverse recoveries"],
        "tips_against": ["Exploit his terrible recovery", "Outspeed him", "Edgeguard him hard"]
    },
    "pichu": {
        "name": "Pichu",
        "archetype": "glass cannon",
        "strengths": ["speed", "combos", "small hurtbox"],
        "weaknesses": ["self-damage", "lightest ever", "range"],
        "key_moves": {"neutral": ["tjolt", "nair", "fair"], "kill": ["thunder", "fsmash", "up-air"], "combo_starters": ["nair", "up-tilt", "down-throw"]},
        "tips_as": ["You deal damage to yourself", "Nair loops like Pikachu", "Kill early before self-damage adds up"],
        "tips_against": ["Pichu dies at 50%", "Every hit matters more", "One good read ends his stock"]
    },
    "falco": {
        "name": "Falco",
        "archetype": "rushdown",
        "strengths": ["combos", "laser", "juggling"],
        "weaknesses": ["recovery", "disadvantage", "kill confirms"],
        "key_moves": {"neutral": ["laser", "nair", "down-tilt"], "kill": ["bair", "fsmash", "up-smash"], "combo_starters": ["down-throw", "shine", "nair"]},
        "tips_as": ["Laser forces approaches", "Dair combos at low percent", "Up-tilt juggles forever"],
        "tips_against": ["Edgeguard his linear recovery", "Get under his laser", "He struggles to land"]
    },
    "marth": {
        "name": "Marth",
        "archetype": "swordie",
        "strengths": ["tipper kills", "range", "edgeguarding"],
        "weaknesses": ["inconsistent", "sourspots", "requires spacing"],
        "key_moves": {"neutral": ["fair", "nair", "dtilt"], "kill": ["tipper fsmash", "tipper fair", "shield breaker"], "combo_starters": ["nair", "dtilt", "dancing blade"]},
        "tips_as": ["Space for tippers", "Fair walls out opponents", "Shield breaker punishes rolls"],
        "tips_against": ["Get inside tipper range", "Sourspots are weak", "His moves are committal"]
    },
    "lucina": {
        "name": "Lucina",
        "archetype": "swordie",
        "strengths": ["consistency", "range", "simplicity"],
        "weaknesses": ["no early kills", "linear", "predictable"],
        "key_moves": {"neutral": ["fair", "nair", "dtilt"], "kill": ["fsmash", "bair", "up-b"], "combo_starters": ["nair", "dtilt", "dancing blade"]},
        "tips_as": ["No tippers means consistent damage", "Fair is your best move", "Easier than Marth"],
        "tips_against": ["Same as Marth but no tippers", "She needs higher percent to kill", "Mixup your recovery"]
    },
    "young link": {
        "name": "Young Link",
        "archetype": "zoner",
        "strengths": ["projectiles", "speed", "combos"],
        "weaknesses": ["kill power", "recovery", "light"],
        "key_moves": {"neutral": ["arrow", "boomerang", "bomb"], "kill": ["dair", "up-b", "fsmash"], "combo_starters": ["nair", "bomb", "up-air"]},
        "tips_as": ["Spam projectiles constantly", "Nair combos into itself", "Dair spikes and kills"],
        "tips_against": ["Get in on him", "He's light - kill early", "His recovery is exploitable"]
    },
    "ganondorf": {
        "name": "Ganondorf",
        "archetype": "super heavyweight",
        "strengths": ["kill power", "damage", "reads"],
        "weaknesses": ["speed", "recovery", "disadvantage"],
        "key_moves": {"neutral": ["nair", "bair", "down-b"], "kill": ["everything", "fsmash", "doriyah"], "combo_starters": ["down-throw", "nair", "flame choke"]},
        "tips_as": ["Every hit does massive damage", "Flame choke is a command grab", "Nair is your fastest option"],
        "tips_against": ["He's slow - camp him", "Edgeguard him - his recovery is awful", "Don't get hit"]
    },
    "mewtwo": {
        "name": "Mewtwo",
        "archetype": "glass cannon",
        "strengths": ["shadow ball", "tail", "mobility"],
        "weaknesses": ["huge hurtbox", "light for size", "tail hurtbox"],
        "key_moves": {"neutral": ["shadow ball", "fair", "dtilt"], "kill": ["shadow ball", "fsmash", "up-throw"], "combo_starters": ["dtilt", "down-throw", "nair"]},
        "tips_as": ["Shadow ball controls neutral", "Fair is disjointed", "Confusion reflects and stuns"],
        "tips_against": ["His tail is a hurtbox", "He's lighter than he looks", "Hit the tail"]
    },
    "roy": {
        "name": "Roy",
        "archetype": "swordie",
        "strengths": ["kill power", "speed", "hilt sweetspots"],
        "weaknesses": ["range", "recovery", "needs to be close"],
        "key_moves": {"neutral": ["jab", "dtilt", "nair"], "kill": ["fsmash", "bair", "up-b"], "combo_starters": ["jab", "dtilt", "nair"]},
        "tips_as": ["Stay close for sweetspots", "Jab is incredibly fast", "Side-b sweetspot kills early"],
        "tips_against": ["Outspace him", "His recovery is linear", "Watch for jab"]
    },
    "chrom": {
        "name": "Chrom",
        "archetype": "swordie",
        "strengths": ["consistency", "speed", "damage"],
        "weaknesses": ["recovery", "no sweetspots", "edgeguardable"],
        "key_moves": {"neutral": ["nair", "fair", "jab"], "kill": ["fsmash", "bair", "up-b"], "combo_starters": ["nair", "dtilt", "jab"]},
        "tips_as": ["No sweetspots means consistency", "Up-b goes down too - recovers worse", "Simpler Roy"],
        "tips_against": ["Edgeguard him - up-b goes down", "Same as Roy otherwise", "Exploit recovery hard"]
    },
    "game & watch": {
        "name": "Mr. Game & Watch",
        "archetype": "bait-and-punish",
        "strengths": ["bucket", "up-b oos", "flat"],
        "weaknesses": ["light", "range", "struggles vs disjoints"],
        "key_moves": {"neutral": ["bacon", "fair", "bair"], "kill": ["bucket", "up-smash", "9 hammer"], "combo_starters": ["dtilt", "nair", "up-air"]},
        "tips_as": ["Bucket absorbs projectiles and attacks", "Up-b out of shield is frame 3", "Flat hitbox avoids moves"],
        "tips_against": ["Don't feed bucket", "He's super light", "Sword characters beat him"]
    },
    # Brawl newcomers
    "meta knight": {
        "name": "Meta Knight",
        "archetype": "rushdown",
        "strengths": ["speed", "recovery", "edgeguarding"],
        "weaknesses": ["damage output", "range", "kill power"],
        "key_moves": {"neutral": ["dash attack", "nair", "fair"], "kill": ["dair", "fsmash", "up-b"], "combo_starters": ["dtilt", "up-air", "nair"]},
        "tips_as": ["Multiple jumps and specials for recovery", "Dash attack leads to combos", "Edgeguard with dair"],
        "tips_against": ["He struggles to kill", "Out-damage him", "Respect his speed"]
    },
    "pit": {
        "name": "Pit",
        "archetype": "all-rounder",
        "strengths": ["recovery", "arrows", "well-rounded"],
        "weaknesses": ["kill power", "nothing exceptional", "damage"],
        "key_moves": {"neutral": ["arrow", "fair", "ftilt"], "kill": ["fsmash", "bair", "up-b"], "combo_starters": ["nair", "dtilt", "up-air"]},
        "tips_as": ["Arrows for neutral control", "Great recovery - go deep", "Jack of all trades"],
        "tips_against": ["He's honest - no gimmicks to exploit", "Out-damage him", "His arrows are weak"]
    },
    "dark pit": {
        "name": "Dark Pit",
        "archetype": "all-rounder",
        "strengths": ["recovery", "side-b kill power", "well-rounded"],
        "weaknesses": ["same as Pit", "arrows worse for gimping", "nothing exceptional"],
        "key_moves": {"neutral": ["arrow", "fair", "ftilt"], "kill": ["side-b", "fsmash", "bair"], "combo_starters": ["nair", "dtilt", "up-air"]},
        "tips_as": ["Side-b kills earlier than Pit's", "Arrows go straighter", "Same gameplan as Pit"],
        "tips_against": ["Same as Pit", "Watch for side-b at ledge", "Arrows are less controllable"]
    },
    "zero suit samus": {
        "name": "Zero Suit Samus",
        "archetype": "rushdown",
        "strengths": ["mobility", "combo game", "flip jump"],
        "weaknesses": ["light", "kill confirms", "grab range"],
        "key_moves": {"neutral": ["zair", "fair", "nair"], "kill": ["flip kick spike", "bair", "up-b"], "combo_starters": ["down-b bury", "nair", "zair"]},
        "tips_as": ["Flip jump is incredible for mixups", "Zair controls space", "Down-b buries for kills"],
        "tips_against": ["Respect flip jump", "She's light", "Don't get buried"]
    },
    "wario": {
        "name": "Wario",
        "archetype": "bait-and-punish",
        "strengths": ["waft", "air mobility", "nair"],
        "weaknesses": ["range", "without waft", "approach"],
        "key_moves": {"neutral": ["bike", "nair", "fair"], "kill": ["waft", "fsmash", "bair"], "combo_starters": ["nair", "dtilt", "bike"]},
        "tips_as": ["Waft charges over time - huge kill move", "Nair is your best move", "Bike gives mobility and a projectile"],
        "tips_against": ["Track waft charge", "He's vulnerable without waft", "Can't camp him - bike approaches"]
    },
    "snake": {
        "name": "Snake",
        "archetype": "zoner",
        "strengths": ["explosives", "kill power", "heavy"],
        "weaknesses": ["disadvantage", "recovery", "close range"],
        "key_moves": {"neutral": ["grenade", "nikita", "c4"], "kill": ["utilt", "fsmash", "nikita"], "combo_starters": ["c4", "grenade", "dtilt"]},
        "tips_as": ["Grenade controls huge space", "Up-tilt is frame 6 and kills early", "C4 stick combos"],
        "tips_against": ["Get in close", "Edgeguard his cypher", "Don't let him set up explosives"]
    },
    "ike": {
        "name": "Ike",
        "archetype": "swordie",
        "strengths": ["range", "kill power", "nair"],
        "weaknesses": ["speed", "recovery", "disadvantage"],
        "key_moves": {"neutral": ["nair", "fair", "jab"], "kill": ["nair", "fsmash", "bair"], "combo_starters": ["nair", "dtilt", "up-air"]},
        "tips_as": ["Nair is your best move - kills and combos", "Fair has huge range", "Eruption at ledge is strong"],
        "tips_against": ["He's slow - whiff punish", "Edgeguard his predictable up-b", "Get in close"]
    },
    "pokemon trainer": {
        "name": "Pokemon Trainer",
        "archetype": "technical",
        "strengths": ["three characters", "versatile", "squirtle speed"],
        "weaknesses": ["complex", "ivysaur recovery", "charizard big hurtbox"],
        "key_moves": {"neutral": ["squirtle nair", "ivy fair", "charizard bair"], "kill": ["ivy dair", "charizard fsmash", "flare blitz"], "combo_starters": ["squirtle nair", "ivy nair", "dtilt"]},
        "tips_as": ["Switch to adapt to situations", "Squirtle for combos, Ivy for neutral, Zard for kills", "Each has different recovery"],
        "tips_against": ["Learn each Pokemon's weakness", "Charizard is slow", "Ivysaur recovery is exploitable"]
    },
    "diddy kong": {
        "name": "Diddy Kong",
        "archetype": "rushdown",
        "strengths": ["banana", "combo game", "speed"],
        "weaknesses": ["kill power", "recovery", "without banana"],
        "key_moves": {"neutral": ["banana", "fair", "ftilt"], "kill": ["fsmash", "bair", "up-smash"], "combo_starters": ["banana", "dtilt", "nair"]},
        "tips_as": ["Banana controls neutral", "Fair combos into itself", "Monkey flip for mixups"],
        "tips_against": ["Catch his banana", "He struggles to kill", "Edgeguard his up-b"]
    },
    "lucas": {
        "name": "Lucas",
        "archetype": "bait-and-punish",
        "strengths": ["pk freeze", "tether recovery", "zair"],
        "weaknesses": ["disadvantage", "slow", "neutral"],
        "key_moves": {"neutral": ["pk fire", "zair", "fair"], "kill": ["pk freeze", "bair", "up-smash"], "combo_starters": ["nair", "dtilt", "dthrow"]},
        "tips_as": ["PK freeze at ledge is oppressive", "Zair is a great poke", "Dair spikes hard"],
        "tips_against": ["SDI pk fire up and away", "His recovery is linear", "He struggles in neutral"]
    },
    "sonic": {
        "name": "Sonic",
        "archetype": "rushdown",
        "strengths": ["speed", "recovery", "spin dash"],
        "weaknesses": ["kill power", "disadvantage", "camping is boring"],
        "key_moves": {"neutral": ["spin dash", "fair", "bair"], "kill": ["fsmash", "bair", "spring gimps"], "combo_starters": ["spin dash", "nair", "up-air"]},
        "tips_as": ["Spin dash for mobility and combos", "Spring can gimp low recoveries", "You're the fastest - use it"],
        "tips_against": ["Shield spin dash and punish", "He struggles to kill", "Anti-air his approaches"]
    },
    "king dedede": {
        "name": "King Dedede",
        "archetype": "super heavyweight",
        "strengths": ["gordos", "recovery", "super armor"],
        "weaknesses": ["speed", "disadvantage", "big hurtbox"],
        "key_moves": {"neutral": ["gordo", "bair", "ftilt"], "kill": ["fsmash", "jet hammer", "gordo"], "combo_starters": ["dtilt", "nair", "inhale"]},
        "tips_as": ["Gordos control huge space", "Multiple jumps for recovery", "Inhale can copy and kill"],
        "tips_against": ["Reflect or hit gordos back", "He's huge - combo him", "Get under him"]
    },
    "olimar": {
        "name": "Olimar",
        "archetype": "zoner",
        "strengths": ["pikmin damage", "range", "safe"],
        "weaknesses": ["recovery", "without pikmin", "light"],
        "key_moves": {"neutral": ["pikmin throw", "fair", "ftilt"], "kill": ["purple smashes", "bair", "red pikmin"], "combo_starters": ["nair", "dtilt", "pikmin throw"]},
        "tips_as": ["Purple pikmin do massive damage", "Cycle to the color you need", "Pikmin throw racks damage"],
        "tips_against": ["Kill his pikmin", "He's very light", "Exploit his bad recovery"]
    },
    "lucario": {
        "name": "Lucario",
        "archetype": "comeback mechanic",
        "strengths": ["aura at high percent", "force palm", "recovery"],
        "weaknesses": ["low damage at low percent", "inconsistent", "relies on losing"],
        "key_moves": {"neutral": ["aura sphere", "fair", "nair"], "kill": ["aura sphere", "fsmash", "up-smash"], "combo_starters": ["force palm", "dtilt", "nair"]},
        "tips_as": ["You get stronger as you take damage", "Aura sphere is huge at high aura", "Force palm is command grab at close range"],
        "tips_against": ["Kill him early before aura kicks in", "He's weak at 0%", "Don't let him come back"]
    },
    "rob": {
        "name": "R.O.B.",
        "archetype": "zoner",
        "strengths": ["gyro", "recovery", "laser"],
        "weaknesses": ["disadvantage", "big hurtbox", "combo food"],
        "key_moves": {"neutral": ["gyro", "laser", "nair"], "kill": ["fsmash", "up-air", "gyro"], "combo_starters": ["nair", "dtilt", "gyro"]},
        "tips_as": ["Gyro is your best friend", "Laser for chip damage", "Nair combos into everything"],
        "tips_against": ["Catch gyro", "He's big - combo him", "Get under his laser angle"]
    },
    "toon link": {
        "name": "Toon Link",
        "archetype": "zoner",
        "strengths": ["projectiles", "speed", "kill confirms"],
        "weaknesses": ["range", "recovery", "light"],
        "key_moves": {"neutral": ["arrow", "boomerang", "bomb"], "kill": ["bomb confirms", "bair", "fsmash"], "combo_starters": ["nair", "bomb", "fair"]},
        "tips_as": ["Faster than Link", "Bomb confirms kill", "Fair combos into itself"],
        "tips_against": ["Get in on him", "He's lighter than Link", "Edgeguard his up-b"]
    },
    "wolf": {
        "name": "Wolf",
        "archetype": "spacie",
        "strengths": ["kill power", "neutral", "blaster"],
        "weaknesses": ["recovery", "disadvantage", "landing"],
        "key_moves": {"neutral": ["blaster", "fair", "bair"], "kill": ["fsmash", "up-smash", "bair"], "combo_starters": ["nair", "dthrow", "shine"]},
        "tips_as": ["Blaster forces reactions", "Nair is your best move", "Bair kills early and is safe"],
        "tips_against": ["Exploit his recovery", "Don't let him land", "Shield blaster and punish"]
    },
    "villager": {
        "name": "Villager",
        "archetype": "zoner",
        "strengths": ["slingshot", "pocket", "recovery"],
        "weaknesses": ["kill power", "speed", "close range"],
        "key_moves": {"neutral": ["slingshot", "lloid", "fair"], "kill": ["bowling ball", "fsmash", "bair"], "combo_starters": ["nair", "fair", "lloid"]},
        "tips_as": ["Slingshot for neutral control", "Pocket their projectiles", "Bowling ball at ledge kills"],
        "tips_against": ["Get in close", "Don't recover low vs bowling ball", "He struggles to kill"]
    },
    "mega man": {
        "name": "Mega Man",
        "archetype": "zoner",
        "strengths": ["projectiles", "metal blade", "edgeguarding"],
        "weaknesses": ["speed", "close range", "kill confirms"],
        "key_moves": {"neutral": ["lemon", "metal blade", "leaf shield"], "kill": ["fsmash", "bair", "up-air"], "combo_starters": ["metal blade", "nair", "dtilt"]},
        "tips_as": ["Metal blade combos into everything", "Lemons are your neutral", "Leaf shield for approaches"],
        "tips_against": ["Catch metal blade", "Get in close", "He struggles without blade"]
    },
    "wii fit trainer": {
        "name": "Wii Fit Trainer",
        "archetype": "gimmick",
        "strengths": ["deep breathing", "header", "jab kills"],
        "weaknesses": ["small hitboxes", "inconsistent", "weird"],
        "key_moves": {"neutral": ["sun salutation", "header", "fair"], "kill": ["deep breathing fsmash", "header", "bair"], "combo_starters": ["jab", "dtilt", "nair"]},
        "tips_as": ["Deep breathing buffs damage", "Header is frame 4 projectile", "Jab buries at ledge"],
        "tips_against": ["Her hitboxes are small", "Don't let her deep breathe", "Weird angles on her attacks"]
    },
    "rosalina": {
        "name": "Rosalina & Luma",
        "archetype": "puppet fighter",
        "strengths": ["luma", "recovery", "stage control"],
        "weaknesses": ["light", "without luma", "luma respawn time"],
        "key_moves": {"neutral": ["luma shot", "fair", "nair"], "kill": ["up-air", "fsmash", "luma attacks"], "combo_starters": ["nair", "dtilt", "luma"]},
        "tips_as": ["Luma extends your range", "Gravitational pull absorbs projectiles", "Keep luma alive"],
        "tips_against": ["Kill luma first", "Rosa is light", "Rush her down without luma"]
    },
    "little mac": {
        "name": "Little Mac",
        "archetype": "glass cannon",
        "strengths": ["ground speed", "super armor", "ko punch"],
        "weaknesses": ["air game", "recovery", "offstage is death"],
        "key_moves": {"neutral": ["jab", "ftilt", "dtilt"], "kill": ["ko punch", "fsmash", "jab"], "combo_starters": ["jab", "dtilt", "nair"]},
        "tips_as": ["Stay on stage", "KO punch kills at 30%", "Super armor through attacks"],
        "tips_against": ["Get him offstage", "Camp platforms", "Any hit offstage kills him"]
    },
    "greninja": {
        "name": "Greninja",
        "archetype": "rushdown",
        "strengths": ["speed", "combos", "recovery"],
        "weaknesses": ["kill power", "light", "disadvantage"],
        "key_moves": {"neutral": ["shuriken", "fair", "dtilt"], "kill": ["up-smash", "bair", "dair"], "combo_starters": ["dtilt", "nair", "dash attack"]},
        "tips_as": ["Shuriken for neutral", "Dtilt combos into up-smash", "Shadow sneak for mixups"],
        "tips_against": ["He struggles to kill", "Catch his landing", "He's light - kill early"]
    },
    "palutena": {
        "name": "Palutena",
        "archetype": "all-rounder",
        "strengths": ["nair", "bair", "teleport"],
        "weaknesses": ["landing", "without nair", "struggles vs small chars"],
        "key_moves": {"neutral": ["nair", "bair", "autoreticle"], "kill": ["bair", "up-smash", "up-air"], "combo_starters": ["nair", "dthrow", "up-air"]},
        "tips_as": ["Nair is your best move", "Bair walls out approaches", "Teleport mixups for recovery"],
        "tips_against": ["Get under her nair", "Small characters beat her", "Punish teleport"]
    },
    "pac-man": {
        "name": "Pac-Man",
        "archetype": "gimmick",
        "strengths": ["hydrant", "fruit", "setups"],
        "weaknesses": ["kill power", "complex", "inconsistent"],
        "key_moves": {"neutral": ["fruit", "hydrant", "fair"], "kill": ["key", "fsmash", "hydrant setups"], "combo_starters": ["apple", "nair", "hydrant"]},
        "tips_as": ["Fruit cycles are key to learn", "Hydrant combos enable crazy stuff", "Key kills early"],
        "tips_against": ["Hit hydrant away", "Don't let him charge fruit", "He's weird - learn the MU"]
    },
    "robin": {
        "name": "Robin",
        "archetype": "zoner",
        "strengths": ["arcfire", "levin sword", "kill power"],
        "weaknesses": ["speed", "resource management", "recovery"],
        "key_moves": {"neutral": ["thunder", "arcfire", "fair"], "kill": ["levin fair", "arcthunder", "fsmash"], "combo_starters": ["arcfire", "nair", "dtilt"]},
        "tips_as": ["Arcfire traps opponents", "Levin sword has range and power", "Manage your tomes"],
        "tips_against": ["Get in close", "His moves have cooldowns", "Edgeguard his tether"]
    },
    "shulk": {
        "name": "Shulk",
        "archetype": "technical",
        "strengths": ["monado arts", "range", "versatility"],
        "weaknesses": ["frame data", "complex", "without arts"],
        "key_moves": {"neutral": ["fair", "nair", "jab"], "kill": ["smash art fsmash", "bair", "up-air"], "combo_starters": ["nair", "dtilt", "fair"]},
        "tips_as": ["Monado arts change everything", "Speed for neutral, Smash for kills", "Shield when in disadvantage"],
        "tips_against": ["Track his arts", "Punish art switching", "Without arts he's slow"]
    },
    "bowser jr": {
        "name": "Bowser Jr.",
        "archetype": "zoner",
        "strengths": ["clown car armor", "mechakoopa", "recovery"],
        "weaknesses": ["hurtbox outside clown car", "slow", "juggling"],
        "key_moves": {"neutral": ["cannonball", "mechakoopa", "fair"], "kill": ["fsmash", "clown car slam", "hammer"], "combo_starters": ["nair", "dtilt", "mechakoopa"]},
        "tips_as": ["Clown car takes reduced damage", "Mechakoopa controls space", "Side-b for movement"],
        "tips_against": ["Hit him out of the car", "Junior himself takes more damage", "Juggle him"]
    },
    "duck hunt": {
        "name": "Duck Hunt",
        "archetype": "zoner",
        "strengths": ["can setup", "tricky", "recovery"],
        "weaknesses": ["kill power", "close range", "can needs management"],
        "key_moves": {"neutral": ["can", "clay pigeon", "fair"], "kill": ["fsmash", "can snipes", "up-smash"], "combo_starters": ["can", "nair", "dtilt"]},
        "tips_as": ["Can controls huge space", "Detonate can at will", "Wild gunman for coverage"],
        "tips_against": ["Hit the can away", "Get in close", "He struggles to kill"]
    },
    "ryu": {
        "name": "Ryu",
        "archetype": "footsies",
        "strengths": ["auto-turnaround", "true inputs", "kill confirms"],
        "weaknesses": ["recovery", "range", "zoners"],
        "key_moves": {"neutral": ["hadouken", "ftilt", "nair"], "kill": ["true shoryuken", "fsmash", "tatsu"], "combo_starters": ["dtilt", "nair", "hadouken"]},
        "tips_as": ["True inputs are stronger", "Hadouken for neutral", "Heavy dtilt into true shoryu kills"],
        "tips_against": ["Zone him out", "His recovery is linear", "Watch for auto-turnaround"]
    },
    "ken": {
        "name": "Ken",
        "archetype": "footsies",
        "strengths": ["combos", "speed", "kill power"],
        "weaknesses": ["recovery", "range", "zoners"],
        "key_moves": {"neutral": ["hadouken", "nair", "ftilt"], "kill": ["true shoryuken", "roundhouse", "heavy tatsu"], "combo_starters": ["crescent kick", "nair", "dtilt"]},
        "tips_as": ["Faster than Ryu", "Crescent kick combos are deadly", "Roundhouse kills early"],
        "tips_against": ["Same as Ryu", "His combo game is scarier", "Zone him"]
    },
    "cloud": {
        "name": "Cloud",
        "archetype": "swordie",
        "strengths": ["range", "speed", "limit"],
        "weaknesses": ["recovery", "grab game", "offstage"],
        "key_moves": {"neutral": ["blade beam", "fair", "bair"], "kill": ["limit cross slash", "limit blade beam", "up-smash"], "combo_starters": ["nair", "up-air", "dtilt"]},
        "tips_as": ["Charge limit when safe", "Bair is your best move", "Don't go deep offstage"],
        "tips_against": ["Force him offstage", "Track limit charge", "His recovery is exploitable"]
    },
    "corrin": {
        "name": "Corrin",
        "archetype": "swordie",
        "strengths": ["pin", "range", "kill power"],
        "weaknesses": ["speed", "disadvantage", "recovery"],
        "key_moves": {"neutral": ["dragon fang", "fair", "bair"], "kill": ["pin tipper", "fsmash", "bair"], "combo_starters": ["nair", "pin", "dtilt"]},
        "tips_as": ["Pin controls space uniquely", "Fair has long range", "Dragon fang shot for zoning"],
        "tips_against": ["Get under pin", "She's slow", "Edgeguard her"]
    },
    "bayonetta": {
        "name": "Bayonetta",
        "archetype": "technical",
        "strengths": ["combos", "witch time", "recovery"],
        "weaknesses": ["damage output", "kill power", "SDI beats her"],
        "key_moves": {"neutral": ["bullet arts", "fair", "nair"], "kill": ["witch time punish", "up-b kills", "bair"], "combo_starters": ["heel slide", "dtilt", "up-air"]},
        "tips_as": ["Witch time counter big moves", "Extended combos with specials", "ABK (always be kicking)"],
        "tips_against": ["SDI her combos", "Her damage is low", "Don't hit witch time"]
    },
    "inkling": {
        "name": "Inkling",
        "archetype": "rushdown",
        "strengths": ["ink mechanic", "roller bury", "mobility"],
        "weaknesses": ["ink management", "kill power", "reload vulnerability"],
        "key_moves": {"neutral": ["splattershot", "fair", "bair"], "kill": ["roller bury into smash", "fsmash", "bair"], "combo_starters": ["dtilt", "nair", "dash attack"]},
        "tips_as": ["Ink increases damage taken", "Roller buries for kills", "Manage ink carefully"],
        "tips_against": ["Inked attacks hurt more", "Catch her reloading", "She struggles to kill without roller"]
    },
    "ridley": {
        "name": "Ridley",
        "archetype": "super heavyweight",
        "strengths": ["range", "kill power", "command grab"],
        "weaknesses": ["big hurtbox", "combo food", "recovery"],
        "key_moves": {"neutral": ["fireballs", "fair", "nair"], "kill": ["command grab offstage", "fsmash", "bair"], "combo_starters": ["nair", "dtilt", "down-b"]},
        "tips_as": ["Skewer crumples for kills", "Space charge for kills", "Command grab at ledge is scary"],
        "tips_against": ["He's huge - combo him", "Edgeguard his linear recovery", "Don't get grabbed offstage"]
    },
    "simon": {
        "name": "Simon",
        "archetype": "zoner",
        "strengths": ["range", "holy water", "whip"],
        "weaknesses": ["speed", "disadvantage", "close range"],
        "key_moves": {"neutral": ["cross", "holy water", "fair"], "kill": ["fsmash", "holy water combos", "up-b"], "combo_starters": ["holy water", "fair", "dtilt"]},
        "tips_as": ["Holy water into smash attack", "Cross controls space", "Whip has insane range"],
        "tips_against": ["Get in close", "His disadvantage is terrible", "Jump over holy water"]
    },
    "richter": {
        "name": "Richter",
        "archetype": "zoner",
        "strengths": ["same as Simon", "holy water aura", "whip"],
        "weaknesses": ["same as Simon", "speed", "close range"],
        "key_moves": {"neutral": ["cross", "holy water", "fair"], "kill": ["fsmash", "holy water combos", "up-b"], "combo_starters": ["holy water", "fair", "dtilt"]},
        "tips_as": ["Holy water is aura not fire", "Otherwise identical to Simon", "Same gameplan"],
        "tips_against": ["Same as Simon", "Get in close", "Punish his poor disadvantage"]
    },
    "king k. rool": {
        "name": "King K. Rool",
        "archetype": "super heavyweight",
        "strengths": ["belly armor", "projectiles", "recovery"],
        "weaknesses": ["belly breaks", "slow", "disadvantage"],
        "key_moves": {"neutral": ["crown", "blunderbuss", "nair"], "kill": ["fsmash", "bury into smash", "crown"], "combo_starters": ["nair", "dtilt", "blunderbuss"]},
        "tips_as": ["Belly armor on smashes and aerials", "Crown is great neutral", "Bury confirms into smash"],
        "tips_against": ["Break the belly armor", "He's slow - whiff punish", "Don't get hit by crown"]
    },
    "isabelle": {
        "name": "Isabelle",
        "archetype": "zoner",
        "strengths": ["pocket", "fishing rod", "lloid trap"],
        "weaknesses": ["kill power", "speed", "range"],
        "key_moves": {"neutral": ["lloid trap", "fishing rod", "fair"], "kill": ["fsmash", "fishing rod gimps", "bair"], "combo_starters": ["nair", "dtilt", "fishing rod"]},
        "tips_as": ["Fishing rod grabs and gimps", "Lloid trap is better than Villager's", "Pocket their projectiles"],
        "tips_against": ["Similar to Villager", "She struggles to kill", "Don't recover into fishing rod"]
    },
    "incineroar": {
        "name": "Incineroar",
        "archetype": "grappler",
        "strengths": ["command grab", "revenge", "kill power"],
        "weaknesses": ["speed", "recovery", "approach"],
        "key_moves": {"neutral": ["alolan whip", "nair", "dtilt"], "kill": ["revenge boosted anything", "alolan whip", "up-smash"], "combo_starters": ["dtilt", "nair", "alolan whip"]},
        "tips_as": ["Revenge buffs your next hit massively", "Alolan whip at ledge is deadly", "You're slow but hit hard"],
        "tips_against": ["Don't feed revenge", "Camp him - he can't approach", "Edgeguard his up-b"]
    },
    "piranha plant": {
        "name": "Piranha Plant",
        "archetype": "gimmick",
        "strengths": ["ptooie", "poison cloud", "long stretch"],
        "weaknesses": ["speed", "disadvantage", "predictable"],
        "key_moves": {"neutral": ["ptooie", "poison cloud", "fair"], "kill": ["ptooie", "fsmash", "down-b"], "combo_starters": ["dtilt", "nair", "poison cloud"]},
        "tips_as": ["Ptooie controls space", "Long stem is a great poke", "Poison cloud for area denial"],
        "tips_against": ["Don't stand near ptooie", "Get around the ball", "He's slow - rush him"]
    },
    "joker": {
        "name": "Joker",
        "archetype": "rushdown",
        "strengths": ["arsene", "gun", "edgeguarding"],
        "weaknesses": ["without arsene", "light", "range"],
        "key_moves": {"neutral": ["gun", "fair", "dtilt"], "kill": ["arsene bair", "arsene smashes", "eigaon"], "combo_starters": ["dtilt", "nair", "fair"]},
        "tips_as": ["Rebel's Guard builds Arsene", "Arsene doubles your power", "Gun for edgeguards"],
        "tips_against": ["Don't hit Rebel's Guard", "Rush him without Arsene", "He's weak without Arsene"]
    },
    "hero": {
        "name": "Hero",
        "archetype": "gimmick",
        "strengths": ["menu spells", "crits", "versatility"],
        "weaknesses": ["mp management", "rng", "slow without spells"],
        "key_moves": {"neutral": ["frizz", "fair", "zap"], "kill": ["crit smashes", "thwack", "kaboom"], "combo_starters": ["nair", "dtilt", "frizz"]},
        "tips_as": ["Learn the spell menu", "Crits can come anytime", "Psyche up for guaranteed crit"],
        "tips_against": ["Don't let him menu safely", "His base moves are slow", "Watch for thwack at high percent"]
    },
    "banjo": {
        "name": "Banjo & Kazooie",
        "archetype": "zoner",
        "strengths": ["wonder wing", "grenade egg", "recovery"],
        "weaknesses": ["5 wonder wings per stock", "speed", "close range"],
        "key_moves": {"neutral": ["egg", "fair", "nair"], "kill": ["wonder wing", "fsmash", "bair"], "combo_starters": ["egg", "nair", "rear egg"]},
        "tips_as": ["Wonder wing has armor", "Track your wing uses", "Rear egg combos"],
        "tips_against": ["Count wonder wings", "He's slow without side-b", "Shield wonder wing and punish"]
    },
    "terry": {
        "name": "Terry",
        "archetype": "footsies",
        "strengths": ["go meter", "input specials", "kill power"],
        "weaknesses": ["recovery", "range", "zoners"],
        "key_moves": {"neutral": ["power wave", "ftilt", "nair"], "kill": ["buster wolf", "power geyser", "power dunk"], "combo_starters": ["jab", "dtilt", "burning knuckle"]},
        "tips_as": ["Go meter at 100%+ enables supers", "Buster Wolf and Power Geyser are deadly", "Jab combos into specials"],
        "tips_against": ["Zone him out", "His recovery is exploitable", "Watch for Go at high percent"]
    },
    "byleth": {
        "name": "Byleth",
        "archetype": "swordie",
        "strengths": ["range", "kill power", "diverse weapons"],
        "weaknesses": ["speed", "frame data", "disadvantage"],
        "key_moves": {"neutral": ["fair", "nair", "failnaught"], "kill": ["amyr (down-b)", "tipman fsmash", "bair"], "combo_starters": ["nair", "dtilt", "up-air"]},
        "tips_as": ["Each attack uses different weapon", "Amyr kills early and has armor", "Failnaught snipes from range"],
        "tips_against": ["She's slow - whiff punish", "Get in close", "Juggle her - poor disadvantage"]
    },
    "min min": {
        "name": "Min Min",
        "archetype": "zoner",
        "strengths": ["insane range", "dragon arm", "ledge trapping"],
        "weaknesses": ["close range", "above her", "disadvantage"],
        "key_moves": {"neutral": ["ramram", "dragon laser", "megawatt"], "kill": ["dragon arm", "fsmash", "up-smash"], "combo_starters": ["ramram", "dtilt", "up-air"]},
        "tips_as": ["Dragon arm after landing smash", "Mix up arm combinations", "Wall of pain at ledge"],
        "tips_against": ["Get above or behind her", "Her arms can't cover close range", "Juggle her"]
    },
    "steve": {
        "name": "Steve",
        "archetype": "gimmick",
        "strengths": ["mining", "minecart", "block building"],
        "weaknesses": ["needs resources", "speed", "close range without tools"],
        "key_moves": {"neutral": ["mine", "minecart", "fair"], "kill": ["diamond smashes", "minecart", "anvil"], "combo_starters": ["minecart", "dtilt", "nair"]},
        "tips_as": ["Always be mining", "Diamond tools are OP", "Blocks extend combos"],
        "tips_against": ["Don't let him mine", "Stay aggressive", "Minecart is punishable on shield"]
    },
    "sephiroth": {
        "name": "Sephiroth",
        "archetype": "swordie",
        "strengths": ["massive range", "wing", "shadow flare"],
        "weaknesses": ["light", "close range", "disadvantage"],
        "key_moves": {"neutral": ["fair", "shadow flare", "bair"], "kill": ["fsmash", "gigaflare", "octoslash"], "combo_starters": ["shadow flare", "nair", "dtilt"]},
        "tips_as": ["Wing activates when behind", "Shadow flare for pressure", "Fsmash range is absurd"],
        "tips_against": ["Get in close", "He's light - kill early", "Don't let wing activate"]
    },
    "pyra": {
        "name": "Pyra",
        "archetype": "swordie",
        "strengths": ["kill power", "range", "simple"],
        "weaknesses": ["speed", "recovery", "disadvantage"],
        "key_moves": {"neutral": ["fair", "nair", "flame nova"], "kill": ["fsmash", "bair", "up-b"], "combo_starters": ["nair", "dtilt", "up-air"]},
        "tips_as": ["Use Pyra for kills", "Blazing End covers space", "Switch to Mythra for neutral"],
        "tips_against": ["She's slow", "Punish commitment", "Force her to approach"]
    },
    "mythra": {
        "name": "Mythra",
        "archetype": "rushdown",
        "strengths": ["speed", "combos", "foresight"],
        "weaknesses": ["kill power", "recovery", "foresight punishable"],
        "key_moves": {"neutral": ["fair", "nair", "photon edge"], "kill": ["switch to Pyra", "fsmash", "up-air"], "combo_starters": ["nair", "dtilt", "up-air"]},
        "tips_as": ["Use Mythra for damage", "Foresight dodges and punishes", "Switch to Pyra for kills"],
        "tips_against": ["Grab beats foresight", "She can't kill easily", "Edgeguard her"]
    },
    "kazuya": {
        "name": "Kazuya",
        "archetype": "footsies",
        "strengths": ["damage output", "comeback with rage", "electric moves"],
        "weaknesses": ["recovery", "speed", "zoners"],
        "key_moves": {"neutral": ["laser", "dtilt", "nair"], "kill": ["electric wind god fist", "rage drive", "command grabs"], "combo_starters": ["ewgf", "dtilt", "command grabs"]},
        "tips_as": ["EWGF is your best move", "Command grabs beat shield", "Crouch dash mixups"],
        "tips_against": ["Zone him", "His recovery is linear", "Watch for crouch dash"]
    },
    "sora": {
        "name": "Sora",
        "archetype": "swordie",
        "strengths": ["recovery", "floaty", "magic"],
        "weaknesses": ["kill power", "damage output", "light"],
        "key_moves": {"neutral": ["fair", "fire", "nair"], "kill": ["up-smash", "bair", "up-b"], "combo_starters": ["fair", "nair", "fire"]},
        "tips_as": ["Fair combos into itself", "Magic for neutral", "Recovery goes very far"],
        "tips_against": ["He struggles to kill", "He's very light", "Out-damage him"]
    },
    # Mii Fighters
    "mii brawler": {
        "name": "Mii Brawler",
        "archetype": "rushdown",
        "strengths": ["speed", "kill power", "combo game"],
        "weaknesses": ["recovery options", "range", "size customization"],
        "key_moves": {"neutral": ["nair", "fair", "varies by build"], "kill": ["varies by build", "fsmash", "bair"], "combo_starters": ["nair", "dtilt", "varies"]},
        "tips_as": ["Customize specials for playstyle", "Good frame data", "Multiple viable builds"],
        "tips_against": ["Learn what specials they chose", "Can be predictable", "Recovery varies by build"]
    },
    "mii swordfighter": {
        "name": "Mii Swordfighter",
        "archetype": "swordie",
        "strengths": ["range", "projectile options", "balanced"],
        "weaknesses": ["nothing exceptional", "master of none", "predictable"],
        "key_moves": {"neutral": ["fair", "tornado", "varies"], "kill": ["fsmash", "bair", "varies"], "combo_starters": ["nair", "dtilt", "varies"]},
        "tips_as": ["Balanced option", "Good zoning tools", "Customize to your preference"],
        "tips_against": ["Nothing too scary", "Predictable gameplan", "Outplay fundamentals"]
    },
    "mii gunner": {
        "name": "Mii Gunner",
        "archetype": "zoner",
        "strengths": ["projectiles", "range", "camping"],
        "weaknesses": ["close range", "mobility", "recovery"],
        "key_moves": {"neutral": ["charge shot", "missiles", "varies"], "kill": ["charge shot", "fsmash", "varies"], "combo_starters": ["fair", "nair", "varies"]},
        "tips_as": ["Zone with projectiles", "Customize your camping", "Keep opponents out"],
        "tips_against": ["Get in close", "She struggles up close", "Pressure her shield"]
    }
}

# All character names for the selector
ALL_CHARACTERS = [
    "Mario", "Donkey Kong", "Link", "Samus", "Dark Samus", "Yoshi", "Kirby", "Fox",
    "Pikachu", "Luigi", "Ness", "Captain Falcon", "Jigglypuff", "Peach", "Daisy",
    "Bowser", "Ice Climbers", "Sheik", "Zelda", "Dr. Mario", "Pichu", "Falco",
    "Marth", "Lucina", "Young Link", "Ganondorf", "Mewtwo", "Roy", "Chrom",
    "Mr. Game & Watch", "Meta Knight", "Pit", "Dark Pit", "Zero Suit Samus",
    "Wario", "Snake", "Ike", "Pokemon Trainer", "Diddy Kong", "Lucas", "Sonic",
    "King Dedede", "Olimar", "Lucario", "R.O.B.", "Toon Link", "Wolf", "Villager",
    "Mega Man", "Wii Fit Trainer", "Rosalina & Luma", "Little Mac", "Greninja",
    "Palutena", "Pac-Man", "Robin", "Shulk", "Bowser Jr.", "Duck Hunt", "Ryu", "Ken",
    "Cloud", "Corrin", "Bayonetta", "Inkling", "Ridley", "Simon", "Richter",
    "King K. Rool", "Isabelle", "Incineroar", "Piranha Plant", "Joker", "Hero",
    "Banjo & Kazooie", "Terry", "Byleth", "Min Min", "Steve", "Sephiroth",
    "Pyra", "Mythra", "Kazuya", "Sora", "Mii Brawler", "Mii Swordfighter", "Mii Gunner"
]

def get_character_key(name: str) -> str:
    """Convert display name to dictionary key."""
    if not name:
        return None
    return name.lower().replace("& ", "").replace(".", "").replace(" ", " ")

def get_character_tips(character: str, is_player: bool = True) -> list:
    """Get tips for playing as or against a character."""
    if not character:
        return []
    
    key = character.lower()
    if key not in CHARACTER_DATA:
        # try matching by name
        for k, v in CHARACTER_DATA.items():
            if v["name"].lower() == character.lower():
                key = k
                break
    
    if key not in CHARACTER_DATA:
        return []
    
    data = CHARACTER_DATA[key]
    return data.get("tips_as" if is_player else "tips_against", [])

def get_character_info(character: str) -> dict:
    """Get full character data."""
    if not character:
        return None
    
    key = character.lower()
    if key not in CHARACTER_DATA:
        for k, v in CHARACTER_DATA.items():
            if v["name"].lower() == character.lower():
                return v
    
    return CHARACTER_DATA.get(key)

def get_matchup_advice(player_char: str, opponent_char: str) -> str:
    """Generate matchup-specific advice."""
    p_data = get_character_info(player_char)
    o_data = get_character_info(opponent_char)
    
    if not p_data and not o_data:
        return None
    
    advice = []
    
    if p_data:
        advice.append(f"As {p_data['name']} ({p_data['archetype']}):")
        advice.append(f"- Strengths: {', '.join(p_data['strengths'])}")
        advice.append(f"- Weaknesses: {', '.join(p_data['weaknesses'])}")
    
    if o_data:
        advice.append(f"\nAgainst {o_data['name']} ({o_data['archetype']}):")
        for tip in o_data.get("tips_against", [])[:3]:
            advice.append(f"- {tip}")
    
    return "\n".join(advice)

def get_character_specific_feedback(player_char: str, opponent_char: str, patterns: dict) -> list:
    """Generate character-specific feedback based on match patterns."""
    tips = []
    
    o_data = get_character_info(opponent_char)
    p_data = get_character_info(player_char)
    
    stock_losses = patterns.get("stock_losses", [])
    damage_spikes = patterns.get("damage_spikes", [])
    
    if o_data:
        if len(damage_spikes) > 3 and "combos" in o_data.get("strengths", []):
            tips.append({
                "type": "character_tip",
                "message": f"{o_data['name']} has strong combo game. Focus on avoiding combo starters."
            })
        
        early_deaths = [s for s in stock_losses if s.get("percent", 100) < 80]
        if early_deaths and "kill power" in o_data.get("strengths", []):
            kill_moves = o_data.get("key_moves", {}).get("kill", [])[:2]
            tips.append({
                "type": "character_tip", 
                "message": f"{o_data['name']} kills early. Watch out for {', '.join(kill_moves)}."
            })
        
        # add general tips against opponent
        against_tips = o_data.get("tips_against", [])
        if against_tips:
            tips.append({
                "type": "character_tip",
                "message": f"Against {o_data['name']}: {against_tips[0]}"
            })
    
    if p_data:
        key_moves = p_data.get("key_moves", {}).get("neutral", [])
        if key_moves:
            tips.append({
                "type": "character_tip",
                "message": f"Key moves for {p_data['name']}: {', '.join(key_moves)}."
            })
        
        player_tips = p_data.get("tips_as", [])
        if player_tips:
            tips.append({
                "type": "character_tip",
                "message": player_tips[0]
            })
    
    return tips

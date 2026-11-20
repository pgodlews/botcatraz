# Prison yard for robots: art spec

A small animated web page: a prison yard seen from a raised 3/4 view (like a 16-bit
console RPG), where up to 30 robot inmates in orange jumpsuits walk around, lift
weights, play basketball, sit, smoke, drink oil and greet newcomers. A browser
engine (not your job) moves the robots and plays the animations. Your job is the
art and the data files that describe it.

Tone: light-hearted, a bit deadpan. Robots are clunky tin-toy machines, not
menacing. No text baked into images except the two signs named below.

## Rendering facts (fixed)

- Scene size: **640 x 360** logical pixels, drawn with nearest-neighbour scaling
  at 2x to 4x. Everything is pixel art on that grid: hard edges, no anti-aliasing,
  no partial alpha (alpha is 0 or 255), no gradients, no dithering noise.
- View: 3/4 top-down. Ground is seen from above; walls, robots and props show
  their front face. Light from the top-left; soft blob shadows are NOT baked into
  robot frames (the engine draws them), but props and walls have a 1-2 px darker
  shadow on the ground to their bottom-right.
- 1 px dark outline (#161c19) around robots and standing props.
- Palette: at most 40 colours across everything, all from this list or close
  relatives you add and report:
  - outline / darkest      #161c19
  - jumpsuit orange        #de632a, shade #b84a1c, highlight #f08a4b
  - robot metal            #c3cac6, #9aa3a0, #6f7a77, #4b5552
  - eye and lamp glows     red #ff4b3e, amber #ffb020, cyan #5fd0e0, green #7ddc6a
  - guard uniform          #2d4a7a, shade #1f3558
  - concrete ground        #b9beb4, #a9afa5, cracks #8f968c
  - walls and building     #6c7670, #58615c, #454d49, window dark #1c2420
  - court paint            #e9e4d0, key area tint #c7a27a
  - rubber gym mat         #2b302e, #3a403d
  - steel bars and wire    #8d9792
  - oil                    #1a1410, drum blue #2a78d6, drum rust #a0522d
  - cigarette ember        #ff4b3e, paper #f3f1e7, smoke #d9ddd6

## Robots (job "robots")

Frame size **32 x 32**, feet centre at pixel **(16, 28)** in every standing frame
(the engine places that point on the ground). A standing robot is about 16 wide
and 24 tall: big head (10-12 px tall) with a face that reads at 2x, short body in
the orange jumpsuit, stubby arms and legs, a dark chest placard (inmate number
plate, no legible text).

Eight inmate variants. Same jumpsuit, different heads:

| # | Head | Antenna | Eyes |
|---|---|---|---|
| 0 | box | coil spring | red visor slit |
| 1 | tall box | single rod, red ball tip | one big round red lens |
| 2 | wide box | twin rods, red tips | two red square eyes, angry brow line |
| 3 | box | twin rods, amber tips | two amber square eyes |
| 4 | box | curly wire | amber visor bar |
| 5 | round | coil spring | one big amber lens |
| 6 | dome | single rod | cyan visor |
| 7 | wide box with ear bolts | none | two green round eyes |

Plus one **guard**: navy uniform, peaked cap, cyan eyes, a baton on the belt.

One PNG per variant, `robot-0.png` ... `robot-7.png` and `guard.png`, each a grid
of 6 columns x 16 rows of 32 x 32 frames (192 x 512). Unused cells transparent.
Rows, in this order:

| Row | Name | Frames | Facing | What it shows |
|---|---|---|---|---|
| 0 | idle_down | 4 | viewer | slow bob, one blink |
| 1 | idle_side | 4 | right | slow bob |
| 2 | idle_up | 2 | away | slow bob |
| 3 | walk_down | 4 | viewer | walk cycle, feet alternate, body bobs 1 px |
| 4 | walk_side | 4 | right | walk cycle |
| 5 | walk_up | 4 | away | walk cycle |
| 6 | sit | 2 | viewer | seated (no seat drawn), legs forward, small head move |
| 7 | press | 4 | lying, head to the left | bench press: lying on a weight bench (bench drawn in the frame), barbell goes down to chest and up to locked arms |
| 8 | curl | 4 | viewer | standing dumbbell curls, arms alternate |
| 9 | dribble | 4 | right | bouncing a basketball (ball drawn in the frame, orange-brown #c7622a with dark seam) |
| 10 | shoot | 4 | right | jump shot: crouch with ball, rise, arms up with ball overhead, follow-through WITHOUT the ball |
| 11 | smoke | 6 | right | standing: hand with cigarette at side, up to the mouth, ember glows, down again, exhale pose (no smoke cloud drawn) |
| 12 | drink | 6 | right | lifts an oil can, tips it at the mouth for two frames, a drip, lowers it |
| 13 | wave | 4 | viewer | one arm up waving hello |
| 14 | bump | 4 | right | reaches a fist forward for a fist bump, holds, pulls back |
| 15 | talk | 2 | right | mouth grille lit / unlit, slight head tilt |

The engine mirrors side-facing rows for "left". The guard needs rows 0-5 and 13
only; leave its other rows transparent.

Consistency matters more than detail: within a row the head, body and colours
must not shift except for the intended motion; across rows a variant must be
recognisably the same robot. Each variant must be told apart from the others at
2x by head silhouette and eye colour alone.

Files:
- `robots/robot-0.png` ... `robots/robot-7.png`, `robots/guard.png`
- `robots/robots.json`: `{ "frame": [32,32], "anchor": [16,28], "rows": [ {"name","row","frames","fps","facing"} ... ], "variants": [ {"file","head","antenna","eyes"} ... ], "palette": ["#rrggbb", ...] }`
- `robots/make_robots.py`: the script that regenerates every file (Pillow only), deterministic
- `robots/preview/sheet-<name>-4x.png`: each sheet at 4x on a mid-grey checker background
- `robots/preview/faces-8x.png`: the idle_down frame 0 of all nine robots side by side at 8x
- `robots/preview/<row name>.gif`: for variant 0, each row as a looping GIF at 6x (use the fps from robots.json)
- `robots/preview/lineup-3x.png`: all nine robots standing in a row on concrete colour #b9beb4, at 3x
- `robots/REPORT.md`: what you made, the checks you ran and their output, anything you could not do

## Yard (job "scene")

One background plus separate props, so the engine can draw robots in front of or
behind things by comparing their feet line.

Layout, in scene pixels (x right, y down). Keep to it within a few pixels and
report the real numbers in `zones.json`:

- **Perimeter**: top wall band y 0-56 (drawn in elevation: you see its face),
  left wall x 0-10, right wall x 630-640, bottom edge y 350-360 (the top of a
  wall seen from behind, with razor wire). Razor wire coils along the top wall.
- **Cell block**: a building face along the top, x 16-300, y 0-56: brick or block
  work, four small barred windows, and a doorway centred on x = 150, 22 wide and
  30 tall, with the sign `CELL BLOCK` above it. Robots walk in and out here; the
  ground point in front of the door is (150, 60).
- **Watchtower**: top-right, footprint about x 560-610, y 30-70, rising above the
  wall (it may cover part of the top band), with a searchlight lamp (no beam).
- **Main gate**: in the right wall, opening y 150-200, sign `INTAKE` beside it.
  New inmates arrive and released ones leave here; ground point just inside is
  (622, 175).
- **Basketball half court**: painted lines on the ground, x 24-214, y 96-296,
  hoop on the left: pole base near (30, 196), backboard facing right, rim centre
  near (46, 178).
- **Picnic tables**: two, with bench seats above and below each, table tops
  centred near (300, 124) and (376, 124).
- **Oil bar**: against the top wall right of the cell block, x 420-540, y 56-100:
  three oil drums (one with a hand pump), a small counter with oil cans on it.
- **Weights area**: a dark rubber mat x 262-442, y 222-332. Two weight benches
  with barbell stands (drawn EMPTY as props, each 32 x 32 or smaller, matching
  the bench in the robots' `press` row: bench centre near (300, 264) and
  (362, 264)); a dumbbell rack near (410, 238); a kettlebell or two loose.
- **Smoking corner**: bottom-right, x 500-624, y 262-344: a lamp post near
  (520, 270), a sand-bucket ash bin near (560, 300), cigarette butts on the ground.
- Elsewhere: open concrete with cracks, stains, a drain cover, painted yellow
  line 6 px inside the walls, a few weeds. Keep it readable: robots must stand out.

Files:
- `scene/yard_bg.png` (640 x 360, opaque): ground, painted lines, wall bands,
  building face with the doorway shown OPEN (dark inside), the gate opening shown
  OPEN (dark road beyond), and anything robots can never walk behind.
- `scene/props.png` + `scene/props.json`: every standing object as a sprite on a
  transparent atlas. For each: `{"name", "rect":[x,y,w,h] in the atlas, "at":[x,y]
  top-left position in the scene, "baseline": scene y of the line where it meets
  the ground, "blocks":[x,y,w,h] ground rectangle robots cannot enter (or null)}`.
  Include: hoop with pole and backboard, both picnic tables with their benches,
  the three drums, the counter, the two EMPTY weight benches (names `bench_0`,
  `bench_1`), dumbbell rack, kettlebells, lamp post, ash bin, watchtower.
  Also animated pieces as frame lists (`"frames":[[x,y,w,h], ...]`):
  - `main_gate`: 4 frames, barred sliding gate from closed to fully open, placed over the gate opening
  - `block_door`: 3 frames, steel door from closed to open, placed over the doorway
  - `ball`: basketball, 8 x 8, 2 frames (seam rotated)
  - `smoke`: puff, 8 x 8, 4 frames growing and thinning
  - `emote_hi`, `emote_bang` (exclamation mark), `emote_heart`, `emote_oil` (drop),
    `emote_zzz`, `emote_fist`: 12 x 12 each, 1 frame, on a white rounded bubble with the dark outline
  - `box`: a small cardboard belongings box, 10 x 8, for a robot being released
- `scene/zones.json`: the real coordinates of everything the engine needs:
  `door` (ground point), `gate` (ground point inside) and `gate_outside` (a point
  beyond the right edge), `court` rect, `hoop` (pole base, rim centre),
  `court_spots` (8 ground points on the court), `seats` (each table seat: point
  and which way the robot faces), `bar_spots` (5 points in front of the bar),
  `press` (2: the ground point where a robots `press` frame anchor (16, 28) must
  go so the robot's drawn bench lands exactly on the empty bench prop, and the
  prop name to hide while occupied), `curl_spots` (4 points on the mat),
  `smoke_spots` (5 points), `loiter_spots` (12 points spread over open ground),
  `guard_post` (point near the gate, about (604, 216)), `walkable` (list of rects
  covering all open ground) and `obstacles` (all `blocks` rects).
- `scene/make_scene.py`: regenerates everything (Pillow only), deterministic
- `scene/preview/yard-2x.png`: background with all props placed, gate and door closed, at 2x
- `scene/preview/yard-open-2x.png`: same with gate and door open
- `scene/preview/yard-zones-2x.png`: same with every zone point and rect drawn and labelled
- `scene/preview/props-4x.png`: the props atlas at 4x on a checker background
- `scene/REPORT.md`: as for robots

For scale while drawing: a standing robot is 16 x 24 px with its feet on the
ground point. Use a plain orange stand-in of that size in `yard-zones-2x.png` at
each spot so the lead can judge scale. In the `press` zone, draw a 30 x 14
stand-in lying on the bench.

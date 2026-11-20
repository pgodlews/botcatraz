#!/usr/bin/env python3
"""Deterministic shared-part pixel sprites. Python standard library + Pillow only.

Run from any working directory: python3 robots/make_robots.py
Every generated path is below this script's directory.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
PREVIEW = ROOT / 'preview'
P = {
    'ink': '#161c19', 'orange': '#de632a', 'shade': '#b84a1c',
    'light': '#f08a4b', 'metal': '#c3cac6', 'mid': '#9aa3a0',
    'steel': '#6f7a77', 'dark': '#4b5552', 'red': '#ff4b3e',
    'amber': '#ffb020', 'cyan': '#5fd0e0', 'green': '#7ddc6a',
    'navy': '#2d4a7a', 'navyshade': '#1f3558', 'ground': '#b9beb4',
    'groundshade': '#a9afa5', 'mat': '#2b302e', 'matlight': '#3a403d',
    'oil': '#1a1410', 'blue': '#2a78d6', 'paper': '#f3f1e7',
    'ball': '#c7622a', 'rust': '#a0522d',
}
SPEC_PALETTE = set('''161c19 de632a b84a1c f08a4b c3cac6 9aa3a0 6f7a77
4b5552 ff4b3e ffb020 5fd0e0 7ddc6a 2d4a7a 1f3558 b9beb4 a9afa5
8f968c 6c7670 58615c 454d49 1c2420 e9e4d0 c7a27a 2b302e 3a403d
8d9792 1a1410 2a78d6 a0522d f3f1e7 d9ddd6 c7622a'''.split())
ROWS = [
    ('idle_down', 4, 3, 'viewer'), ('idle_side', 4, 3, 'right'),
    ('idle_up', 2, 3, 'away'), ('walk_down', 6, 9, 'viewer'),
    ('walk_side', 6, 9, 'right'), ('walk_up', 6, 9, 'away'),
    ('sit', 4, 2, 'viewer'), ('press', 4, 5, 'lying, head to the left'),
    ('curl', 4, 5, 'viewer'), ('dribble', 4, 7, 'right'),
    ('shoot', 4, 5, 'right'), ('smoke', 6, 3, 'right'),
    ('drink', 6, 3, 'right'), ('wave', 4, 5, 'viewer'),
    ('bump', 4, 5, 'right'), ('talk', 2, 3, 'right'),
    ('sit_back', 4, 2, 'away'),
]
VARIANTS = [
    ('robot-0', 'box', 'coil spring', 'red visor slit', 'red'),
    ('robot-1', 'tall box', 'single rod, red ball tip', 'one big round red lens', 'red'),
    ('robot-2', 'wide box', 'twin rods, red tips', 'two red square eyes, angry brow line', 'red'),
    ('robot-3', 'box', 'twin rods, amber tips', 'two amber square eyes', 'amber'),
    ('robot-4', 'box', 'curly wire', 'amber visor bar', 'amber'),
    ('robot-5', 'round', 'coil spring', 'one big amber lens', 'amber'),
    ('robot-6', 'dome', 'single rod', 'cyan visor', 'cyan'),
    ('robot-7', 'wide box with ear bolts', 'none', 'two green round eyes', 'green'),
    ('robot-8', 'television', 'rabbit ears', 'two cyan screen eyes', 'cyan'),
    ('robot-9', 'upturned bucket, stocky', 'none', 'one amber slot eye', 'amber'),
    ('robot-10', 'glass bulb, slim tall', 'none', 'glowing amber filament', 'amber'),
    ('robot-11', 'toaster, two top slots', 'none', 'two red LED eyes', 'red'),
    ('robot-12', 'hexagonal nut, rust accents', 'none', 'one off-centre green lens', 'green'),
    ('robot-13', 'diving helmet', 'none', 'round cyan porthole', 'cyan'),
    ('robot-14', 'small head, barrel body, stocky', 'none', 'two green eyes', 'green'),
    ('robot-15', 'binocular head, periscope neck, slim', 'none', 'two red eyes', 'red'),
    ('robot-16', 'padlock with U-shackle', 'none', 'amber keyhole', 'amber'),
    ('robot-17', 'traffic signal, slim', 'none', 'red, amber and green lenses', 'amber'),
    ('robot-18', 'reel-to-reel tape deck', 'none', 'cyan tape window', 'cyan'),
    ('robot-19', 'flash camera', 'none', 'cyan lens barrel', 'cyan'),
    ('robot-20', 'safety cone, white band', 'none', 'two green eyes', 'green'),
    ('robot-21', 'parking meter, slim', 'none', 'red expired flag window', 'red'),
    ('guard', 'box with peaked cap', 'none', 'two cyan square eyes', 'cyan'),
]
NEAREST = Image.Resampling.NEAREST
GUARD = 22
VIEWED_NOTES = [
    'Inspected all frames in walk-review-v0/v9/v10/v15.png, decoded from the delivered GIFs: down and side for all four, plus up for v0. The side stride now opens, crosses, exchanges support and opens again; the front arm sweeps fore/aft against the legs. The stocky gait is compact but the lifted soles and wider stride are visible.',
    'Inspected sit-review.png and sit_back-review.png, all four poses for variants0/9/10/15. Front seats now have visibly bent, spread knees, left/centre/right gaze and a nod. Back seats show metal head backs, darker uniform panels, tucked trouser ends and a shoulder shrug, without faces. Torso height stays fixed. The glass bulb turns are subtler than the visor and binocular heads because its filament is symmetric.',
    'Inspected faces-8x.png and lineup-3x.png with all17 robots. The CRT/rabbit ears, bucket rim, bulb, toaster slots, nut flats/rust, diving collar, tiny barrel-body head and tall bent periscope are readable against concrete. The guard remains navy. The nut and helmet are the closest silhouette pair; their flat-versus-rounded contours and eye colours provide the distinction.',
    'Inspected full checker sheets for robot0, guard and all eight new types. The idle bob, empty cells, seated row and action poses are visible. Refined the glass rim, exposed bucket neck, barrel contour and slim chest plates after review. Raised the periscope smoke/drink hand poses to its high head and connected its reclining neck; re-opened that sheet. These tiny service-port contacts and the oil drip remain small details.',
    'Inspected lineup-3x.png, faces-8x.png and full checker sheets sheet-robot-16-4x.png through sheet-robot-21-4x.png for the six round-3 variants (padlock, traffic signal, reel-to-reel, flash camera, safety cone, parking meter). All front, side and back heads, idle blinks, walk gaits, sit/sit_back turns, bench press, smoke/drink and wave poses read cleanly without clipping or back-view glow.',
]


def color(name):
    return P.get(name, name)


def box(d, bounds, fill, outline=True):
    d.rectangle(bounds, fill=color(fill), outline=P['ink'] if outline else None)


def stroke(d, points, fill, width=3):
    d.line(points, fill=P['ink'], width=width + 2)
    d.line(points, fill=color(fill), width=width)


def head(variant, direction='viewer', blink=False, talking=False, antenna_dx=0):
    """Shared head space, including antennas; neck attaches at (16,17)."""
    if 8 <= variant < GUARD:
        return extra_head(variant, direction, blink, talking, antenna_dx)
    im = Image.new('RGBA', (32, 20))
    d = ImageDraw.Draw(im)
    idx = variant
    col = VARIANTS[idx][4]
    left, top, right, bottom = 10, 7, 21, 16
    if idx == 1:
        left, top, right = 11, 5, 20
    elif idx in (2, 7):
        left, right = 8, 23
    if direction == 'right':
        left += 1
        right -= 1
    antenna = Image.new('RGBA', im.size)
    d = ImageDraw.Draw(antenna)
    # The antenna is behind the head, and remains recognisable in all views.
    if idx in (0, 5):
        d.line([(16, top), (16, top-1), (14, top-2), (17, top-3),
                (14, top-4), (16, top-5)], fill=P['ink'], width=1)
        d.point((15, top-3), fill=P['metal'])
    elif idx in (1, 6):
        d.line([(16, top), (16, 2 if idx == 1 else 3)], fill=P['ink'])
        if idx == 1:
            box(d, (14, 0, 18, 3), 'red')
        else:
            box(d, (15, 2, 17, 4), 'metal')
    elif idx in (2, 3):
        for x in (left+3, right-3):
            d.line([(x, top), (x, top-4)], fill=P['ink'])
            box(d, (x-1, top-5, x+1, top-3), col)
    elif idx == 4:
        d.line([(15, top), (14, 4), (18, 3), (18, 1), (15, 1),
                (14, 2)], fill=P['ink'], width=1)
        d.point((16, 2), fill=P['metal'])
    im.alpha_composite(antenna, (antenna_dx, 0))
    d = ImageDraw.Draw(im)
    if idx in (5, 6):
        if idx == 5:
            d.ellipse((left, top, right, bottom), fill=P['mid'], outline=P['ink'])
            d.line((left+3, top+1, right-3, top+1), fill=P['metal'])
        else:
            d.polygon([(left, bottom), (left, top+4), (left+1, top+2),
                       (left+3, top), (right-3, top), (right-1, top+2),
                       (right, top+4), (right, bottom)], fill=P['ink'])
            d.polygon([(left+1,bottom-1),(left+1,top+4),(left+3,top+1),
                       (right-3,top+1),(right-1,top+4),(right-1,bottom-1)], fill=P['mid'])
            d.line((left+3,top+1,right-3,top+1), fill=P['metal'])
    else:
        box(d, (left, top, right, bottom), 'mid')
        d.line((left+1, top+1, right-1, top+1), fill=P['metal'])
        d.line((left+1, top+1, left+1, bottom-1), fill=P['metal'])
        d.line((left+1, bottom-1, right-1, bottom-1), fill=P['steel'])
    if idx == 7:
        for x in (left-2, right+1):
            box(d, (x, 10, x+1, 13), 'dark')
            d.point((x, 10), fill=P['metal'])
    if direction == 'away':
        box(d, (left+3, top+3, right-3, bottom-3), 'dark')
        for y in (top+4, bottom-4):
            d.line((left+4,y,right-4,y), fill=P['steel'])
    else:
        # Side heads show a dark rear panel and the eye on their right plane.
        if direction == 'right':
            box(d, (left, top+3, left+2, bottom-2), 'steel')
        cy = top+4 if idx != 1 else 10
        if idx in (0, 4, 6):
            x0 = left+2 if direction == 'viewer' else right-5
            box(d, (x0, cy-1, right-1, cy+2), 'ink')
            if not blink:
                d.rectangle((x0+1, cy, right-2, cy+1), fill=P[col])
            else:
                d.line((x0+1,cy+1,right-2,cy+1), fill=P['steel'])
        elif idx in (1, 5):
            cx = 16 if direction == 'viewer' else right-3
            d.ellipse((cx-3,cy-2,cx+3,cy+4), fill=P['ink'])
            if not blink:
                d.ellipse((cx-2,cy-1,cx+2,cy+3), fill=P[col])
                d.rectangle((cx-1,cy,cx,cy+1), fill=P['paper'])
            else:
                d.line((cx-2,cy+1,cx+2,cy+1), fill=P['steel'])
        else:
            inset = 3 if idx in (3,GUARD) else 4
            centers = (left+inset,right-inset) if direction == 'viewer' else (right-3,)
            for cx in centers:
                if idx == 7:
                    d.ellipse((cx-2,cy-1,cx+2,cy+3), fill=P['ink'])
                    if not blink:
                        d.ellipse((cx-1,cy,cx+1,cy+2), fill=P[col])
                else:
                    box(d, (cx-2,cy-1,cx+1,cy+2), 'ink')
                    if not blink:
                        d.rectangle((cx-1,cy,cx,cy+1), fill=P[col])
                if blink:
                    d.line((cx-1,cy+1,cx+1,cy+1), fill=P['steel'])
            if idx == 2:
                d.line([(left+2,cy-3),(left+5,cy-2)], fill=P['ink'])
                d.line([(right-5,cy-2),(right-2,cy-3)], fill=P['ink'])
        # The grille is visibly below, and never joins a glowing eye to outline.
        gx = 15 if direction == 'viewer' else right-3
        d.line((gx-1,bottom-2,gx+2,bottom-2), fill=P['cyan'] if talking else P['dark'])
    if idx == GUARD:
        box(d, (10, 4, 21, 7), 'navy')
        d.line((11,5,20,5), fill=P['metal'])
        box(d, (10,7,23 if direction == 'right' else 22,8), 'navyshade')
        d.rectangle((15,5,16,6), fill=P['amber'])
    return im


def extra_head(v, direction, blink, talking, antenna_dx):
    """Eight silhouettes, with the same head attachment point as the old set."""
    im = Image.new('RGBA', (32,20))
    d = ImageDraw.Draw(im)
    away, side = direction == 'away', direction == 'right'
    if v == 8:                         # CRT, aerials and right-hand knobs
        d.line([(14,7),(11+antenna_dx,2),(10+antenna_dx,2)], fill=P['ink'])
        d.line([(18,7),(22+antenna_dx,1),(23+antenna_dx,1)], fill=P['ink'])
        box(d,(8,7,24,16),'dark')
        d.line((9,8,23,8),fill=P['metal'])
        box(d,(10,9,20,14),'steel' if away else 'ink')
        if not away:
            for x in ((16,) if side else (12,17)):
                box(d,(x,10,x+2,12),'steel' if blink else 'cyan',False)
            for y in (10,13):
                d.point((22,y),fill=P['metal'])
    elif v == 9:                       # inverted bucket, wide lower rim
        d.polygon([(11,6),(20,6),(23,15),(24,16),(7,16),(9,14)],fill=P['ink'])
        d.polygon([(12,7),(19,7),(22,14),(9,14)],fill=P['mid'])
        d.line((12,7,19,7),fill=P['metal'])
        box(d,(7,14,24,16),'steel')
        box(d,(12 if not side else 16,10,21,13),'dark')
        if not away:
            d.rectangle((13 if not side else 17,11,20,12),fill=P['steel' if blink else 'amber'])
    elif v == 10:                      # opaque pixel-glass, illuminated filament
        d.ellipse((11,3,20,14),fill=P['dark'],outline=P['ink'])
        d.line([(12,8),(12,6),(14,4),(17,4)],fill=P['metal'])
        d.line([(19,8),(19,11),(18,12)],fill=P['steel'])
        box(d,(13,14,19,17),'steel')
        d.line((14,15,18,15),fill=P['metal'])
        if not away:
            d.line([(14,12),(14,9),(16,7),(18,9),(18,12)],fill=P['steel' if blink else 'amber'],width=2)
            d.line((15,11,17,11),fill=P['amber'])
        else:
            d.line((15,6,15,12),fill=P['steel'])
        # The filament never overwrites the glass's one-pixel black rim.
        d.ellipse((11,3,20,14),outline=P['ink'])
    elif v == 11:                      # toaster lid and two inset slots
        box(d,(8,8,23,16),'mid')
        box(d,(10,5,21,8),'metal')
        for x in (12,17):
            d.line((x,6,x+1,7),fill=P['ink'])
        box(d,(24,10,25,12),'dark')
        if not away:
            for x in ((19,) if side else (11,18)):
                box(d,(x,10,x+2,13),'ink')
                if not blink:
                    d.rectangle((x,11,x+1,12),fill=P['red'])
        else:
            d.line((11,12,20,12),fill=P['dark'])
    elif v == 12:                      # six flats, nut opening offset to left
        points=[(11,5),(20,5),(24,10),(21,16),(10,16),(7,11)]
        d.polygon(points,fill=P['ink'])
        d.polygon([(12,6),(19,6),(23,10),(20,15),(11,15),(8,11)],fill=P['mid'])
        d.line([(11,7),(9,10),(10,12)],fill=P['rust'],width=2)
        d.line((18,15,20,14),fill=P['rust'],width=2)
        if not away:
            x = 19 if side else 14
            d.ellipse((x-3,8,x+3,14),fill=P['ink'])
            if not blink:
                d.ellipse((x-2,9,x+2,13),fill=P['green'])
        else:
            box(d,(13,9,18,12),'dark')
    elif v == 13:                      # collar, helmet globe, circular porthole
        d.ellipse((8,5,23,17),fill=P['mid'],outline=P['ink'])
        d.arc((9,6,21,16),190,270,fill=P['metal'])
        for x in (7,23):
            box(d,(x,10,x+1,13),'steel')
        box(d,(10,16,21,17),'steel')
        cx = 19 if side else 16
        d.ellipse((cx-5,7,cx+4,15),fill=P['dark'],outline=P['ink'])
        d.ellipse((cx-3,9,cx+2,13),fill=P['steel' if away or blink else 'cyan'])
        if away:
            d.line((cx-2,11,cx+1,11),fill=P['dark'])
    elif v == 14:                      # deliberately small head, shoulder gap
        box(d,(12,9,19,15),'mid')
        d.line((13,10,18,10),fill=P['metal'])
        box(d,(14,16,17,17),'steel')
        if not away:
            for x in ((17,) if side else (13,17)):
                d.rectangle((x,11,x+1,12),fill=P['steel' if blink else 'green'])
        else:
            box(d,(14,11,17,13),'dark')
    elif v == 15:                      # bent telescoping stem and twin barrels
        stroke(d,[(16,17),(16,10),(19,10),(19,7)],'steel',2)
        box(d,(10,4,23,8),'dark')
        for x in (11,19):
            box(d,(x,3,x+4,9),'mid')
            d.line((x+1,4,x+3,4),fill=P['metal'])
            box(d,(x+1,5,x+3,8),'dark' if away else 'ink')
            if not away and not blink:
                d.rectangle((x+1,6,x+2,7),fill=P['red'])
        if side and not away:
            box(d,(11,5,14,8),'steel')
    elif v == 16:                      # padlock with U-shackle and amber keyhole
        if side:
            d.polygon([(15,2),(16,2),(17,3),(17,9),(14,9),(14,3)],fill=P['ink'])
            d.rectangle((15,3,16,8),fill=P['metal'])
            d.line((16,4,16,8),fill=P['steel'])
            d.polygon([(11,9),(20,9),(21,10),(21,15),(20,16),(11,16),(10,15),(10,10)],fill=P['ink'])
            d.polygon([(12,10),(19,10),(20,11),(20,14),(19,15),(12,15),(11,14),(11,11)],fill=P['mid'])
            d.line((12,10,19,10),fill=P['metal'])
            box(d,(10,11,12,14),'steel')
            d.rectangle((17,10,19,15),fill=P['ink'])
            d.rectangle((18,11,18,14),fill=P['steel' if blink else 'amber'])
        else:
            d.polygon([(12,2),(19,2),(21,4),(21,9),(19,9),(19,5),(18,4),(13,4),(12,5),(12,9),(10,9),(10,4)],fill=P['ink'])
            d.point((11,3),fill=P['ink'])
            d.point((20,3),fill=P['ink'])
            for px,py in [(12,3),(13,3),(14,3),(15,3),(16,3),(17,3),(18,3),(19,3),
                          (11,4),(11,5),(11,6),(11,7),(11,8),
                          (20,4),(20,5),(20,6),(20,7),(20,8)]:
                d.point((px,py),fill=P['metal'])
            d.rectangle((12,4,19,8),fill=P['ink'])
            d.rectangle((13,5,18,9),fill=(0,0,0,0))
            d.polygon([(9,9),(22,9),(23,10),(23,15),(22,16),(9,16),(8,15),(8,10)],fill=P['ink'])
            d.polygon([(10,10),(21,10),(22,11),(22,14),(21,15),(10,15),(9,14),(9,11)],fill=P['mid'])
            d.line((10,10,21,10),fill=P['metal'])
            d.line((10,15,21,15),fill=P['steel'])
            if away:
                box(d,(11,11,20,14),'dark')
                for rx,ry in ((12,12),(19,12),(12,13),(19,13)):
                    d.point((rx,ry),fill=P['steel'])
            else:
                d.rectangle((14,10,17,15),fill=P['ink'])
                d.rectangle((15,11,16,14),fill=P['steel' if blink else 'amber'])
    elif v == 17:                      # traffic signal housing, three stacked lenses
        if side:
            box(d,(14,2,16,3),'mid')
            box(d,(12,3,18,16),'steel')
            box(d,(12,5,13,14),'dark')
            for y,col in ((5,'red'),(9,'amber'),(13,'green')):
                box(d,(19,y-1,21,y),'dark')
                d.rectangle((16,y-1,18,y+2),fill=P['ink'])
                d.rectangle((17,y,18,y+1),fill=P['steel' if blink else col])
        else:
            for y in (5,9,13):
                box(d,(10,y,11,y+2),'dark')
                box(d,(20,y,21,y+2),'dark')
            box(d,(14,2,17,3),'mid')
            box(d,(12,3,19,16),'steel')
            d.line((13,4,18,4),fill=P['mid'])
            if away:
                box(d,(14,5,17,14),'dark')
                d.line((14,9,17,9),fill=P['steel'])
            else:
                for y,col in ((5,'red'),(9,'amber'),(13,'green')):
                    d.rectangle((14,y-1,17,y+2),fill=P['ink'])
                    d.rectangle((15,y,16,y+1),fill=P['steel' if blink else col])
    elif v == 18:                      # reel-to-reel tape deck
        if side:
            box(d,(15,4,17,9),'steel')
            box(d,(17,3,20,10),'metal')
            d.line((18,4,18,9),fill=P['dark'])
            box(d,(10,9,21,16),'steel')
            d.line((11,10,20,10),fill=P['mid'])
            box(d,(10,11,12,14),'dark')
            box(d,(16,11,21,14),'ink')
            d.rectangle((17,12,20,13),fill=P['steel' if blink else 'cyan'])
        else:
            for cx in (11,21):
                d.ellipse((cx-4,3,cx+4,11),fill=P['dark' if away else 'metal'],outline=P['ink'])
                d.ellipse((cx-2,5,cx+2,9),fill=P['steel' if away else 'dark'],outline=P['ink'])
                d.point((cx,7),fill=P['steel' if away else 'metal'])
            box(d,(8,9,24,16),'steel')
            d.line((9,10,23,10),fill=P['mid'])
            if away:
                box(d,(11,11,21,14),'dark')
            else:
                box(d,(11,11,20,14),'ink')
                d.rectangle((12,12,19,13),fill=P['steel' if blink else 'cyan'])
                d.point((22,12),fill=P['red'])
    elif v == 19:                      # flash camera with protruding lens barrel
        if side:
            box(d,(12,3,17,8),'dark')
            box(d,(15,4,17,7),'paper')
            box(d,(10,8,19,16),'mid')
            d.line((11,9,18,9),fill=P['metal'])
            box(d,(10,13,19,16),'dark')
            box(d,(10,10,12,12),'steel')
            box(d,(18,9,23,15),'steel')
            box(d,(21,10,23,14),'ink')
            d.rectangle((21,11,22,13),fill=P['steel' if blink else 'cyan'])
            if not blink:
                d.point((21,11),fill=P['paper'])
        else:
            box(d,(10,3,16,8),'dark')
            if away:
                d.line((11,4,14,4),fill=P['steel'])
                box(d,(18,6,21,8),'steel')
            else:
                box(d,(11,4,15,7),'paper')
                d.line((12,5,14,5),fill=P['amber'])
                box(d,(18,6,21,8),'steel')
                d.point((20,5),fill=P['ink'])
                d.point((20,6),fill=P['red'])
            box(d,(8,8,23,16),'mid')
            d.line((9,9,22,9),fill=P['metal'])
            box(d,(8,13,23,16),'dark')
            if away:
                box(d,(11,10,20,14),'dark')
                d.line((12,11,19,11),fill=P['steel'])
            else:
                d.ellipse((10,9,17,16),fill=P['steel'],outline=P['ink'])
                d.ellipse((11,10,16,15),fill=P['ink'])
                d.ellipse((12,11,15,14),fill=P['steel' if blink else 'cyan'])
                if not blink:
                    d.point((12,11),fill=P['paper'])
                box(d,(19,10,21,12),'ink')
                d.point((20,11),fill=P['steel'])
                d.point((21,9),fill=P['red'])
    elif v == 20:                      # safety cone, white band, dark rubber base
        d.polygon([(15,2),(17,2),(22,14),(10,14)],fill=P['ink'])
        d.polygon([(15,3),(17,3),(21,14),(11,14)],fill=P['orange'])
        if away:
            d.line([(17,4),(21,14)],fill=P['shade'])
        else:
            d.line([(15,4),(11,14)],fill=P['light'])
        d.polygon([(14,6),(18,6),(19,9),(13,9)],fill=P['paper'])
        if side:
            d.rectangle((15,10,20,12),fill=P['ink'])
            d.rectangle((18,10,19,11),fill=P['steel' if blink else 'green'])
            box(d,(9,14,23,16),'dark')
            d.line((10,15,22,15),fill=P['steel'])
        else:
            if not away:
                d.rectangle((12,10,19,12),fill=P['ink'])
                for x in (13,17):
                    d.rectangle((x,10,x+1,11),fill=P['steel' if blink else 'green'])
            box(d,(8,14,24,16),'dark')
            d.line((9,15,23,15),fill=P['steel'])
    elif v == 21:                      # arched parking meter
        if side:
            d.polygon([(13,3),(18,3),(20,6),(20,16),(11,16),(11,6)],fill=P['ink'])
            d.polygon([(14,4),(17,4),(19,7),(19,15),(12,15),(12,7)],fill=P['steel'])
            d.line((14,4,17,4),fill=P['metal'])
            box(d,(11,8,13,14),'dark')
            box(d,(15,6,19,12),'ink')
            d.rectangle((16,8,19,11),fill=P['steel' if blink else 'paper'])
            if not blink:
                d.rectangle((17,8,19,10),fill=P['red'])
            d.line((17,14,18,14),fill=P['ink'])
        else:
            d.polygon([(12,3),(19,3),(22,6),(22,16),(9,16),(9,6)],fill=P['ink'])
            d.polygon([(13,4),(18,4),(21,7),(21,15),(10,15),(10,7)],fill=P['steel'])
            d.line((13,4,18,4),fill=P['metal'])
            if away:
                box(d,(12,7,19,14),'dark')
                d.line((13,10,18,10),fill=P['steel'])
            else:
                d.polygon([(13,6),(18,6),(20,8),(20,12),(11,12),(11,8)],fill=P['ink'])
                if blink:
                    d.rectangle((12,8,19,11),fill=P['steel'])
                else:
                    d.rectangle((12,8,19,11),fill=P['paper'])
                    d.rectangle((12,8,15,10),fill=P['red'])
                    d.rectangle((17,9,18,10),fill=P['green'])
                d.line((15,14,16,14),fill=P['ink'])
    # Back views contain metal panels only: absolutely no eye/filament glow.
    if away:
        glow = tuple(int(P[VARIANTS[v][4]][i:i+2],16) for i in (1,3,5))
        for y in range(im.height):
            for x in range(im.width):
                if im.getpixel((x,y))[:3] == glow:
                    im.putpixel((x,y), (*tuple(int(P['dark'][i:i+2],16) for i in (1,3,5)),255))
    elif talking:
        d.line((15,15,17,15),fill=P['cyan'])
    return im


def build(v):
    # x bounds, standing top, standing underside; heels always remain y=28.
    return {9:(10,22,18,24), 10:(12,20,16,22),
            14:(10,22,17,24), 15:(12,20,17,23),
            17:(12,20,17,23), 21:(12,20,17,23)}.get(v,(11,21,17,23))


def torso_layer(v, bob=0, direction='viewer', seated=False):
    im = Image.new('RGBA',(32,32))
    d = ImageDraw.Draw(im)
    left,right,top,bottom = build(v)
    if seated:
        top,bottom = 18,24
    top,bottom = top+bob,bottom+bob
    uniform,shade,hi = ('navy','navyshade','steel') if v == GUARD else ('orange','shade','light')
    if v == 14:
        d.polygon([(left+2,top),(right-2,top),(right,top+2),
                   (right,bottom-2),(right-2,bottom),(left+2,bottom),
                   (left,bottom-2),(left,top+2)],fill=P['ink'])
        d.polygon([(left+3,top+1),(right-3,top+1),(right-1,top+2),
                   (right-1,bottom-2),(right-3,bottom-1),(left+3,bottom-1),
                   (left+1,bottom-2),(left+1,top+2)],fill=P[uniform])
        d.line((left+3,top+1,right-3,top+1),fill=P[hi])
        for y in (top+2,bottom-1):
            d.line((left+2,y,right-2,y),fill=P[shade])
    else:
        box(d,(left,top,right,bottom),uniform)
        d.line((left+1,top+1,right-1,top+1),fill=P[hi])
        d.line((right-1,top+2,right-1,bottom-1),fill=P[shade])
    if direction == 'away':
        box(d,(left+2,top+2,right-2,bottom-1),shade)
        d.line((16,top+2,16,bottom-2),fill=P['dark'])
    else:
        plate_left=14 if v in (10,15,17,21) else 13
        box(d,(plate_left,top+2,18,top+4),'dark')
        d.line((plate_left+1,top+3,16,top+3),fill=P['mid'])
        d.point((right-2,bottom-1),fill=P['metal'])
    if v == GUARD:
        box(d,(left,bottom-1,right,bottom),'ink')
        box(d,(15,bottom-1,16,bottom),'amber',False)
    return im


def walk_parts(v, direction, f):
    """Anatomical L/R layers: contact/down/passing, then exchanged legs.

    Shoe coordinates are not inferred by dividing the image into screen halves:
    that would misidentify the legs when they cross in the side view.
    """
    lows = ((28,28),(28,26),(28,26),(28,28),(26,28),(26,28))[f]
    xs = ((21,11),(20,12),(14,18),(11,21),(12,20),(18,14))[f] if direction == 'right' else (12,20)
    left,right,top,bottom = build(v)
    bob = (0,1,0,0,1,0)[f]
    hips = (14,18) if direction == 'right' else (13,19)
    legs,shoes = [],[]
    for k,(x,low) in enumerate(zip(xs,lows)):
        leg = Image.new('RGBA',(32,32))
        d = ImageDraw.Draw(leg)
        knee_x = (19,15)[k] if direction == 'right' and f in (2,5) else (hips[k]+x)//2
        knee_y = 24 if low == 28 else 23
        stroke(d,[(hips[k],bottom-1+bob),(knee_x,knee_y),(x,low-2)],
               'navy' if v == GUARD else ('shade' if k == 0 and direction == 'right' else 'orange'),2)
        shoe = Image.new('RGBA',(32,32))
        sd = ImageDraw.Draw(shoe)
        box(sd,(x-2,low-2,x+2,low),'dark')
        sd.line((x-1,low-1,x+1,low-1),fill=P['mid'])
        legs.append(leg)
        shoes.append(shoe)
    return legs,shoes


def walk_hands(direction, f):
    if direction == 'right':
        return ([(10,23),(12,24),(17,23),(24,23),(22,24),(16,23)][f],
                [(24,23),(22,22),(16,23),(10,23),(12,22),(17,23)][f])
    return ([(9,20),(9,21),(9,22),(9,25),(9,24),(10,23)][f],
            [(24,25),(24,24),(23,23),(23,20),(23,21),(24,22)][f])


def moving_head(v, direction, row, f, bob):
    lag = (-1 if f == 1 else 1 if f == 4 else 0) if row.startswith('walk') else 0
    turn = row == 'sit' and f in (0,2)
    h = head(v,'right' if turn else direction,blink=(row=='idle_down' and f==2),
             talking=(row=='talk' and f==1),antenna_dx=lag)
    if turn and f==0:
        h=h.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    dx,dy = 0,bob
    if row in ('sit','sit_back'):
        dx,dy = (-1,0,1,0)[f],1+(f==3 and row=='sit')
    # Idle heads move as a rigid sprite with the body's vertical bob.
    # Shifting only their upper rows would split the casing and face.
    dy=max(dy,-h.getbbox()[1])
    return h,dx,dy


def seated_frame(v, row, f):
    im = Image.new('RGBA',(32,32))
    d = ImageDraw.Draw(im)
    back = row == 'sit_back'
    left,right,_,_ = build(v)
    if back:
        # Tucked trouser ends, no exposed shoes.
        for x in (12,18):
            box(d,(x,24,x+2,26),'shade')
    else:
        # Thighs project sideways from the hips, then shins drop toward us.
        # This wide knee / narrow hip silhouette distinguishes sitting from idle.
        for hip,knee in ((13,10),(19,22)):
            stroke(d,[(hip,24),(knee,25),(knee,27)],'orange',3)
        for x in (7,19):
            box(d,(x,27,x+6,29),'dark')
            d.line((x+1,28,x+5,28),fill=P['mid'])
    shrug = -1 if back and f==3 else 0
    for x,hand in ((left,(left-1,25)),(right,(right+1,25))):
        arm(d,(x,20+shrug),(hand[0],22+shrug),hand,'shade' if back else 'orange')
    im.alpha_composite(torso_layer(v,direction='away' if back else 'viewer',seated=True))
    h,dx,dy = moving_head(v,'away' if back else 'viewer',row,f,0)
    im.alpha_composite(h,(dx,dy))
    if shrug:
        d=ImageDraw.Draw(im)
        for x in (left,right):
            box(d,(x-1,18,x+1,20),'orange')
    return im


def arm(d, shoulder, elbow, hand, uniform, fist=True):
    stroke(d, [shoulder, elbow, hand], uniform, 3)
    if fist:
        x,y = hand
        box(d, (x-1,y-1,x+2,y+2), 'mid')
        d.point((x,y), fill=P['metal'])


def ball(d, x, y, phase=0):
    d.ellipse((x-3,y-3,x+4,y+4), fill=P['ball'], outline=P['ink'])
    d.line((x-2,y+1,x+3,y+1), fill=P['ink'])
    d.line([(x+(phase%2),y-2),(x+1+(phase%2),y),
            (x+(phase%2),y+3)], fill=P['ink'])
    d.point((x-1,y-1), fill=P['light'])


def dumbbell(d, x, y):
    stroke(d, [(x-4,y),(x+4,y)], 'metal', 1)
    for dx in (-5,3):
        box(d, (x+dx,y-3,x+dx+2,y+3), 'dark')
        d.point((x+dx+1,y-2), fill=P['mid'])


def bench(d):
    # Shared with scene: top rect [2,22,28,4], centre (16,24), baseline 28.
    for x in (5,25):
        box(d,(x,25,x+1,28),'steel')
        d.line((x-1,28,x+2,28),fill=P['ink'])
    box(d,(2,22,29,25),'mat')
    d.line((3,23,28,23),fill=P['matlight'])


def press_frame(v, f):
    im = Image.new('RGBA',(32,32))
    d = ImageDraw.Draw(im)
    bench(d)
    # Lying horizontal, face upward toward viewer, head at the left.
    box(d,(12,17,23,22),'orange')
    d.line((13,18,22,18),fill=P['light'])
    box(d,(17,18,21,20),'dark')
    for y in (18,21):
        stroke(d,[(23,y),(26,y),(28,20)],'shade',2)
    box(d,(27,19,30,22),'dark')
    h = head(v)
    if v == 15:
        stroke(d,[(9,20),(13,20)],'steel',2)
    # Heads preserve their antenna and facial pixel design when reclined.
    im.alpha_composite(h,(-5 if v==7 else -7,6))
    d = ImageDraw.Draw(im)
    by = [17,12,7,12][f]
    for sx,dx in ((16,16),(21,24)):
        arm(d,(sx,20),((sx+dx)//2,by+4),(dx,by+1),'orange')
    stroke(d,[(15,by),(29,by)],'metal',1)
    for x in (14,28):
        box(d,(x,by-4,x+2,by+4),'dark')
        d.line((x+1,by-3,x+1,by+2),fill=P['mid'])
    return im


def frame(v, row, f):
    if row == 'press':
        return press_frame(v,f)
    if row in ('sit','sit_back'):
        return seated_frame(v,row,f)
    im = Image.new('RGBA',(32,32))
    d = ImageDraw.Draw(im)
    uniform = 'navy' if v == GUARD else 'orange'
    shade = 'navyshade' if v == GUARD else 'shade'
    direction = ('away' if row.endswith('_up') else 'right'
                 if row.endswith('_side') or row in ('dribble','shoot','smoke','drink','bump','talk')
                 else 'viewer')
    bob = 0
    if row.startswith('idle'):
        bob = [0,-1,0,1][f] if row != 'idle_up' else [0,-1][f]
    elif row.startswith('walk'):
        bob = [0,1,0,0,1,0][f]
    elif row == 'shoot':
        bob = [2,0,-3,-2][f]
    elif row in ('smoke','drink','talk'):
        bob = -1 if (row == 'talk' and f == 1) or (row == 'smoke' and f == 5) else 0
    left,right,top,bottom = build(v)
    sy = top+2+bob
    # Arm L swings backward as leg L comes forward, then exchanges at f=3.
    if row.startswith('walk'):
        rear_hand,_=walk_hands(direction,f)
        shoulder = 15 if direction == 'right' else left
        elbow = ((shoulder+rear_hand[0])//2,sy+2)
        arm(d,(shoulder,sy),elbow,rear_hand,shade)
        legs,shoes=walk_parts(v,direction,f)
        for leg,shoe in zip(legs,shoes):
            im.alpha_composite(leg)
            im.alpha_composite(shoe)
    else:
        arm(d,(left,sy),(left-2,sy+2),(left-2,sy+4),shade)
        floor = 27 if row == 'shoot' and f in (2,3) else 28
        for x in (11,18):
            box(d,(x,bottom-1+bob,x+3,floor-1),uniform)
        for x,w in ((10,5),(18,4)):
            box(d,(x,floor-2,x+w,floor),'dark')
            d.line((x+1,floor-1,x+w-1,floor-1),fill=P['mid'])
    if v == 9:
        # One exposed neck pixel bridges the bucket rim to its lower shoulders.
        stroke(d,[(16,16+bob),(16,top+bob)],'steel',2)
    im.alpha_composite(torso_layer(v,bob,direction))
    d = ImageDraw.Draw(im)
    if v == GUARD:
        stroke(d,[(right+1,22+bob),(right+3,26)],'dark',1)
    h,dx,dy = moving_head(v,direction,row,f,bob)
    im.alpha_composite(h,(dx,dy))
    d = ImageDraw.Draw(im)
    hand = (23,23+bob)
    elbow = (23,21+bob)
    if row.startswith('walk'):
        _,hand = walk_hands(direction,f)
        elbow = ((19+hand[0])//2,sy+2) if direction == 'right' else (right+2,sy+1)
    elif row.startswith('idle'):
        # Four distinct slow poses, without sliding the feet.
        hand = [(23,23),(23,22),(22,23),(23,24)][f] if row!='idle_up' else [(23,23),(23,22)][f]
    elif row == 'wave':
        hand = [(24,12),(27,10),(24,8),(22,10)][f]
        elbow = (25,17)
    elif row == 'bump':
        hand = [(23,21),(27,18),(28,18),(24,20)][f]
        elbow = [(23,21),(24,19),(25,18),(23,20)][f]
    elif row == 'curl':
        hy = [24,19,14,19][f]
        ly = [14,19,24,19][f]
        arm(d,(12,sy),(9,21),(8,ly),uniform)
        dumbbell(d,7,ly)
        hand,elbow = (24,hy),(23,21)
    elif row == 'dribble':
        hand = [(25,18),(25,21),(25,24),(25,20)][f]
        elbow = (23,19)
    elif row == 'shoot':
        hand = [(24,18),(24,12),(23,5),(25,6)][f]
        elbow = [(23,21),(23,17),(22,11),(24,11)][f]
        arm(d,(12,sy),(17,hand[1]+4),(hand[0]-4,hand[1]),shade)
    elif row == 'smoke':
        hand = [(24,24),(25,19),(23,15),(23,15),(25,21),(24,24)][f]
        elbow = [(23,21),(24,21),(25,19),(25,18),(25,20),(23,21)][f]
        if v == 15:
            hand = [(24,24),(25,15),(23,9),(23,9),(25,18),(24,24)][f]
            elbow = (24,15 if f in (2,3) else 20)
    elif row == 'drink':
        hand = [(24,24),(26,19),(24,14),(24,13),(26,17),(25,22)][f]
        elbow = (24,20 if f in (0,1,4,5) else 18)
        if v == 15:
            hand = [(24,24),(26,16),(24,10),(24,9),(26,14),(25,22)][f]
            elbow = (24,14 if f in (2,3) else 20)
    elif row == 'talk':
        hand = (24,21-f)
        elbow = (23,20)
    shoulder = 19 if row=='walk_side' else right
    arm(d,(shoulder,sy),elbow,hand,uniform)
    if row == 'curl':
        dumbbell(d,25,hy)
    elif row == 'dribble':
        ball(d,26,[15,20,24,19][f],f)
    elif row == 'shoot' and f<3:
        ball(d,[24,24,23][f],[16,10,4][f],f)
    elif row == 'smoke':
        hx,hy=hand
        # Mouth contact frames point left; exhale frame has pursed grille.
        if f in (2,3):
            box(d,(21,hy-1,26,hy),'paper')
            d.rectangle((25,hy-1,26,hy),fill=P['red' if f==3 else 'shade'])
        else:
            box(d,(hx,hy,hx+5,hy+1),'paper')
            d.rectangle((hx+4,hy,hx+5,hy+1),fill=P['red'])
        if f==5:
            d.rectangle((21,8,22,9) if v==15 else (18,13,19,14),fill=P['ink'])
    elif row == 'drink':
        hx,hy=hand
        if f in (2,3):
            # Horizontal can, dark spout pressed to the mouth.
            box(d,(hx-1,hy-3,hx+5,hy+1),'blue')
            box(d,(hx+2,hy-5,hx+5,hy-3),'metal')
            d.line((hx,hy-2,hx+4,hy-2),fill=P['metal'])
            box(d,(hx-4,hy-1,hx-1,hy),'oil')
        else:
            box(d,(hx-2,hy-2,hx+3,hy+3),'blue')
            box(d,(hx,hy-4,hx+3,hy-2),'metal')
            d.line((hx-1,hy-1,hx+2,hy-1),fill=P['metal'])
            d.line((hx-3,hy-3,hx,hy-3),fill=P['ink'])
        if f==4:
            d.polygon([(22,17),(21,19),(21,20),(23,20),(23,19)],fill=P['oil'])
    return im


def checker(size):
    im=Image.new('RGBA',size,P['groundshade'])
    d=ImageDraw.Draw(im)
    for y in range(0,size[1],8):
        for x in range(0,size[0],8):
            if (x//8+y//8)%2==0:
                d.rectangle((x,y,x+7,y+7),fill=P['ground'])
    return im


def opaque_preview(im,scale):
    bg=checker(im.size)
    bg.alpha_composite(im)
    return bg.convert('RGB').resize((im.width*scale,im.height*scale),NEAREST)


def generate():
    ROOT.mkdir(exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)
    sheets=[]
    for v,(name,*_) in enumerate(VARIANTS):
        sheet=Image.new('RGBA',(192,544))
        for r,(row,n,_,_) in enumerate(ROWS):
            if v==GUARD and r not in (0,1,2,3,4,5,13):
                continue
            for f in range(n):
                sheet.alpha_composite(frame(v,row,f),(f*32,r*32))
        sheet.save(ROOT/f'{name}.png')
        opaque_preview(sheet,4).save(PREVIEW/f'sheet-{name}-4x.png')
        sheets.append(sheet)
    metadata={
        'frame':[32,32], 'anchor':[16,28],
        'rows':[dict(name=n,row=r,frames=c,fps=fps,facing=facing)
                for r,(n,c,fps,facing) in enumerate(ROWS)],
        'variants':[dict(file=f'{n}.png',head=h,antenna=a,eyes=e)
                    for n,h,a,e,_ in VARIANTS],
        'palette':sorted(set(P.values())),
        'guard_rows':[0,1,2,3,4,5,13],
        'press_bench':{'top_rect':[2,22,28,4],'centre':[16,24],
                       'baseline':28,'anchor':[16,28],
                       'note':'Hide the empty bench prop during press. Bench legs at x=5..6 and 25..26, y=25..28.'},
    }
    (ROOT/'robots.json').write_text(json.dumps(metadata,indent=2)+'\n')
    lineup=Image.new('RGBA',(32*len(VARIANTS),32),P['ground'])
    faces=Image.new('RGBA',(24*len(VARIANTS),22),P['ground'])
    for v,sheet in enumerate(sheets):
        first=sheet.crop((0,0,32,32))
        lineup.alpha_composite(first,(v*32,0))
        faces.alpha_composite(first.crop((4,0,28,22)),(v*24,0))
    lineup.convert('RGB').resize((lineup.width*3,96),NEAREST).save(PREVIEW/'lineup-3x.png')
    faces.convert('RGB').resize((faces.width*8,176),NEAREST).save(PREVIEW/'faces-8x.png')
    # Fixed palette GIF avoids quantisation colours and any temporal dithering.
    gifcolors=[P['ground']]+sorted(set(P.values())-{P['ground']})
    pal=Image.new('P',(1,1))
    raw=[int(c[i:i+2],16) for c in gifcolors for i in (1,3,5)]
    pal.putpalette(raw+[0]*(768-len(raw)))
    gif_jobs=[(0,r) for r in range(len(ROWS))]
    gif_jobs += [(v,r) for v in (9,10,15) for r in (3,4,6,16)]
    for v,r in gif_jobs:
        row,n,fps,_=ROWS[r]
        stem=row if v==0 else f'{row}-v{v}'
        frames=[]
        for f in range(n):
            rgba=sheets[v].crop((32*f,32*r,32*f+32,32*r+32))
            bg=Image.new('RGBA',(32,32),P['ground'])
            bg.alpha_composite(rgba)
            rgb=bg.convert('RGB').resize((192,192),NEAREST)
            frames.append(rgb.quantize(palette=pal,dither=Image.Dither.NONE))
        frames[0].save(PREVIEW/f'{stem}.gif',save_all=True,append_images=frames[1:],
                       duration=round(100/fps)*10,loop=0,optimize=False,disposal=2)
        # Review every saved GIF frame, not just the first frame.
        with Image.open(PREVIEW/f'{stem}.gif') as gif:
            strip=Image.new('RGB',(gif.width*gif.n_frames,gif.height),P['ground'])
            for i in range(gif.n_frames):
                gif.seek(i)
                strip.paste(gif.convert('RGB'),(i*gif.width,0))
            strip.save(PREVIEW/f'{stem}-gif-frames.png')
    # Four walk panels: down then side; v0 also includes up.
    for v in (0,9,10,15):
        names=[f'{row}' + (f'-v{v}' if v else '') for row in ('walk_down','walk_side')]
        if v==0:
            names.append('walk_up')
        panel=Image.new('RGB',(1152,192*len(names)),P['ground'])
        for i,stem in enumerate(names):
            with Image.open(PREVIEW/f'{stem}-gif-frames.png') as strip:
                panel.paste(strip,(0,192*i))
        panel.save(PREVIEW/f'walk-review-v{v}.png')
    # Two seated panels, each with variants 0,9,10,15 in that vertical order.
    for row in ('sit','sit_back'):
        panel=Image.new('RGB',(768,768),P['ground'])
        for i,v in enumerate((0,9,10,15)):
            stem=row+(f'-v{v}' if v else '')
            with Image.open(PREVIEW/f'{stem}-gif-frames.png') as strip:
                panel.paste(strip,(0,192*i))
        panel.save(PREVIEW/f'{row}-review.png')
    # Bench geometry alone is useful to the scene artist without touching scene/.
    ref=Image.new('RGBA',(32,32))
    bench(ImageDraw.Draw(ref))
    ref.save(ROOT/'bench-reference.png')
    return sheets


def check(sheets):
    out=['All statements in this block are MEASURED by assertions against saved artifacts.',
         'Frame indices are zero-based; combined walk shoe bounds centre exactly on x=16.',
         'Foot identity: separately rendered anatomical L/R shoe masks, compared to visible saved pixels.',
         'Seat measurement: isolated torso alpha bbox bottom minus 1, plus saved central underside ink scanline.',
         'Build measurement: isolated standing torso bbox (left,top,right-exclusive,bottom-exclusive).']
    allcolors=set()
    checked_frames=0
    walk_count=seat_count=idle_count=0
    for v,source in enumerate(sheets):
        name=VARIANTS[v][0]
        with Image.open(ROOT/f'{name}.png') as disk:
            assert disk.mode=='RGBA' and disk.size==(192,544),name
            sheet=disk.copy()
            assert sheet.tobytes()==source.tobytes(),name
        alpha=set(sheet.getchannel('A').getdata())
        assert alpha == {0,255},(name,alpha)
        allcolors|={rgb[:3] for rgb in sheet.getdata() if rgb[3]}
        out.append(f'{name}: 192 x 544 RGBA; alpha={sorted(alpha)}; standing torso={torso_layer(v).getbbox()}')
        glow=tuple(int(P[VARIANTS[v][4]][i:i+2],16) for i in (1,3,5))
        y0,y1 = (5,9) if v==15 else (6,14) if v==10 else (8,15)
        pixels={(x,y) for y in range(y0,y1) for x in range(6,27)
                if sheet.getpixel((x,y))[:3]==glow and sheet.getpixel((x,y))[3]}
        components=[]
        while pixels:
            todo=[pixels.pop()]; component=set(todo)
            while todo:
                x,y=todo.pop()
                for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if q in pixels:
                        pixels.remove(q); component.add(q); todo.append(q)
            components.append((max(x for x,y in component)-min(x for x,y in component)+1,
                               max(y for x,y in component)-min(y for x,y in component)+1))
        assert len(components)==(2 if v in (2,3,7,8,11,14,15,20,GUARD) else 1),(name,components)
        assert all(w>=2 and h>=2 for w,h in components),(name,components)
        out.append(f'  face glow components={sorted(components)}; each at least2x2 PASS')
        for r,(row,n,_,facing) in enumerate(ROWS):
            expected=0 if v==GUARD and r not in (0,1,2,3,4,5,13) else n
            cells=[sheet.crop((f*32,r*32,f*32+32,r*32+32)) for f in range(6)]
            assert [f for f,c in enumerate(cells) if c.getbbox()]==list(range(expected)),(name,row)
            if not expected:
                continue
            assert all(cells[f].tobytes()!=cells[(f+1)%expected].tobytes() for f in range(expected)),(name,row,'repeated adjacent frame')
            if row.startswith('walk') or row in ('sit','sit_back'):
                assert len({c.tobytes() for c in cells[:expected]})==expected,(name,row,'duplicate frame')
            checked_frames+=expected
            lows=[c.getbbox()[3]-1 for c in cells[:expected]]
            if row.startswith('idle'):
                for f,c in enumerate(cells[:expected]):
                    bob = (0,-1,0,1)[f] if row != 'idle_up' else (0,-1)[f]
                    rigid = head(v,facing,blink=(row=='idle_down' and f==2))
                    reference = Image.new('RGBA',(32,32))
                    reference.alpha_composite(rigid,(0,max(bob,-rigid.getbbox()[1])))
                    # Above the shoulders, saved pixels must preserve the
                    # entire casing, antenna and face without a horizontal split.
                    assert c.crop((0,0,32,14)).tobytes()==reference.crop((0,0,32,14)).tobytes(),(name,row,f,'skewed idle head')
                    idle_count+=1
            if row.startswith('walk'):
                assert n==6 and ROWS[r][2]==9
                assert lows==[28]*6,(name,row,lows)
                bottoms=[[],[]]
                centers=[[],[]]
                visible=[[],[]]
                for f,c in enumerate(cells[:expected]):
                    legs,shoes=walk_parts(v,facing,f)
                    for k,shoe in enumerate(shoes):
                        bbox=shoe.getbbox()
                        low=bbox[3]-1
                        bottoms[k].append(low)
                        centers[k].append((bbox[0]+bbox[2]-1)/2)
                        # Actual image must expose this shoe's lowest row in
                        # the same colours, outside the other shoe's mask.
                        xs=[x for x in range(32) if shoe.getpixel((x,low))[3]
                            and not shoes[1-k].getpixel((x,low))[3]
                            and c.getpixel((x,low))==shoe.getpixel((x,low))]
                        assert xs,(name,row,f,k,'shoe underside occluded')
                        visible[k].append(len(xs))
                    combined=[x for x in range(32) for k in (0,1)
                              if shoes[k].getchannel('A').getbbox() and
                              any(shoes[k].getpixel((x,y))[3] for y in range(24,29))]
                    assert (min(combined)+max(combined))/2==16
                l,rfoot=bottoms
                l_wins=[f for f in range(6) if l[f]>rfoot[f]]
                r_wins=[f for f in range(6) if rfoot[f]>l[f]]
                assert l_wins and r_wins,(name,row,bottoms)
                lifts=[sum(y<=26 for y in foot) for foot in bottoms]
                assert min(lifts)>=2,(name,row,lifts)
                hands=[walk_hands(facing,f) for f in range(6)]
                if facing=='right':
                    assert all((centers[0][f]-centers[1][f])*(hands[f][0][0]-hands[f][1][0])<0 for f in range(6)),(name,'arm swing x')
                else:
                    assert all(hands[f][0][1]<hands[f][1][1] for f in l_wins)
                    assert all(hands[f][1][1]<hands[f][0][1] for f in r_wins)
                torso_tops=[torso_layer(v,(0,1,0,0,1,0)[f],facing).getbbox()[1] for f in range(6)]
                assert [y-torso_tops[0] for y in torso_tops]==[0,1,0,0,1,0]
                crossing=''
                if row=='walk_side':
                    deltas=[centers[0][f]-centers[1][f] for f in range(6)]
                    assert min(deltas)<0<max(deltas)
                    legs,_=walk_parts(v,facing,2)
                    overlap=sum(bool(a and b) for a,b in zip(legs[0].getchannel('A').getdata(),legs[1].getchannel('A').getdata()))
                    assert overlap>0,(name,'no crossing leg pixels')
                    crossing=f'; L-R shoe x={deltas}; passing leg overlap={overlap}px'
                out.append(f'  {row}: 6 distinct @9fps; lowest={lows}; L shoe={l}; R shoe={rfoot}; strict L-low frames={l_wins}, R-low={r_wins}; lifted<=26 counts={lifts}; min exposed sole pixels={min(map(min,visible))}; opposite arm endpoints; bob=0,1,0,0,1,0{crossing} PASS')
                walk_count+=6
            elif row in ('sit','sit_back'):
                torso=torso_layer(v,direction=facing,seated=True)
                seat=torso.getbbox()[3]-1
                assert seat==24
                left,right,_,_=build(v)
                ink=tuple(int(P['ink'][i:i+2],16) for i in (1,3,5))+(255,)
                for f,c in enumerate(cells[:expected]):
                    assert all(c.getpixel((x,24))==ink for x in range(left+2,right-1)),(name,row,f,'seat not visible at24')
                out.append(f'  {row}: 4 distinct; torso underside={[seat]*4}; saved underside scanline x={left+2}..{right-2},y=24 PASS')
                seat_count+=4
            elif row!='press':
                expected_floor=[28]*expected
                if row=='shoot':
                    expected_floor=[28,28,27,27]
                assert lows==expected_floor,(name,row,lows)
                for c in cells[:expected]:
                    feet=[x for x in range(10,23) for y in range(26,29) if c.getpixel((x,y))[3]]
                    assert feet and abs((min(feet)+max(feet))/2-16)<=1,(name,row,'feet centre')
        with Image.open(PREVIEW/f'sheet-{name}-4x.png') as preview:
            assert preview.size==(768,2176)
    silhouettes=[list(im.crop((0,0,32,32)).getchannel('A').getdata()) for im in sheets[:GUARD]]
    pairs=[(sum(a!=b for a,b in zip(silhouettes[i],silhouettes[j])),i,j)
           for i in range(GUARD) for j in range(i+1,GUARD)]
    minimum=min(pairs)
    assert minimum[0]>0,minimum
    out.append(f'Inmate idle_down frame0 silhouettes: all {len(pairs)} pairs differ; minimum XOR opaque pixels={minimum[0]}, robot-{minimum[1]} vs robot-{minimum[2]} PASS')
    # Source head antennas must actually move on both down frames, relative to
    # the torso. The one-pixel offset is independent of the body's 1px bob.
    for v in (0,1,2,3,4,5,6,8):
        for direction in ('viewer','right','away'):
            base=head(v,direction)
            assert head(v,direction,antenna_dx=-1).tobytes()!=base.tobytes()
            assert head(v,direction,antenna_dx=1).tobytes()!=base.tobytes()
    out.append('Antenna-bearing types 0..6,8: down frames offset antenna -1/+1px relative to head; all 3 views differ PASS')
    # Bench contract remains independent of build or head.
    ref=Image.new('RGBA',(32,32)); bench(ImageDraw.Draw(ref))
    with Image.open(ROOT/'bench-reference.png') as disk:
        assert disk.tobytes()==ref.tobytes()
    for v in range(GUARD):
        for f in range(4):
            c=sheets[v].crop((f*32,7*32,f*32+32,8*32))
            for x in (5,6,25,26):
                assert c.getpixel((x,28))==ref.getpixel((x,28)),(v,f,'bench foot')
    out.append(f'Press bench: top rect [2,22,28,4], centre [16,24], baseline28; reference and all {4*GUARD} press-frame support pixels agree PASS')
    nvar=len(VARIANTS)
    with Image.open(PREVIEW/'lineup-3x.png') as im:
        assert im.size==(32*nvar*3,96)
    with Image.open(PREVIEW/'faces-8x.png') as im:
        assert im.size==(24*nvar*8,176)
    metadata=json.loads((ROOT/'robots.json').read_text())
    assert len(metadata['rows'])==17 and len(metadata['variants'])==nvar
    assert metadata['anchor']==[16,28] and metadata['guard_rows']==[0,1,2,3,4,5,13]
    out.append(f'Metadata: 17 rows, {GUARD} inmate variants + guard; anchor [16,28]; guard only rows0..5,13 PASS')
    out.append(f'Preview sizes: {nvar} sheets at4x; faces{24*nvar*8}x176 ({nvar} at8x), lineup{32*nvar*3}x96 ({nvar} at3x) PASS')
    artifact_colors=set()
    raster_count=0
    gif_count=0
    for path in sorted(ROOT.rglob('*')):
        if path.suffix not in ('.png','.gif'):
            continue
        raster_count+=1
        with Image.open(path) as im:
            for f in range(getattr(im,'n_frames',1)):
                im.seek(f)
                colors=im.convert('RGBA').getcolors(256)
                assert colors is not None,(path,'more than256 colours')
                for _,pixel in colors:
                    assert pixel[3] in (0,255),(path,'partial alpha')
                    if pixel[3]:
                        artifact_colors.add(pixel[:3])
    for v in (0,9,10,15):
        jobs=range(17) if v==0 else (3,4,6,16)
        for r in jobs:
            row,n,fps,_=ROWS[r]
            stem=row+(f'-v{v}' if v else '')
            with Image.open(PREVIEW/f'{stem}.gif') as gif:
                assert gif.n_frames==n and gif.size==(192,192) and gif.info.get('loop')==0,stem
                durations=[]
                for f in range(n):
                    gif.seek(f); durations.append(gif.info['duration'])
                assert set(durations)=={round(100/fps)*10},(stem,durations)
                out.append(f'GIF {stem}: {n} frames; looping; {durations[0]}ms/frame (JSON {fps}fps) PASS')
                gif_count+=1
    hexcolors={'#'+''.join(f'{c:02x}' for c in rgb) for rgb in allcolors}
    artifact_hex={'#'+''.join(f'{c:02x}' for c in rgb) for rgb in artifact_colors}
    assert hexcolors<=set(P.values())
    assert all(c[1:] in SPEC_PALETTE for c in artifact_hex)
    assert len(artifact_hex)<=40
    out.extend([f'Sheet opaque colours: {len(hexcolors)}; all raster opaque colours: {len(artifact_hex)} (limit40) PASS',
                'Sheet colours: '+', '.join(sorted(hexcolors)),
                f'Alpha only0/255 and palette compliance: every frame of all {raster_count} PNG/GIF files PASS',
                f'Frames: {checked_frames} populated; unused cells transparent; consecutive and loop poses differ; walk/seat frames all distinct PASS',
                f'Idle audit: {idle_count} frames, rigid head shapes in all 3 views with vertical bob and front blink PASS',
                f'Walk audit: {walk_count} frames, exact lowest y28, both anatomical feet strictly lowest and lifted<=26 at least twice per cycle PASS',
                f'Seat audit: {seat_count} frames, torso underside y24, front and back PASS',
                f'GIF audit: {gif_count} files PASS',
                'SELF-CHECK PASS'])
    return '\n'.join(out)


def write_report(output):
    nvar=len(VARIANTS)
    lines=[
        '# Robot sprite report — round 3', '',
        f'**Measured:** The single deterministic Pillow generator rebuilds robot-0 through robot-{GUARD-1} and guard ({nvar} variants), all 192 × 544 (6 × 17 cells). Walks have six distinct frames at 9 fps; sit and new row 16 sit_back have four frames each. Guard retains only rows 0–5 and 13. Anchor metadata remains (16,28).', '',
        '**Measured:** Walk phases are contact, down, passing, contact, down, passing. Anatomical left and right shoe layers are audited separately, including their exposed bottom pixels in the saved sheets. Strict support alternates; each foot lifts to row 26 twice. Side legs exchange horizontal order and intersect in the passing pose. Torso top offsets are [0,1,0,0,1,0]; antenna-bearing types use -1/+1 px horizontal antenna lag on the down frames. Arms swing in opposition. Idle counts remain 4/4/2 at 3 fps; vertical bob and hand motion prevent repeated consecutive poses. Idle heads retain their rigid shape, with a blink in the front view.', '',
        '**Measured:** Seat underside is measured from the isolated torso alpha bounding box (last occupied row = bbox bottom - 1), excluding arms, head and legs. A central ink scanline at y=24 is also checked against every saved seated frame. Both seated rows keep torso top18/bottom24 fixed. Front legs extend to row29; back legs are tucked to row26 with no shoes. Head motions are left, centre, right, nod (front) or shrug (back).', '',
        '**Measured:** From the original draw coordinates, round-1 used sit bob=3+frame, with torso bounds y=20..26 and y=21..27. Preserving those body positions and meeting an underside at y=24 simultaneously is impossible. This revision follows the explicit y=24 contract, raising the torso by 2/3px relative to those old poses; it never bobs during sit. This is the one requested constraint that could not be retained literally.', '',
        f'**Measured:** Round-2 types (8..15): television/rabbit ears/cyan; bucket/amber slot/stocky; glass bulb/amber filament/slim tall; toaster/two slots/red; hex nut/offset green lens/rust #a0522d; diving helmet/cyan porthole; small head/barrel body/green/stocky; periscope/binocular/red/slim. Round-3 types (16..21): padlock/U-shackle/amber keyhole; traffic signal/red-amber-green/slim; reel-to-reel tape deck/cyan readout; flash camera/cyan lens barrel; safety cone/white band/green eyes; parking meter/red expired flag/slim. Standard/stocky/slim torso widths are 11/13/9px; stocky legs are 1px shorter and bulb legs 1px longer. Build bounds are in the check output. All {GUARD*(GUARD-1)//2} inmate silhouette pairs differ in alpha.', '',
        f'**Measured:** Deliverables include {nvar} sheet previews at4x, faces with all{nvar} at8x, lineup with all{nvar} at3x, 29 looping GIFs at6x and 29 strips decoded from the GIFs. Four walk review panels cover variants0/9/10/15 (down then side; v0 also up). Two seated review panels cover sit and sit_back, each top-to-bottom variants0/9/10/15.', '',
        '**Measured:** The press bench geometry remains top rect [2,22,28,4], centre(16,24), baseline28. The bench function was retained; bench-reference.png is regenerated. Rust uses the existing SPEC colour. All raster colours stay within the SPEC palette and total40 limit.', '',
        '**Measured:** GIF durations round to10ms: 9fps→110ms, 3fps→330ms, 7fps→140ms, 5fps→200ms, 2fps→500ms; exact requested fps stay in JSON. The jump shot retains feet at y27 in frames2/3; other standing frames end at y28.', '',
    ]
    if VIEWED_NOTES:
        lines.extend('**Viewed:** '+note+'\n' for note in VIEWED_NOTES)
    else:
        lines+=['**Not checked:** Preview visual review pending.','']
    lines += [
        '**Not checked:** Live engine playback at30px/s, alignment against the separate scene table/bench assets, and subjective recognition by other viewers at2x. GIF review uses all decoded frames, not real-time playback timing. The rear seating row requires the engine to select sit_back for near-side seats.', '',
        '**Measured — self-check output (every line in this block is measured):**', '', '```text',output,'```','',
    ]
    (ROOT/'REPORT.md').write_text('\n'.join(lines))


if __name__=='__main__':
    sheets=generate()
    def hashes():
        return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(ROOT.rglob('*')) if p.suffix in ('.png','.gif','.json')}
    first_hashes=hashes()
    sheets=generate()
    assert hashes()==first_hashes,'Non-deterministic rebuild'
    output=check(sheets)
    output+=f'\nDeterminism: two full builds byte-identical (SHA-256), {len(first_hashes)} PNG/GIF/JSON files: PASS'
    (ROOT/'self-check.txt').write_text(output+'\n')
    write_report(output)
    print(output)

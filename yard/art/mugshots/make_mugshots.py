#!/usr/bin/env python3
"""Booking portraits. Pillow + Python stdlib only; all writes stay beside this file.

Run: python3 mugshots/make_mugshots.py
The source module is imported without bytecode writes or running its generator.
Head/antenna/eye descriptors and body widths come from that module, not a second
character list. Unrecognised descriptors fail instead of drifting.
"""
from pathlib import Path
import sys
import importlib.util
import hashlib
import json
from itertools import combinations
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
PREVIEW = ROOT / 'preview'
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('yard_robots', ROOT.parent / 'robots/make_robots.py')
yard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yard)
TYPES = yard.VARIANTS[:yard.GUARD]
N_TYPES = len(TYPES)
assert N_TYPES == 22
P = dict(yard.P, wall='#1c2420')
# No added mid-tones: all colours, including the one-pixel eye cores, are existing.
ADDED_METAL = []
SIZE = (100, 85)
PLACARD = (28, 61, 44, 20)
NN = Image.Resampling.NEAREST
VIEWED_NOTES = [
    'Opened match-6x.png and all-front-4x.png, then pairs-3x.png. The red visor/spring, tall red cyclops, wide angry twins, amber twins, curly amber visor, round amber cyclops, cyan dome and green ear-bolt box read as the corresponding yard types 0–7. Raised the tall-box casing after the first review and kept its red ball inside the frame.',
    'The CRT aerials and knobs, bucket rim and stocky shoulders, dark bulb/filament and slim body, toaster slots, rusty six-sided nut/offset lens, diving porthole, small head/barrel body and bent binocular neck distinguish types 8–15 in the match preview. Re-centred the toaster including its lever and made the bulb taller. No front pair looked interchangeable to me; 0/4 share the most geometry, distinguished by red/spring versus amber/curly wire.',
    'Opened all-side-4x.png and pairs-3x.png. Profiles show one front eye or a narrow visor/screen at the left, rear service panels/vents to the right, and a turned shoulder. The near ear bearing is visible on types 7/13. Rivets, seams, welded patches on 0/9, soot at the toaster slots, nut rust and lens cracks on 1/13 add wear without changing the identifying shapes. No wall, bars, tally marks, booking text or other scene furniture appears in the portraits.',
    'Opened pairs-3x.png, match-6x.png, and portraits mug-16..mug-21 (front and side). The padlock U-shackle/keyhole, traffic signal three-lens visors, reel-to-reel spools, flash camera lens barrel, safety cone reflective band, and parking meter expired flag match yard variants 16–21 cleanly from both front and left-profile angles.',
]


def rgb(c):
    c = P.get(c, c)
    return tuple(int(c[j:j+2], 16) for j in (1, 3, 5))


def canvas():
    return Image.new('RGBA', SIZE, (0, 0, 0, 0))


def opaque_colors(im):
    return {'#%02x%02x%02x'%p[:3] for _,p in im.convert('RGBA').getcolors(1<<24) if p[3]}


def rect(d, b, c='mid', edge=True):
    d.rectangle(b, fill=P.get(c,c), outline=P['ink'] if edge else None)


def line(d, pts, c='ink', w=1):
    d.line(pts, fill=P.get(c,c), width=w)


def metal(im, bounds=None, polygon=None, ellipse=False, fill='mid'):
    """Hard metal surface, four-connected 1px outer contour, top-left lighting."""
    mask = Image.new('L', SIZE)
    md = ImageDraw.Draw(mask)
    if polygon:
        md.polygon(polygon, fill=255)
    elif ellipse:
        md.ellipse(bounds, fill=255)
    else:
        md.rectangle(bounds, fill=255)
    box = mask.getbbox()
    x0,y0,x1,y1 = box
    pix = mask.load()
    for y in range(y0,y1):
        for x in range(x0,x1):
            if not pix[x,y]:
                continue
            boundary = any(not (0 <= x+dx < 100 and 0 <= y+dy < 85) or not pix[x+dx,y+dy]
                           for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)))
            c = 'ink' if boundary else fill
            if not boundary:
                if not pix[max(0,x-2),y] or not pix[x,max(0,y-2)]:
                    c = 'metal'
                elif not pix[min(99,x+3),y] or not pix[x,min(84,y+3)]:
                    c = 'steel'
            im.putpixel((x,y), (*rgb(c),255))
    return box


def rivet(d,x,y):
    rect(d,(x-1,y-1,x+1,y+1),'dark',False)
    d.point((x-1,y-1),fill=P['metal'])
    d.point((x,y),fill=P['steel'])


def vents(d,x,y,n=3):
    for j in range(n):
        line(d,(x,y+j*3,x+7,y+j*3),'dark')
        line(d,(x,y+j*3+1,x+6,y+j*3+1),'metal')


def lens(d,b,col,round_=False,crack=False):
    draw = d.ellipse if round_ else d.rectangle
    draw(b,fill=P['ink'])
    a,t,c,z=b
    draw((a+2,t+2,c-2,z-2),fill=P[col])
    # A single-pixel-wide lighter line sits *inside* the coloured emitter.
    if round_:
        cx,cy=a+(c-a)//3,t+(z-t)//3
        line(d,(cx,cy,cx+max(1,(c-a)//6),cy),'paper')
    elif c-a>=8:
        line(d,(a+3,t+3,min(c-3,a+6),t+3),'paper')
    else:
        d.point((a+2,t+2), fill=P['paper'])
    if crack:
        line(d,[(c-4,t+2),(c-5,t+5),(c-3,t+7),(c-5,z-2)],'dark')


def visor(d,b,col):
    rect(d,b,'ink')
    a,t,c,z=b
    rect(d,(a+2,t+2,c-2,z-2),col,False)
    line(d,(a+3,t+3,c-4,t+3),'paper')


def patch(d,x,y):
    rect(d,(x,y,x+8,y+6),'steel')
    line(d,(x+1,y+1,x+6,y+1),'metal')
    for px,py in ((x,y+2),(x+3,y),(x+6,y+6),(x+8,y+3)):
        d.point((px,py),fill=P['metal'])


def antenna(im,desc,col,top,side=False):
    d=ImageDraw.Draw(im)
    if desc=='none':
        return
    if desc=='coil spring':
        # Square-wire spring; consistent zigzag with the yard sprite.
        line(d,[(50,top),(50,top-3),(45,top-5),(53,top-8),
                (45,top-11),(51,top-14)],'ink',3)
        line(d,[(50,top-1),(50,top-3),(46,top-5),(52,top-8),
                (46,top-11),(51,top-14)],'steel')
        d.point((49,top-9),fill=P['metal'])
    elif desc in ('single rod, red ball tip','single rod'):
        rod_top=max(6,top-12)
        line(d,(50,top,50,rod_top),'ink',3)
        line(d,(50,top-1,50,rod_top+1),'metal')
        if 'ball' in desc:
            tip=max(2,top-17)
            d.ellipse((46,tip,54,tip+8),fill=P['red'],outline=P['ink'])
            line(d,(48,tip+2,49,tip+2),'paper')
        else:
            rect(d,(47,top-15,53,top-10),'metal')
    elif desc.startswith('twin rods'):
        for x in ((46,53) if side else (36,64)):
            line(d,(x,top,x,top-10),'ink',3)
            line(d,(x,top-1,x,top-10),'steel')
            rect(d,(x-3,top-15,x+3,top-10),col)
            d.point((x-2,top-14),fill=P['paper'])
    elif desc=='curly wire':
        pts=[(48,top),(47,top-5),(56,top-8),(56,top-14),(47,top-14),(44,top-10)]
        line(d,pts,'ink',3)
        line(d,pts,'steel')
        line(d,(48,top-14,53,top-14),'metal')
    elif desc=='rabbit ears':
        for pts in ([ (46,top),(38,top-11),(34,top-13)],
                    [(54,top),(62,top-13),(65,top-14)]):
            line(d,pts,'ink',3)
            line(d,pts,'steel')
            d.point(pts[-1],fill=P['metal'])
    else:
        raise ValueError('New yard antenna requires a portrait renderer: '+desc)


# Keys are the imported yard head descriptors, not variant numbers.
KINDS={
    'box':'box', 'tall box':'tall', 'wide box':'wide',
    'round':'round', 'dome':'dome', 'wide box with ear bolts':'ears',
    'television':'tv', 'upturned bucket, stocky':'bucket',
    'glass bulb, slim tall':'bulb', 'toaster, two top slots':'toaster',
    'hexagonal nut, rust accents':'nut', 'diving helmet':'diver',
    'small head, barrel body, stocky':'small',
    'binocular head, periscope neck, slim':'bino',
    'padlock with U-shackle':'padlock', 'traffic signal, slim':'signal',
    'reel-to-reel tape deck':'reel', 'flash camera':'camera',
    'safety cone, white band':'cone', 'parking meter, slim':'meter',
}


def metal_mask(im, mask, fill='mid'):
    """Apply metal() 1px contour + top-left lighting to an arbitrary L-mode mask."""
    box = mask.getbbox()
    x0,y0,x1,y1 = box
    pix = mask.load()
    for y in range(y0,y1):
        for x in range(x0,x1):
            if not pix[x,y]:
                continue
            boundary = any(not (0 <= x+dx < 100 and 0 <= y+dy < 85) or not pix[x+dx,y+dy]
                           for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)))
            c = 'ink' if boundary else fill
            if not boundary:
                if not pix[max(0,x-2),y] or not pix[x,max(0,y-2)]:
                    c = 'metal'
                elif not pix[min(99,x+3),y] or not pix[x,min(84,y+3)]:
                    c = 'steel'
            im.putpixel((x,y), (*rgb(c),255))
    return box


def head(v,side=False):
    _,desc,ant,eyes,col=TYPES[v]
    kind=KINDS[desc]
    im=canvas()
    # The front top positions leave both antenna and cranial casing in-frame.
    top={'tall':14,'bulb':9,'bino':13,'small':28}.get(kind,22)
    antenna(im,ant,col,top,side)
    d=ImageDraw.Draw(im)
    l,r=(30,70)
    if kind=='tall': l,r=32,68
    if kind in ('wide','tv','bucket','toaster','nut','diver','bino'): l,r=29,72
    if kind in ('round','bulb'): l,r=31,69
    if kind=='small': l,r=32,68
    if side:
        return profile(im,kind,col,eyes,top,l,r)
    if kind in ('box','tall','wide','ears','small'):
        metal(im,(l,top,r,49 if kind!='small' else 46))
        d=ImageDraw.Draw(im)
        if kind=='ears':
            for a,b in ((28,31),(69,71)):
                metal(im,(a,32,b,40),fill='dark')
            d=ImageDraw.Draw(im)
        # Lid seam, jaw seam, fixing screws. Character remains flat-faced.
        line(d,(l+3,top+5,r-3,top+5),'steel')
        for x in (l+3,r-3): rivet(d,x,top+3)
        if 'visor' in eyes:
            visor(d,(l+4,top+9,r-4,top+17),col)
        elif 'one big round' in eyes:
            lens(d,(40,24,60,44),col,True,crack=True)
            vents(d,46,47,1)
        else:
            ey=top+9
            if kind=='small': ey=33
            for x in (l+6,r-14):
                lens(d,(x,ey,x+9,ey+9),col,kind=='ears')
            if 'angry' in eyes:
                line(d,[(l+5,ey-3),(l+15,ey-1)],'ink')
                line(d,[(r-15,ey-1),(r-5,ey-3)],'ink')
        if kind!='tall':
            gy=44 if kind!='small' else 44
            line(d,(44,gy,56,gy),'dark')
            for x in range(45,57,3): d.point((x,gy),fill=P['metal'])
        if kind=='box' and 'red'==col:
            patch(d,32,40)
        elif kind=='wide':
            line(d,[(63,44),(61,46),(64,46)],'dark')
        elif kind=='ears':
            vents(d,32,43,1)
    elif kind=='round':
        metal(im,(31,22,69,49),ellipse=True)
        d=ImageDraw.Draw(im)
        lens(d,(40,27,60,46),col,True)
        rivet(d,36,35); rivet(d,64,35)
        line(d,[(58,46),(60,44),(63,44)],'dark')
    elif kind=='dome':
        metal(im,polygon=[(30,49),(30,34),(32,29),(37,24),(42,22),
                          (58,22),(63,24),(68,29),(70,34),(70,49)])
        d=ImageDraw.Draw(im)
        visor(d,(34,33,66,41),col)
        line(d,(42,45,57,45),'dark')
        rivet(d,34,45); rivet(d,66,45)
        line(d,[(36,29),(40,27),(44,27)],'metal')
    elif kind=='tv':
        metal(im,(28,22,71,49),fill='dark')
        d=ImageDraw.Draw(im)
        rect(d,(31,26,63,45),'steel')
        rect(d,(33,28,61,43),'ink',False)
        for x in (36,50): lens(d,(x,31,x+8,39),col)
        for y in (29,39):
            d.ellipse((65,y,69,y+4),fill=P['mid'],outline=P['ink'])
            d.point((66,y+1),fill=P['metal'])
        line(d,(33,47,58,47),'steel')
        rivet(d,69,46)
    elif kind=='bucket':
        metal(im,polygon=[(37,22),(63,22),(69,44),(71,47),(28,47),(30,44)])
        metal(im,(28,45,71,49),fill='steel')
        d=ImageDraw.Draw(im)
        visor(d,(40,32,65,40),col)
        line(d,(37,26,63,26),'steel')
        patch(d,32,36)
        rivet(d,32,47); rivet(d,68,47)
    elif kind=='bulb':
        metal(im,(32,9,68,46),ellipse=True,fill='dark')
        d=ImageDraw.Draw(im)
        # Opaque dark glass, as in the yard; no partial-alpha glow.
        line(d,[(35,28),(35,21),(39,16),(46,13),(51,13)],'metal')
        line(d,[(65,25),(65,32),(62,37)],'steel')
        line(d,[(43,42),(43,30),(50,22),(57,30),(57,42)],'amber',3)
        line(d,(44,37,56,37),'amber',3)
        line(d,[(43,39),(43,30),(49,23)],'paper')
        metal(im,(40,44,60,51),fill='steel')
        d=ImageDraw.Draw(im)
        for y in (46,49): line(d,(42,y,58,y),'dark')
    elif kind=='toaster':
        metal(im,(29,26,68,49))
        metal(im,(33,19,64,27),fill='metal')
        d=ImageDraw.Draw(im)
        for x in (38,54):
            rect(d,(x,21,x+8,24),'ink',False)
            line(d,(x+1,25,x+7,25),'steel')
        metal(im,(69,32,72,38),fill='dark')
        d=ImageDraw.Draw(im)
        for x in (35,53): lens(d,(x,33,x+9,41),col)
        vents(d,46,44,1)
        # Flat soot stains under the slots, rather than random noise.
        line(d,(34,28,42,28),'dark'); line(d,(58,28,66,28),'dark')
        rivet(d,32,46); rivet(d,65,46)
    elif kind=='nut':
        metal(im,polygon=[(38,20),(62,20),(72,32),(65,49),(35,49),(29,34)])
        d=ImageDraw.Draw(im)
        line(d,[(38,23),(32,33),(35,40)],'rust',3)
        line(d,[(59,47),(64,44),(66,40)],'rust',2)
        lens(d,(36,28,57,46),col,True)
        line(d,(64,26,67,31),'metal')
        line(d,[(61,35),(65,35),(63,38)],'dark')
    elif kind=='diver':
        metal(im,(31,19,69,49),ellipse=True)
        for x in (28,69): metal(im,(x,31,x+2,40),fill='steel')
        metal(im,(35,47,65,51),fill='steel')
        d=ImageDraw.Draw(im)
        lens(d,(36,24,64,47),col,True,crack=True)
        # Porthole bezel fasteners, outside the luminous glass.
        for x,y in ((50,25),(38,35),(62,35),(50,46)): rivet(d,x,y)
        line(d,[(32,29),(35,24),(40,22)],'metal')
    elif kind=='bino':
        metal(im,(28,16,71,30),fill='dark')
        for x in (28,54):
            metal(im,(x,13,min(71,x+18),33))
            d=ImageDraw.Draw(im)
            lens(d,(x+3,19,x+15,30),col)
        d=ImageDraw.Draw(im)
        line(d,(47,25,53,25),'steel')
    elif kind=='padlock':
        # Open U-shackle arch above chamfered lock casing
        m=Image.new('L',SIZE); md=ImageDraw.Draw(m)
        md.ellipse((34,6,66,38),fill=255)
        md.rectangle((34,20,66,26),fill=255)
        md.ellipse((42,14,58,30),fill=0)
        md.rectangle((42,20,58,26),fill=0)
        metal_mask(im,m)
        metal(im,polygon=[(32,24),(67,24),(70,27),(70,46),(67,49),(32,49),(29,46),(29,27)])
        d=ImageDraw.Draw(im)
        for rx,ry in ((34,28),(65,28),(34,45),(65,45)): rivet(d,rx,ry)
        rect(d,(42,28,57,46),'steel')
        d.ellipse((45,30,54,39),fill=P['ink'])
        d.rectangle((47,36,52,44),fill=P['ink'])
        d.ellipse((46,31,53,38),fill=P[col])
        d.rectangle((48,36,51,43),fill=P[col])
        line(d,(47,33,49,33),'paper')
    elif kind=='signal':
        metal(im,(43,4,56,9),fill='steel')
        for y in (14,25,36):
            metal(im,(30,y,37,y+7),fill='dark')
            metal(im,(63,y,70,y+7),fill='dark')
        metal(im,(36,9,63,49),fill='steel')
        d=ImageDraw.Draw(im)
        for y,sc in ((13,'red'),(25,'amber'),(37,'green')):
            lens(d,(43,y,56,y+10),sc,True)
        for y in (11,47): rivet(d,40,y); rivet(d,59,y)
    elif kind=='reel':
        for cx in (39,61):
            metal(im,(cx-10,8,cx+10,28),ellipse=True,fill='metal')
            d=ImageDraw.Draw(im)
            d.ellipse((cx-6,12,cx+6,24),fill=P['dark'],outline=P['ink'])
            d.ellipse((cx-2,16,cx+2,20),fill=P['metal'],outline=P['ink'])
            d.point((cx,18),fill=P['ink'])
        metal(im,(29,23,71,49),fill='steel')
        d=ImageDraw.Draw(im)
        rivet(d,33,27); rivet(d,67,27)
        visor(d,(34,31,60,41),col)
        d.ellipse((63,34,67,38),fill=P['red'],outline=P['ink'])
        for x in (36,42,48,54):
            rect(d,(x,44,x+4,46),'mid')
    elif kind=='camera':
        metal(im,(33,8,49,22),fill='dark')
        d=ImageDraw.Draw(im)
        rect(d,(36,11,46,19),'paper')
        line(d,(38,14,44,14),'amber')
        line(d,(38,16,44,16),'amber')
        metal(im,(55,16,66,22),fill='steel')
        d=ImageDraw.Draw(im)
        rect(d,(58,12,64,16),'red')
        metal(im,(29,21,71,49))
        d=ImageDraw.Draw(im)
        rect(d,(30,34,70,48),'dark',False)
        line(d,(30,34,70,34),'ink')
        metal(im,(33,25,54,46),ellipse=True,fill='steel')
        d=ImageDraw.Draw(im)
        lens(d,(36,28,51,43),col,True)
        rect(d,(58,26,66,32),'ink')
        rect(d,(59,27,65,31),'steel',False)
        d.ellipse((65,22,68,25),fill=P['red'],outline=P['ink'])
    elif kind=='cone':
        # Pointed safety cone with white band and dark rubber base
        d.polygon([(47,6),(52,6),(68,44),(32,44)],fill=P['orange'],outline=P['ink'])
        line(d,[(48,7),(34,43)],'light',2)
        line(d,[(52,7),(66,43)],'shade',2)
        d.polygon([(43,17),(57,17),(60,26),(40,26)],fill=P['paper'],outline=P['ink'])
        line(d,[(56,18),(58,25)],'metal')
        rect(d,(37,28,63,38),'ink')
        lens(d,(39,29,48,37),col)
        lens(d,(52,29,61,37),col)
        metal(im,(29,43,71,49),fill='dark')
        d=ImageDraw.Draw(im)
        rivet(d,33,46); rivet(d,67,46)
    elif kind=='meter':
        metal(im,polygon=[(42,7),(58,7),(65,11),(69,18),(69,49),(31,49),(31,18),(35,11)])
        d=ImageDraw.Draw(im)
        d.polygon([(42,13),(58,13),(64,18),(64,36),(36,36),(36,18)],fill=P['ink'])
        rect(d,(38,18,62,34),'paper')
        rect(d,(39,19,51,29),col,False)
        rect(d,(54,22,59,29),'green',False)
        for x in range(41,60,3): line(d,(x,31,x,33),'dark')
        rect(d,(47,40,53,45),'dark')
        line(d,(49,41,51,41),'ink')
        rivet(d,36,42); rivet(d,64,42)
    else:
        raise ValueError(kind)
    return im


def profile(im,kind,col,eyes,top,l,r):
    """Actual left-facing casings: front plane on left, service panel on right."""
    # Profile depths differ; all remain chest-up with the original antenna.
    l,r=({ 'tall':(34,65),'small':(35,65),'bino':(29,70),
           'tv':(29,71),'bucket':(29,71),'bulb':(32,68),
           'padlock':(32,68),'signal':(37,65),'reel':(32,69),
           'camera':(34,69),'cone':(30,70),'meter':(33,67)}.get(kind,(30,70)))
    if kind in ('box','tall','wide','ears','small'):
        metal(im,(l,top,r,46 if kind=='small' else 49))
    elif kind in ('round','diver','bulb'):
        metal(im,(l,10 if kind=='bulb' else 19 if kind=='diver' else 22,r,47),
              ellipse=True,fill='dark' if kind=='bulb' else 'mid')
    elif kind=='dome':
        metal(im,polygon=[(l,49),(l,34),(l+4,27),(l+12,22),
                          (r-12,22),(r-4,27),(r,34),(r,49)])
    elif kind=='bucket':
        metal(im,polygon=[(37,22),(62,22),(69,44),(71,47),(29,47),(31,44)])
        metal(im,(29,45,71,49),fill='steel')
    elif kind=='tv':
        metal(im,(29,22,71,49),fill='dark')
    elif kind=='toaster':
        metal(im,(30,26,70,49)); metal(im,(34,19,66,27),fill='metal')
    elif kind=='nut':
        metal(im,polygon=[(39,20),(61,20),(70,32),(63,49),(37,49),(30,34)])
    elif kind=='bino':
        metal(im,(30,16,70,30),fill='dark')
        metal(im,(29,13,43,33)); metal(im,(43,15,66,31),fill='steel')
    elif kind=='padlock':
        metal(im,polygon=[(46,6),(54,6),(56,9),(56,25),(44,25),(44,9)],fill='mid')
        metal(im,polygon=[(34,24),(66,24),(68,27),(68,46),(66,49),(34,49),(32,46),(32,27)])
    elif kind=='signal':
        metal(im,(44,4,55,9),fill='steel')
        metal(im,(l,9,r,49),fill='steel')
        for y in (12,24,36):
            metal(im,(29,y,38,y+4),fill='dark')
    elif kind=='reel':
        metal(im,(38,10,44,24),fill='steel')
        metal(im,(30,8,38,26),fill='metal')
        metal(im,(l,23,r,49),fill='steel')
    elif kind=='camera':
        metal(im,(36,8,52,22),fill='dark')
        metal(im,(53,16,60,22),fill='steel')
        metal(im,(l,21,r,49))
        metal(im,(25,25,36,45),fill='steel')
    elif kind=='cone':
        d=ImageDraw.Draw(im)
        d.polygon([(47,6),(52,6),(67,44),(33,44)],fill=P['orange'],outline=P['ink'])
        line(d,[(48,7),(35,43)],'light',2)
        d.polygon([(43,17),(57,17),(59,26),(41,26)],fill=P['paper'],outline=P['ink'])
        line(d,[(56,18),(57,25)],'metal')
        metal(im,(l,43,r,49),fill='dark')
    elif kind=='meter':
        metal(im,polygon=[(42,7),(58,7),(63,11),(67,18),(67,49),(33,49),(33,18),(37,11)],fill='steel')
    else:
        raise ValueError(kind)
    d=ImageDraw.Draw(im)
    if kind=='bulb':
        line(d,[(36,28),(36,20),(40,15),(47,13)],'metal')
        line(d,[(43,41),(43,29),(48,23),(53,29),(53,41)],col,3)
        line(d,[(43,38),(43,29),(47,24)],'paper')
        line(d,(44,36,52,36),col,3)
        metal(im,(40,44,60,51),fill='steel')
        d=ImageDraw.Draw(im)
        for y in (46,49): line(d,(42,y,58,y),'dark')
        return im
    if kind=='bino':
        lens(d,(30,19,39,29),col)
        line(d,(46,18,62,18),'metal')
        vents(d,51,22,2)
        return im
    if kind=='padlock':
        line(d,(52,28,52,44),'dark')
        vents(d,56,33,3); rivet(d,61,29)
        rect(d,(33,29,41,44),'ink')
        d.rectangle((34,31,38,42),fill=P[col])
        line(d,(35,33,37,33),'paper')
        return im
    if kind=='signal':
        line(d,(52,14,52,44),'dark')
        vents(d,55,29,3); rivet(d,60,14)
        for y,sc in ((14,'red'),(26,'amber'),(38,'green')):
            lens(d,(35,y,44,y+8),sc,True)
        return im
    if kind=='reel':
        line(d,(52,27,52,44),'dark')
        vents(d,56,33,3); rivet(d,63,27)
        visor(d,(33,31,47,41),col)
        return im
    if kind=='camera':
        rect(d,(37,11,43,19),'paper')
        line(d,(38,14,42,14),'amber')
        rect(d,(35,34,68,48),'dark',False)
        line(d,(35,34,68,34),'ink')
        line(d,(53,26,53,44),'dark')
        vents(d,57,35,3); rivet(d,63,26)
        rect(d,(25,27,33,43),'ink')
        rect(d,(26,28,31,42),col,False)
        line(d,(27,30,27,36),'paper')
        return im
    if kind=='cone':
        rect(d,(36,28,49,38),'ink')
        lens(d,(37,29,47,37),col)
        rivet(d,61,46)
        return im
    if kind=='meter':
        line(d,(52,14,52,44),'dark')
        vents(d,56,31,3); rivet(d,61,20)
        d.polygon([(35,16),(45,16),(48,19),(48,34),(34,34),(34,19)],fill=P['ink'])
        rect(d,(35,19,46,32),'paper')
        rect(d,(36,20,43,29),col,False)
        line(d,(37,40,42,40),'dark')
        return im
    # Rear casing seam, vents and the ear bearing on the near side.
    sx=54 if kind!='tall' else 52
    line(d,(sx,top+5,sx,44),'dark')
    vents(d,sx+4,33,3 if kind!='small' else 2)
    rivet(d,sx+7,top+4)
    if kind in ('ears','diver'):
        metal(im,(55,30,65,39),fill='steel')
        d=ImageDraw.Draw(im)
        rect(d,(58,33,62,36),'dark')
        line(d,(59,33,61,33),'metal')
    if kind=='toaster':
        for x in (38,51): rect(d,(x,21,x+7,24),'ink',False)
        metal(im,(70,32,73,38),fill='dark')
        d=ImageDraw.Draw(im)
        line(d,(35,28,43,28),'dark')
    if kind=='nut':
        line(d,[(39,23),(33,33),(36,40)],'rust',3)
        lens(d,(30,29,45,44),col,True)
    elif kind=='diver':
        metal(im,(28,26,40,44),fill='dark')
        d=ImageDraw.Draw(im)
        lens(d,(28,28,38,42),col,True,True)
        metal(im,(35,47,65,51),fill='steel')
    elif kind=='tv':
        rect(d,(29,27,42,44),'steel')
        rect(d,(30,29,39,42),'ink',False)
        lens(d,(31,32,38,40),col)
        line(d,(46,26,46,45),'steel')
    elif 'visor' in eyes or 'slot eye' in eyes:
        visor(d,(l+1,top+10,l+17,top+18),col)
    elif 'one big' in eyes:
        lens(d,(l+1,top+7,l+19,top+24),col,True,kind=='tall')
    else:
        ey=33 if kind in ('small','toaster') else top+9
        lens(d,(l+2,ey,l+13,ey+10),col,kind=='ears')
        if 'angry' in eyes: line(d,(l+1,ey-3,l+14,ey-1),'ink')
    d=ImageDraw.Draw(im)
    if kind=='box' and col=='red': patch(d,55,42)
    if kind=='bucket': patch(d,56,37)
    return im


def shoulders(v,side=False):
    """Widths come from yard.build(); the barrel retains its rounded shoulders."""
    im=canvas(); d=ImageDraw.Draw(im)
    _,desc,_,_,_=TYPES[v]
    kind=KINDS[desc]
    bl,br,_,_=yard.build(v)
    width=br-bl+1
    half={9:26,11:33,13:40}[width]
    l,r=50-half,50+half
    neck_top=47
    # Telescoping periscope is deliberately long, bent and thin.
    if kind=='bino':
        rect(d,(48,35,54,58),'steel')
        rect(d,(48,32,62,38),'steel')
        rect(d,(56,28,62,35),'steel')
        line(d,(49,40,49,54),'metal')
        for y in (43,49,55): line(d,(49,y,53,y),'dark')
    else:
        nw=5 if width==9 else 10 if width==13 else 8
        rect(d,(50-nw,neck_top,50+nw,58),'steel')
        line(d,(51-nw,49,51-nw,56),'metal')
        for y in (51,54,57): line(d,(52-nw,y,48+nw,y),'dark')
    shoulder_top=54 if width==13 else 56
    if side:
        half={9:23,11:27,13:34}[width]
        l,r=52-half,52+half
        if kind=='small': shoulder_top=53
        pts=[(l,84),(l+1,shoulder_top+14),(l+6,shoulder_top+7),
             (40,shoulder_top+1),(55,shoulder_top),(r-8,shoulder_top+4),
             (r-2,shoulder_top+12),(r,shoulder_top+21),(r,84)]
        d.polygon(pts,fill=P['orange'],outline=P['ink'])
        line(d,(l+1,84,r-1,84),'orange')
        line(d,[(l+2,83),(l+3,shoulder_top+14),(l+7,shoulder_top+8),
                (40,shoulder_top+3)],'light',2)
        d.polygon([(r-9,shoulder_top+8),(r-2,shoulder_top+15),(r-1,84),
                   (r-9,84)],fill=P['shade'])
        d.polygon([(40,shoulder_top+1),(48,shoulder_top+6),
                   (43,shoulder_top+11)],fill=P['light'],outline=P['ink'])
        line(d,[(56,shoulder_top+5),(65,shoulder_top+13),(67,84)],'shade')
        rect(d,(l+7,73,l+17,81),'shade')
        line(d,(l+8,74,l+15,74),'light')
        rivet(d,l+15,76)
        return im
    pts=[(l,84),(l,shoulder_top+13),(l+5,shoulder_top+5),
         (42,shoulder_top),(58,shoulder_top),(r-5,shoulder_top+5),
         (r,shoulder_top+13),(r,84)]
    if kind=='small':
        pts=[(l,84),(l,68),(l+6,58),(40,53),(60,53),(r-6,58),(r,68),(r,84)]
    d.polygon(pts,fill=P['orange'],outline=P['ink'])
    # Fill through bottom: the crop cuts cloth, rather than a hem line.
    line(d,(l+1,84,r-1,84),'orange')
    line(d,[(l+2,83),(l+2,shoulder_top+13),(l+7,shoulder_top+6),(40,shoulder_top+2)],'light',2)
    d.polygon([(r-7,shoulder_top+7),(r-1,shoulder_top+14),(r-1,84),
               (r-9,84),(r-10,shoulder_top+13)],fill=P['shade'])
    # Collar folded over the neck, stitch seams and jacket zipper.
    d.polygon([(39,shoulder_top+1),(46,shoulder_top+5),(49,shoulder_top+4),
               (45,shoulder_top+11)],fill=P['shade'],outline=P['ink'])
    d.polygon([(61,shoulder_top+1),(54,shoulder_top+5),(51,shoulder_top+4),
               (55,shoulder_top+11)],fill=P['light'],outline=P['ink'])
    line(d,(50,shoulder_top+7,50,84),'shade')
    for a,b in ((22,27),(72,77)):
        rect(d,(a-2,65,b+2,75),'dark')
        rect(d,(a,64,b,75),'mid')
        line(d,(a+1,65,b,65),'metal')
        for y in (68,71,74): line(d,(a+1,y,b,y),'steel')
    # Paint last, so hands touch its edge but never obscure live-text pixels.
    rect(d,(28,61,71,80),'ink',False)
    d.rectangle((28,61,71,80),outline=P['metal'])
    return im


def portrait(v,side=False):
    body=shoulders(v,side)
    h=head(v,side)
    body.alpha_composite(h)
    return body,h


def label(d,pos,text):
    # Pillow's built-in bitmap font: preview labels only, never portrait pixels.
    d.fontmode='1'
    d.text(pos,text,fill=P['metal'])


def previews(fronts,sides):
    PREVIEW.mkdir(exist_ok=True)
    rows=(len(fronts)+3)//4
    for name,ims in (('all-front-4x.png',fronts),('all-side-4x.png',sides)):
        board=Image.new('RGB',(4*108,rows*100),P['wall'])
        d=ImageDraw.Draw(board)
        for v,im in enumerate(ims):
            x,y=(v%4)*108+4,(v//4)*100
            label(d,(x+3,y+2),f'{v:02d}')
            board.paste(im,(x,y+15),im)
        board.resize((board.width*4,board.height*4),NN).save(PREVIEW/name)
    board=Image.new('RGB',(4*208,rows*100),P['wall'])
    d=ImageDraw.Draw(board)
    for v,(a,b) in enumerate(zip(fronts,sides)):
        x,y=(v%4)*208+4,(v//4)*100
        label(d,(x+3,y+2),f'{v:02d}   FRONT / LEFT')
        board.paste(a,(x,y+15),a); board.paste(b,(x+100,y+15),b)
    board.resize((board.width*3,board.height*3),NN).save(PREVIEW/'pairs-3x.png')
    # Scales are exact, not a scaled composite: 32*6 beside 100*2.
    board=Image.new('RGB',(4*416,rows*216),P['wall'])
    d=ImageDraw.Draw(board)
    for v,im in enumerate(fronts):
        x,y=(v%4)*416,(v//4)*216
        label(d,(x+12,y+7),f'{v:02d}  YARD x6 / MUG x2')
        sprite=Image.open(ROOT.parent/'robots'/f'robot-{v}.png').crop((0,0,32,32)).convert('RGBA')
        sprite=sprite.resize((192,192),NN)
        mug=im.resize((200,170),NN)
        board.paste(sprite,(x+8,y+24),sprite)
        board.paste(mug,(x+208,y+46),mug)
    board.save(PREVIEW/'match-6x.png')


def generate():
    fronts,sides=[],[]
    for v in range(N_TYPES):
        a,_=portrait(v); b,_=portrait(v,True)
        a.save(ROOT/f'mug-{v}.png'); b.save(ROOT/f'mug-{v}-side.png')
        fronts.append(a); sides.append(b)
    previews(fronts,sides)
    colors=set()
    for im in fronts+sides:
        colors.update(opaque_colors(im))
    data={'size':list(SIZE),'placard':list(PLACARD),
          'variants':[{'front':f'mug-{v}.png','side':f'mug-{v}-side.png',
                       'type':'; '.join(TYPES[v][1:4]),'eye':P[TYPES[v][4]]} for v in range(N_TYPES)],
          'palette':sorted(colors),'added_metal_midtones':ADDED_METAL}
    (ROOT/'mugshots.json').write_text(json.dumps(data,indent=2)+'\n')


def check():
    out=[]
    colors=set(); fronts=[]
    for v in range(N_TYPES):
        for side in (False,True):
            name=f'mug-{v}'+('-side' if side else '')+'.png'
            im=Image.open(ROOT/name)
            assert im.size==SIZE and im.mode=='RGBA',name
            alpha=sorted(set(im.getchannel('A').getdata()))
            assert alpha==[0,255],(name,alpha)
            colors.update('#%02x%02x%02x'%p[:3] for p in im.getdata() if p[3])
            edge=sum(im.getpixel((x,0))[3]>0 for x in range(100))
            edge+=sum(im.getpixel((x,y))[3]>0 for x in (0,99) for y in range(85))
            assert edge==0,(name,'frame edge')
            bottom={x for x in range(100) if im.getpixel((x,84))[3]}
            body=shoulders(v,side)
            assert bottom and all(im.getpixel((x,84))==body.getpixel((x,84)) for x in bottom)
            allowed={(*rgb(c),255) for c in ('ink','orange','shade','light')}
            assert all(im.getpixel((x,84)) in allowed for x in bottom)
            h=head(v,side)
            assert not h.crop((0,84,100,85)).getbbox()
            placard='none (profile)'
            if not side:
                bad=[]
                for y in range(61,81):
                    for x in range(28,72):
                        expected=(*rgb('metal' if x in (28,71) or y in (61,80) else 'ink'),255)
                        if im.getpixel((x,y))!=expected: bad.append((x,y))
                assert not bad,(name,'placard',bad)
                placard='880/880 exact'
                hb=h.crop((0,0,100,50)).getbbox()
                centre=(hb[0]+hb[2]-1)/2
                assert abs(centre-50)<=1,(name,hb,centre)
                assert 36<=hb[2]-hb[0]<=44
                # The saved portrait must contain the actual isolated head pixels.
                assert all(im.getpixel((x,y))==h.getpixel((x,y))
                           for y in range(50) for x in range(100) if h.getpixel((x,y))[3])
                fronts.append(im.copy())
                center_note=f'; head bbox above y50={hb}, centre={centre:g}'
            else:
                center_note='; profile intentionally projects left'
            out.append(f'{name}: 100x85 RGBA; alpha={alpha}; placard={placard}; '
                       f'top/left/right clear; bottom only uniform x={min(bottom)}..{max(bottom)}'
                       +center_note+' PASS')
    data=json.loads((ROOT/'mugshots.json').read_text())
    assert data['size']==list(SIZE) and data['placard']==list(PLACARD)
    assert len(data['variants'])==N_TYPES
    for v,variant in enumerate(data['variants']):
        assert variant['type']=='; '.join(TYPES[v][1:4]) and variant['eye']==P[TYPES[v][4]]
        for side,key in ((False,'front'),(True,'side')):
            im=Image.open(ROOT/variant[key])
            assert (*rgb(TYPES[v][4]),255) in set(im.getdata())
            assert (*rgb('paper'),255) in set(im.getdata())
            # Core pixels inside the face, adjacent to their actual eye colour.
            core=sum(im.getpixel((x,y))==(*rgb('paper'),255)
                     and any(im.getpixel((x+dx,y+dy))==(*rgb(TYPES[v][4]),255)
                             for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)))
                     for y in range(19,46) for x in range(27,74))
            assert core>0,(v,key,'no lighter eye core')
    out.append(f'Metadata: {N_TYPES} imported yard types, actual eye colours and emitter/core pixels in all {2*N_TYPES} portraits PASS')
    differences=[]
    for a,b in combinations(range(N_TYPES),2):
        n=sum(pa!=pb for pa,pb in zip(fronts[a].getdata(),fronts[b].getdata()))
        assert n>0
        differences.append((n,a,b))
    n,a,b=min(differences)
    out.append(f'Front uniqueness: all {len(differences)} pairs differ; minimum {n} differing RGBA pixels, types {a} vs {b} PASS')
    assert colors==set(data['palette'])
    outside=colors-{'#'+s for s in yard.SPEC_PALETTE}
    assert outside==set(ADDED_METAL) and len(colors)<=40
    # Include preview colours and existing yard/scene rasters in overall scope.
    overall=set(colors)
    for folder in (ROOT/'preview',ROOT.parent/'robots',ROOT.parent/'scene'):
        for p in sorted(folder.rglob('*.png')):
            im=Image.open(p).convert('RGBA')
            overall.update(opaque_colors(im))
    assert len(overall)<=40,(len(overall),sorted(overall))
    # The scene declares one relative of its own (scene/make_scene.py: 'yellow').
    alloutside=overall-{'#'+s for s in yard.SPEC_PALETTE}-{'#c7ad60'}
    assert alloutside==set(ADDED_METAL),alloutside
    out.append(f'Portrait opaque RGB colours: {len(colors)}; palette=' + ', '.join(sorted(colors)))
    out.append(f'Added metal mid-tones: {ADDED_METAL}; colours outside declared palette: {sorted(outside)} PASS')
    out.append(f'Overall opaque RGB colours, portraits/previews + existing robots/scene PNGs: {len(overall)}/40; outside SPEC: {sorted(alloutside)} PASS')
    rows=(N_TYPES+3)//4
    expected={'all-front-4x.png':(1728,rows*400),'all-side-4x.png':(1728,rows*400),
              'pairs-3x.png':(2496,rows*300),'match-6x.png':(1664,rows*216)}
    for name,size in expected.items():
        assert Image.open(PREVIEW/name).size==size
    out.append(f'Previews: 4x{rows} fronts/sides at exact 4x; 4x{rows} pairs at 3x; {N_TYPES} yard crops at 6x beside fronts at 2x PASS')
    out.append('SELF-CHECK PASS')
    return '\n'.join(out)


def hashes():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ROOT.rglob('*')) if p.suffix in ('.png','.json')}


def delivered_hashes():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ROOT.rglob('*')) if p.is_file()}


def source_hashes():
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT.parent/'robots').rglob('*')) if p.is_file()}


def report(output):
    notes=[
        '# Robot booking portraits', '',
        f'**Measured:** {2*N_TYPES} transparent 100 × 85 RGBA portraits, metadata and four labelled previews were generated by `make_mugshots.py`, using Pillow and the Python standard library. Only `mugshots/` is written. `robots/make_robots.py` is imported with bytecode writes disabled; its inmate descriptors, eye palette and `build()` dimensions drive rendering. Unknown head/antenna descriptors fail explicitly. The existing robot files are hashed before and after the build.', '',
        '**Measured:** The full 44 × 20 placard, including all 124 border pixels and 756 interior pixels, is checked in every saved front PNG. Fingers abut x27/x72 and the placard owns x28..71, so nothing overlaps its live-text area. No bars, wall, tally marks, number or portrait text is baked in.', '',
        '**Measured:** Head centring uses the isolated head layer, including antennas and ear bolts, cropped to y0..49; bounding boxes are reported below. Side profiles deliberately project left and are excluded from frontal symmetry. The neck and uniform layers are excluded from head bounds. Every bottom-edge pixel must equal the isolated uniform layer and be an orange or outline colour; top, left and right must be empty.', '',
        '**Measured:** No added metal mid-tones (0 of 6 allowed). Eye cores use existing #f3f1e7. `palette` lists actual opaque portrait colours; transparent pixels are excluded from colour counts. The broader overall count also scans all existing robots/scene PNGs and these previews. No antialiasing, filtering or partial-alpha rendering is used; nearest-neighbour alone scales previews.', '',
        '**Measured:** Standard / stocky / slim front uniform widths are 67 / 81 / 53 px; they derive from the yard body widths 11 / 13 / 9. Profile uniform widths are 55 / 69 / 47 px. Frontal head bounds are all within 36–44 px wide and within 1 px of x50, including ear bolts and antennas.', '',
    ]
    notes += ['**Viewed:** '+note+'\n' for note in VIEWED_NOTES]
    if not VIEWED_NOTES:
        notes += ['**Not checked:** Visual preview review pending.','']
    notes += [
        '**Not checked:** Integration behind the live page bars, the live booking text overlay, recognition by other viewers, and browser rendering. No page code is available in this task. Profiles reinterpret depth that the tiny yard sprites cannot resolve; they are left-facing drawings, not mirrored front views.', '',
        '**Measured — self-check output (every line in this block is measured):**', '',
        '```text',output,'```','',
    ]
    (ROOT/'REPORT.md').write_text('\n'.join(notes))


if __name__=='__main__':
    before=source_hashes()
    n_expected=2*N_TYPES+8
    def full_build():
        generate()
        result=check()
        assert before==source_hashes(),'Read-only yard files changed'
        result+=f'\nDeterminism: two complete builds byte-identical (SHA-256), all {n_expected} delivered files including script/report/check transcript PASS'
        result+='\nRead-only robots/: all source/asset hashes unchanged PASS'
        (ROOT/'self-check.txt').write_text(result+'\n')
        report(result)
        return result
    output=full_build()
    first=delivered_hashes()
    assert len(first)==n_expected,('Unexpected deliverables',len(first),list(first))
    output=full_build()
    second=delivered_hashes()
    if first!=second:
        output=output.replace(f'all {n_expected} delivered files including script/report/check transcript PASS',
                              f'all {n_expected} delivered files including script/report/check transcript FAIL')
        (ROOT/'self-check.txt').write_text(output+'\n')
        report(output)
        raise AssertionError('Non-deterministic full build')
    print(output)

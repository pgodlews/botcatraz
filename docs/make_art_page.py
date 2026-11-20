#!/usr/bin/env python3
"""Write the pictures for docs/ART.md from the committed art in yard/art.

    python3 docs/make_art_page.py

Writes docs/art/*.png and *.gif, and the table of robot types between the
<!-- types --> markers in docs/ART.md. Run it after the art generators.
Needs Pillow. The output is deterministic, like the art itself.
"""
import json
import pathlib
import re

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
ART = ROOT / "yard" / "art"
OUT = ROOT / "docs" / "art"
PAGE = ROOT / "docs" / "ART.md"
NEAREST = Image.Resampling.NEAREST
GROUND = (0xB9, 0xBE, 0xB4, 255)      # concrete, from the palette
WALL = (0x58, 0x61, 0x5C, 255)        # building wall, from the palette
TICK_MS = 50                          # animation time step
LOOP_TICKS = 80                       # 4 s: a whole number of cycles for every row

robots = json.loads((ART / "robots" / "robots.json").read_text())
mugs = json.loads((ART / "mugshots" / "mugshots.json").read_text())
FW, FH = robots["frame"]
ROWS = robots["rows"]
SHEETS = [Image.open(ART / "robots" / v["file"]).convert("RGBA") for v in robots["variants"]]
GUARD_ROWS = set(robots["guard_rows"])


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), NEAREST)


def frame(sheet, row, f):
    return sheet.crop((f * FW, row * FH, (f + 1) * FW, (row + 1) * FH))


def grid(cells, cols, cell_size, gap, background):
    rows = (len(cells) + cols - 1) // cols
    w, h = cell_size
    im = Image.new("RGBA", (cols * w + (cols + 1) * gap, rows * h + (rows + 1) * gap), background)
    for i, cell in enumerate(cells):
        if cell is not None:
            x, y = gap + (i % cols) * (w + gap), gap + (i // cols) * (h + gap)
            im.alpha_composite(cell, (x + (w - cell.width) // 2, y + (h - cell.height) // 2))
    return im


def save_png(im, name):
    im.convert("RGB").save(OUT / name)


def save_gif(frames, name):
    """Exact colours: the art has far fewer than 256, so no quantising is needed."""
    colours = sorted({c for f in frames for c in f.convert("RGB").getdata()})
    assert len(colours) <= 256, name
    index = {c: i for i, c in enumerate(colours)}
    palette = [v for c in colours for v in c]
    out = []
    for f in frames:
        p = Image.new("P", f.size)
        p.putpalette(palette)
        p.putdata([index[c] for c in f.convert("RGB").getdata()])
        out.append(p)
    out[0].save(OUT / name, save_all=True, append_images=out[1:], duration=TICK_MS, loop=0,
                optimize=False, disposal=1)


def row_named(name):
    return next(r for r in ROWS if r["name"] == name)


def lineup_gif():
    """Every type and the guard walking towards the viewer, 3x."""
    walk = row_named("walk_down")
    ticks = int(walk["frames"] / walk["fps"] * 1000 / TICK_MS)
    frames = []
    for t in range(ticks):
        f = int(t * TICK_MS / 1000 * walk["fps"]) % walk["frames"]
        cells = [scaled(frame(s, walk["row"], f), 3) for s in SHEETS]
        frames.append(grid(cells, 8, (FW * 3, FH * 3), 12, GROUND))
    save_gif(frames, "robots.gif")


def animations_gif(v, name):
    """Every animation row of one sheet, each at its own speed, 3x."""
    rows = [r for r in ROWS if v != len(SHEETS) - 1 or r["row"] in GUARD_ROWS]
    frames = []
    for t in range(LOOP_TICKS):
        cells = [scaled(frame(SHEETS[v], r["row"], int(t * TICK_MS / 1000 * r["fps"]) % r["frames"]), 3)
                 for r in rows]
        frames.append(grid(cells, 6, (FW * 3, FH * 3), 12, GROUND))
    save_gif(frames, name)
    return [r["name"] for r in rows]


def sheets_png():
    cells = [scaled(s, 2) for s in SHEETS]
    save_png(grid(cells, 6, cells[0].size, 16, GROUND), "sheets.png")


def mugshots_png():
    pairs = []
    for v in mugs["variants"]:
        front = Image.open(ART / "mugshots" / v["front"]).convert("RGBA")
        side = Image.open(ART / "mugshots" / v["side"]).convert("RGBA")
        pair = Image.new("RGBA", (front.width + side.width + 4, front.height))
        pair.alpha_composite(front, (0, 0))
        pair.alpha_composite(side, (front.width + 4, 0))
        pairs.append(scaled(pair, 2))
    save_png(grid(pairs, 4, pairs[0].size, 16, WALL), "mugshots.png")


def scene_png():
    """The background with every fixed prop in place, doors closed, as the engine draws them."""
    scene = Image.open(ART / "scene" / "yard_bg.png").convert("RGBA")
    atlas = Image.open(ART / "scene" / "props.png").convert("RGBA")
    props = json.loads((ART / "scene" / "props.json").read_text())
    for p in sorted(props, key=lambda p: p["baseline"]):
        if p.get("dynamic"):
            continue
        x, y, w, h = p["rect"]
        scene.alpha_composite(atlas.crop((x, y, x + w, y + h)), tuple(p["at"]))
    save_png(scaled(scene, 2), "scene.png")
    checker = Image.new("RGBA", atlas.size)
    for y in range(0, atlas.height, 4):
        for x in range(0, atlas.width, 4):
            shade = (0x9A, 0xA3, 0xA0, 255) if (x // 4 + y // 4) % 2 else (0xC3, 0xCA, 0xC6, 255)
            checker.paste(shade, (x, y, x + 4, y + 4))
    checker.alpha_composite(atlas)
    save_png(scaled(checker, 4), "props.png")


def types_table():
    lines = ["| # | Head | Antenna | Eyes | Booking photos |", "|---|---|---|---|---|"]
    for i, (v, m) in enumerate(zip(robots["variants"], mugs["variants"])):
        photos = (f'<img src="../yard/art/mugshots/{m["front"]}" width="100" alt="type {i}, front"> '
                  f'<img src="../yard/art/mugshots/{m["side"]}" width="100" alt="type {i}, profile">')
        lines.append(f'| {i} | {v["head"]} | {v["antenna"]} | {v["eyes"]} | {photos} |')
    guard = robots["variants"][-1]
    lines.append(f'| guard | {guard["head"]} | {guard["antenna"]} | {guard["eyes"]} | none |')
    text = PAGE.read_text()
    marked = re.compile(r"(<!-- types -->\n).*?(<!-- /types -->)", re.S)
    assert marked.search(text), "docs/ART.md has no <!-- types --> ... <!-- /types --> markers"
    PAGE.write_text(marked.sub(lambda m: m.group(1) + "\n".join(lines) + "\n" + m.group(2), text, count=1))


def main():
    OUT.mkdir(exist_ok=True)
    assert len(mugs["variants"]) == len(SHEETS) - 1
    lineup_gif()
    rows = animations_gif(0, "animations.gif")
    guard_rows = animations_gif(len(SHEETS) - 1, "guard.gif")
    sheets_png()
    mugshots_png()
    scene_png()
    types_table()
    print("animations.gif rows:", ", ".join(rows))
    print("guard.gif rows:", ", ".join(guard_rows))
    for path in sorted(OUT.iterdir()):
        print(path.name, Image.open(path).size, path.stat().st_size)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the jail pages from the records each server keeps.

    ./build.py              every server in servers.json: fetch a fresh export, build its pages
    ./build.py --www DIR    also lay out a website in DIR:
                              DIR/index.html           all jails
                              DIR/<id>/index.html      the cells of one server
                              DIR/<id>/yard.html       its exercise yard
                              DIR/<id>/yard.json       what the yard re-reads every 5 minutes
    ./build.py --no-export  rebuild from the last exports (after editing a template)
    ./build.py --only ID    one server only
    ./build.py --sample     no servers needed: build a website in www/ (or --www DIR) from
                            invented records (sample/make_sample.py), then look at it with
                            python3 -m http.server --directory www

    --servers FILE   the list of servers (default: servers.json next to this file; see
                     servers.example.json):
                     [{"id": "server1", "ssh": "user@host", "key": "~/.ssh/key"}, ...]
                     "key" is optional. The command is fixed: jail-records export, which
                     prints the snapshot the server's timer writes every 5 minutes. Log in
                     as the server's jail-export account, whose key may run nothing else.

out/<id>/jail.html and out/<id>/yard.html are page bodies with no document around
them, for embedding in another page; the website copies are the same bodies inside
a complete HTML document.

Nothing here looks anything up: countries and networks come out of the records,
which each server fills from its own local DB-IP Lite databases. The name shown
for a server is the one in its own /etc/jail-records.json.
"""
import argparse
import base64
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "out"
DOCUMENT = ('<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="color-scheme" content="light dark">\n<meta name="robots" content="noindex">\n')


def write(path, text):
    """Replace the file in one step, so a reader never sees half a page."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def dumps(value):
    return json.dumps(value, separators=(",", ":")).replace("</", "<\\/")


def fetch(server):
    """The latest snapshot from one server. A broken one must not replace the last good one."""
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20"]
    if server.get("key"):
        ssh += ["-i", os.path.expanduser(server["key"]), "-o", "IdentitiesOnly=yes"]
    res = subprocess.run(ssh + [server["ssh"], "jail-records export"], capture_output=True, check=True, timeout=60)
    json.loads(res.stdout)
    write(OUT / server["id"] / "jail.json", res.stdout.decode())


def sample(server):
    """Invented records for one of the sample servers, written where an export would be."""
    spec = importlib.util.spec_from_file_location("make_sample", HERE / "sample" / "make_sample.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    write(OUT / server["id"] / "jail.json", dumps(module.export(server["id"])))


def yard_data(data):
    """What the yard needs: who is inside now, and who walked out in the last day."""
    geo, now = data["geo"], data["generated"]

    def row(r):
        g = geo.get(r["ip"], {})
        jail = data["jails"].get(r["jail"], {})
        if jail.get("door") == "ssh":
            users = data["ssh"].get(r["ip"], {}).get("users") or []
            tried = "tried to log in as " + ", ".join(u[0] for u in users[:3]) if users else ""
        else:
            paths = data["web"].get(r["ip"], {}).get("paths") or []
            tried = "sent " + ", ".join(p[0] for p in paths[:2]) if paths else ""
        return {"ip": r["ip"], "jail": r["jail"], "wing": jail.get("wing") or r["jail"][:1].upper(),
                "banned_at": r["banned_at"], "release": r["release"], "sentence": r["sentence"],
                "bancount": r["bancount"], "cc": g.get("cc"), "country": g.get("country"),
                "city": g.get("city"), "org": g.get("org"), "tried": tried[:90]}

    released = []
    for r in data["records"]:
        when = r.get("released_early") or r["release"]
        if not r["inside"] and now - 86400 <= when <= now:
            released.append({**row(r), "released_at": when})
    return {"generated": now, "host": data["host"], "released": released,
            "prisoners": [row(r) for r in data["records"] if r["inside"]]}


def yard_art():
    """The pixel art (yard/art, drawn from yard/SPEC.md), inlined as data URIs."""
    art = HERE / "yard" / "art"

    def uri(path):
        return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode() if path.exists() else None

    def js(path):
        return json.loads(path.read_text()) if path.exists() else None

    robots, scene = art / "robots", art / "scene"
    if not (robots / "robot-0.png").exists() and not (scene / "yard_bg.png").exists():
        return None
    sheets = sorted(robots.glob("robot-*.png"), key=lambda p: int(p.stem.split("-")[1]))
    return {"robots": {"meta": js(robots / "robots.json"), "guard": uri(robots / "guard.png"),
                       "sheets": [uri(p) for p in sheets]},
            "scene": {"bg": uri(scene / "yard_bg.png"), "props": uri(scene / "props.png"),
                      "propsMeta": js(scene / "props.json"), "zones": js(scene / "zones.json")}}


def mug_shots():
    """Booking photos of the robot types (yard/art/mugshots), for the cells page."""
    folder = HERE / "yard" / "art" / "mugshots"
    if not (folder / "mugshots.json").exists():
        return None
    meta = json.loads((folder / "mugshots.json").read_text())

    def uri(name):
        return "data:image/png;base64," + base64.b64encode((folder / name).read_bytes()).decode()

    return {"size": meta["size"], "placard": meta["placard"],
            "front": [uri(v["front"]) for v in meta["variants"]], "side": [uri(v["side"]) for v in meta["variants"]]}


def build(server, www, art, land, mugs):
    """The cells page and the yard of one server. Returns its line for the front page."""
    sid = server["id"]
    data = json.loads((OUT / sid / "jail.json").read_text())
    name = data["host"]
    cells = (HERE / "template.html").read_text().replace("{{NAME}}", name)
    cells = cells.replace("/*__DATA__*/null", dumps(data)).replace("/*__LAND__*/null", land)
    cells = cells.replace("/*__MUGS__*/null", dumps(mugs))
    feed = yard_data(data)
    yard = (HERE / "yard" / "yard.html").read_text().replace("{{NAME}}", name)
    yard = yard.replace("/*__YARD__*/null", dumps(feed)).replace("/*__ART__*/null", dumps(art))
    write(OUT / sid / "jail.html", cells)
    write(OUT / sid / "yard.html", yard)
    if www:
        nav = '<p class="lede"><a href="yard.html">Visit the yard →</a> · <a href="../">All jails</a></p>'
        write(www / sid / "index.html", DOCUMENT + cells.replace("<!--NAV-->", nav))
        write(www / sid / "yard.html", DOCUMENT + yard.replace("/*__LIVE__*/false", "true"))
        write(www / sid / "yard.json", dumps(feed))
    inside = [r for r in data["records"] if r["inside"]]
    return {"id": sid, "name": name, "generated": data["generated"], "inside": len(inside),
            "repeat": sum(1 for r in inside if r["bancount"] > 1), "on_record": len(data["records"]),
            "worst": max((r["bancount"] for r in inside), default=0),
            "knocks": data["totals"]["ssh_attempts"] + data["totals"]["web_requests"],
            "window_days": data["window_days"], "place": (data.get("home") or {}).get("country"),
            "cc": (data.get("home") or {}).get("cc"),
            "wings": [{"wing": j.get("wing"), "label": j.get("label"),
                       "inside": sum(1 for r in inside if r["jail"] == key)} for key, j in data["jails"].items()]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-export", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--www")
    ap.add_argument("--servers")
    ap.add_argument("--sample", action="store_true")
    args = ap.parse_args()

    if args.sample:
        servers = [{"id": "sample1"}, {"id": "sample2"}]
        args.www = args.www or str(HERE / "www")
    else:
        listing = pathlib.Path(args.servers) if args.servers else HERE / "servers.json"
        if not listing.exists():
            sys.exit(f"build.py: no {listing} (copy servers.example.json, or try --sample)")
        servers = json.loads(listing.read_text())
    servers = [s for s in servers if not args.only or s["id"] == args.only]
    www = pathlib.Path(args.www) if args.www else None
    art, land, mugs = yard_art(), (HERE / "land-110m.json").read_text().strip(), mug_shots()

    failed, sites = [], []
    for server in servers:
        if args.sample:
            sample(server)
        elif not args.no_export:
            try:
                fetch(server)
            except (subprocess.SubprocessError, OSError, ValueError) as exc:
                failed.append(server["id"])
                print(f"{server['id']}: export failed, keeping the last one ({exc})", file=sys.stderr)
        if not (OUT / server["id"] / "jail.json").exists():
            continue
        site = build(server, www, art, land, mugs)
        sites.append(site)
        print(f"{site['id']} ({site['name']}): {site['inside']} inside, {site['on_record']} on record")
    if www and sites and not args.only:
        front = (HERE / "landing.html").read_text().replace("/*__SITES__*/null", dumps(sites))
        write(www / "index.html", DOCUMENT + front)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

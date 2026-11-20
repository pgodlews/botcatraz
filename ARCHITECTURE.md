# Architecture

Botcatraz has three parts that never share a process:

1. **`server/jail-records`**, a single Python file on each server. It keeps a
   record of fail2ban's bans and of the knocks that led to them.
2. **`build.py`**, on a web host. It fetches each server's records over SSH and
   writes static pages.
3. **The pages**: the cells page (`template.html`), the yard (`yard/yard.html`)
   and the front page (`landing.html`). They run in the browser with everything
   inlined.

The pixel art in `yard/art/` is written by three generator scripts. It is
committed, and `build.py` inlines it into the pages.

## The whole system

```mermaid
flowchart LR
    subgraph server["Each server"]
        f2b["fail2ban"]
        sshlog["SSH journal<br/>(systemd unit ssh)"]
        weblog["nginx access log<br/>(optional)"]
        jr["jail-records<br/>/usr/local/sbin"]
        db[("records.sqlite3<br/>/var/lib/jail-records")]
        geo[("DB-IP Lite<br/>city.mmdb, asn.mmdb")]
        timer1["jail-records.timer<br/>sync every 5 minutes,<br/>sandboxed, offline"]
        timer3["jail-records-geo.timer<br/>daily, downloads monthly"]
        snap[("export/jail.json<br/>root + jail-export group")]
        timer1 --> jr
        timer3 --> geo
        jr --> snap
        f2b -- "fail2ban-client get" --> jr
        sshlog -- journalctl --> jr
        weblog -- glob --> jr
        geo -- offline lookups --> jr
        jr <--> db
        f2b -. "ignorecommand:<br/>jail-records is-trusted" .-> jr
    end

    subgraph host["Web host"]
        timer2["NAME-build.timer<br/>every 5 minutes"]
        build["build.py"]
        out[("out/&lt;id&gt;/<br/>jail.json, jail.html, yard.html")]
        www[("www/<br/>index.html, &lt;id&gt;/...")]
        serve["NAME.service<br/>python3 -m http.server"]
        timer2 --> build
        build --> out --> build
        build --> www --> serve
    end

    browser["Browser:<br/>front page, cells, yard"]

    build == "connects over SSH every 5 minutes (polling)<br/>as jail-export: jail-records export" ==> snap
    snap -. "the snapshot on stdout,<br/>same connection" .-> build
    browser == "requests pages; an open yard<br/>polls yard.json every 5 minutes" ==> serve
    serve -. "static files" .-> browser
```

Between the three places, a thick arrow points from the side that opens the
connection, and a dotted arrow shows what comes back over it. The web host
polls the servers and the browser polls the web host. A server never connects
to the web host and holds no key for it. Inside a box, arrows show which
way data moves.

Nothing calls out to the internet at run time, apart from two things: a server
downloads the DB-IP Lite databases once a month, and a browser loads the fonts
from Google Fonts.

## On each server: `jail-records`

| Command | What it does | Who runs it |
|---|---|---|
| `sync` | Reads fail2ban's live bans and settings, the SSH journal and the web logs for the last 7 whole days, and writes them into SQLite. Looks up new addresses in DB-IP. Then writes the export snapshot, one JSON document with everything the pages need. | `jail-records.timer`, every 5 minutes, as root in a sandbox |
| `export` | Prints the snapshot. Needs no root: the `jail-export` group may read it. | `build.py`, over SSH as `jail-export`, whose key can run nothing else |
| `is-trusted ADDR` | Exits 0 if the address is ours (own, already trusted, or logged in over SSH in the last day). Reads only; any error means "not trusted". | fail2ban, as its `ignorecommand` |
| `geo-update [--force]` | Downloads DB-IP Lite when the copy is older than 35 days, or always with `--force`. | `jail-records-geo.timer`, daily; `install.sh` |
| `stats` | Prints counts and the last sync time. | You |

`server/install.sh` installs the tool, `/etc/jail-records.json` (from
`site.json`), the two timers, and `python3-maxminddb`. With `export-key.pub`
next to it, it creates the `jail-export` account and locks that key to
`jail-records export` in `authorized_keys`
(`command="/usr/local/sbin/jail-records export",restrict`). It runs a first
`geo-update` and `sync`.

### Who may do what

| Part | Runs as | Can |
|---|---|---|
| `jail-records.service` (sync) | root, sandboxed | Read fail2ban, the journal and logs; write only `/var/lib/jail-records`. No IP network, no new privileges; of root's capabilities only `CAP_DAC_READ_SEARCH` |
| `jail-records-geo.service` | root, sandboxed | Reach the internet; write only `/var/lib/jail-records`; no capabilities at all |
| `jail-records export` | `jail-export` | Read the snapshot. Its SSH key runs only this command: no shell, terminal, forwarding or sftp |
| `jail-records is-trusted` | root, from fail2ban | Read only; any error means "not trusted" |

### What it keeps

```mermaid
erDiagram
    offenders ||--o{ bookings : "is booked"
    offenders ||--o{ sightings : "is seen"
    offenders {
        text ip PK
        int first_seen
        int last_seen
        text cc
        text country
        text city
        real lat
        real lon
        text asn
        text org
    }
    bookings {
        text jail PK
        text ip PK
        int booked_at PK
        int sentence
        int release_at
        int ban_no
        int failures
        text evidence
        int released_early
    }
    sightings {
        text day PK
        text door PK
        text ip PK
        int hits
        text detail
    }
    hourly {
        text door PK
        int hour PK
        int hits
    }
    trusted {
        text ip PK
        text why
        int since
    }
    meta {
        text key PK
        text value
    }
```

A "door" is `ssh` or `web`. Each jail in the settings names its door, the letter
of its wing (used in booking numbers such as `S-4589`) and a label.

### What never leaves the server

```mermaid
flowchart TD
    seen["An address appears in a log or a ban"] --> own{"One of the machine's own<br/>addresses, or under own?"}
    own -- yes --> drop["Not recorded"]
    own -- no --> trusted{"Logged in over SSH, or<br/>showed a valid web token?"}
    trusted -- yes --> forget["Added to trusted;<br/>everything held about it is deleted"]
    trusted -- no --> keep["Recorded"]
    keep --> scrub["On export, evidence lines have the<br/>host name and own addresses<br/>replaced by the configured name"]
```

## On the web host: `build.py`

```mermaid
sequenceDiagram
    participant T as build timer
    participant B as build.py
    participant S as server (jail-records)
    participant O as out/<id>/
    participant W as www/

    T->>B: start (every 5 minutes)
    loop each server in servers.json
        B->>S: ssh -o BatchMode=yes … jail-export@server jail-records export
        alt export works
            S-->>B: JSON
            B->>O: jail.json (replaced in one step)
        else unreachable or bad JSON
            B-->>B: keep the last jail.json, mark failed
        end
        B->>B: fill template.html and yard/yard.html
        B->>O: jail.html, yard.html (bodies only)
        B->>W: <id>/index.html, <id>/yard.html, <id>/yard.json
    end
    B->>W: index.html from landing.html (one card per server)
    B-->>T: exit 1 if any export failed
```

Every file is written to a `.tmp` name and renamed, so the web server never
serves half a page. One server failing leaves its last good pages up.

### How a page is filled

The templates hold placeholders that `build.py` replaces with JSON.
`dumps()` escapes `</` so the data cannot close the `<script>` it sits in.

| Placeholder | In | Replaced with |
|---|---|---|
| `{{NAME}}` | `template.html`, `yard/yard.html` | The server's name from its own settings |
| `/*__DATA__*/null` | `template.html` | The whole export |
| `/*__LAND__*/null` | `template.html` | `land-110m.json`, the world outline |
| `/*__MUGS__*/null` | `template.html` | Booking photos as data URIs, from `yard/art/mugshots/` |
| `/*__YARD__*/null` | `yard/yard.html` | Who is inside, and who left in the last day (`yard_data()`) |
| `/*__ART__*/null` | `yard/yard.html` | Robot sheets, guard, background, props and zones, from `yard/art/` |
| `/*__LIVE__*/false` | `yard/yard.html` | `true` in the website copy, so it re-reads `yard.json` |
| `<!--NAV-->` | `template.html` | Links to the yard and the front page, in the website copy |
| `/*__SITES__*/null` | `landing.html` | One summary per server |

`--sample` skips SSH. It writes invented exports from `sample/make_sample.py`,
with addresses from the documentation ranges only.

`webhost/install.sh` turns the three `*.in` files into systemd units (a static
server, a build service and its timer) and remembers its options in
`install.conf`. `deploy-web.sh` copies the builder to a host and runs it there.

## In the browser

### The cells page

`template.html` draws everything from the inlined export: a cell per prisoner
with its booking photo, the rap sheet, a world map drawn from `land-110m.json`,
the busiest countries and networks, knocks per hour and recent releases. A link
ending in a booking number opens that cell.

### The yard

`yard/yard.html` is one canvas and no libraries. A robot's type is
`hash(ip) % types`, and the cells page picks the booking photo the same way, so
the two pages show the same robot.

```mermaid
stateDiagram-v2
    [*] --> Arriving: new booking
    Arriving --> Welcomed: repeat offender
    Welcomed --> Yard
    Arriving --> Yard
    Yard --> CellBlock: more than 30 outside
    CellBlock --> Yard: swap through the door
    Yard --> Leaving: sentence over or unbanned
    CellBlock --> Leaving: sentence over or unbanned
    Leaving --> [*]: out through the gate with a box

    state Yard {
        [*] --> Walking
        Walking --> Activity: pickTask()
        Activity --> Walking: done
        note right of Activity
            weights, basketball, benches,
            smoking, oil, chatting
        end note
    }
```

| Loop | Rate | Does |
|---|---|---|
| `tick()` | every animation frame | `update(dt)` moves robots along `findPath()` routes on a grid built from `zones.json`, then `draw()` |
| `everySecond()` | 1 s | Releases robots whose time is up, starts queued events, swaps robots with the cell block (`balance()`) |
| `sync()` | 5 min, live copy only | Fetches `yard.json`: a new booking is an arrival, a missing one a release |

`?fast=N` speeds time up.

All three pages have a Lights out / Day shift button. The choice is kept in
`localStorage` under `lights`, shared by every page of the site: a small script
at the top of each page applies it before anything is drawn, and a `storage`
event switches pages that are already open.

## The art

```mermaid
flowchart LR
    spec["yard/SPEC.md<br/>the brief"]
    robots["robots/make_robots.py"]
    scene["scene/make_scene.py"]
    mugs["mugshots/make_mugshots.py"]
    rpng[("robot-0..21.png, guard.png<br/>robots.json")]
    spng[("yard_bg.png, props.png<br/>props.json, zones.json")]
    mpng[("mug-N.png, mug-N-side.png<br/>mugshots.json")]
    build["build.py"]

    spec -.-> robots & scene & mugs
    robots --> rpng
    rpng -- "previews" --> scene
    rpng -- "imports descriptors" --> mugs
    scene --> spng
    mugs --> mpng
    rpng & spng & mpng --> build
```

The generators use Pillow and nothing else, and are deterministic. Each checks
its own output before it finishes: palette, anchors, frame counts, and for the
scene, the background's pixels against the accepted reference it embeds. The
number of robot types is set by the files: `build.py` globs `robot-*.png`, and
both pages take the count from the arrays they are given.

## Checks

```mermaid
flowchart LR
    push["push or pull request"] --> py & sh & f2b & art & pages
    py["Python 3.9 and 3.12:<br/>compile, unittest"]
    sh["shellcheck,<br/>unit rendering"]
    f2b["fail2ban 1.0.2:<br/>filters over tests/fail2ban/*.log"]
    art["Art: macOS byte for byte,<br/>Ubuntu by pixels"]
    pages["Sample build in<br/>headless Chromium"]
```

The commands are in the README's "Checks" section and in
`.github/workflows/ci.yml`.

## Files

| Path | Role |
|---|---|
| `server/jail-records` | The server tool |
| `server/install.sh`, `jail-records.service`, `.timer`, `jail-records-geo.*` | Install it on a server, with its sandboxed units |
| `deploy.sh` | Copy `server/` to a server and install it |
| `build.py` | Fetch exports and write the pages |
| `template.html`, `yard/yard.html`, `landing.html` | The three pages |
| `land-110m.json` | World outline for the map |
| `webhost/` | Units and installer for the web host |
| `deploy-web.sh` | Copy the builder to a web host and install it |
| `sample/make_sample.py` | Invented records for `--sample` |
| `yard/art/` | Generators and their committed output |
| `docs/ART.md`, `docs/make_art_page.py`, `docs/art/` | A page of all the art, the script that draws its pictures, and the guide to making art |
| `docs/take_screenshots.js` | Takes the README screenshots with dates and half of each address blanked |
| `fail2ban/` | Optional filters and jails |
| `tests/` | Unit tests and check scripts |

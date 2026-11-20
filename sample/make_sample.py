#!/usr/bin/env python3
"""Invented jail records, in the shape `jail-records export` prints.

    ./build.py --sample                 build the pages from these (the usual way in)
    python3 sample/make_sample.py ID    print one export as JSON (ID: sample1 or sample2)

Nothing here comes from a real server. Every address is from the ranges reserved
for documentation (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24, 2001:db8::/32),
the networks are made up and carry AS numbers reserved for documentation
(64496-64511, 65536-65551), and the cities are just large cities.

The history is replayed from a fixed date in ten-minute steps, and each step is
seeded by its own time. So two builds a few minutes apart tell the same story,
the later one a little further on: a yard left open in a browser sees the new
bans walk in and the finished sentences walk out.
"""
import calendar
import collections
import json
import random
import sys
import time

EPOCH = calendar.timegm((2026, 1, 1, 0, 0, 0))   # where the invented history starts
STEP = 600
DAY = 86400
WINDOW_DAYS = 7
KEEP_DAYS = 6         # a released address stays on record this long

SERVERS = {
    "sample1": {
        "home": {"cc": "DE", "country": "Germany", "city": "Frankfurt am Main", "lat": 50.11, "lon": 8.68,
                 "asn": "AS64496", "org": "Tin Can Hosting"},
        "jails": {"sshd": {"door": "ssh", "wing": "S", "label": "SSH"}},
        "arrivals": {"sshd": 0.075}, "knocks": 42, "crowd": 1150,
    },
    "sample2": {
        "home": {"cc": "SG", "country": "Singapore", "city": "Singapore", "lat": 1.29, "lon": 103.85,
                 "asn": "AS64497", "org": "Sprocket Cloud"},
        "jails": {"sshd": {"door": "ssh", "wing": "S", "label": "SSH"},
                  "web-auth": {"door": "web", "wing": "W", "label": "web endpoint"}},
        "arrivals": {"sshd": 0.02, "web-auth": 0.012}, "knocks": 30, "crowd": 820,
    },
}
RULES = {"ssh": {"maxretry": 3, "findtime": 3600, "bantime": DAY, "maxtime": 7 * DAY},
         "web": {"maxretry": 2, "findtime": 600, "bantime": DAY, "maxtime": 7 * DAY}}

# (country code, country, city, latitude, longitude, how busy)
CITIES = [
    ("CN", "China", "Beijing", 39.9, 116.4, 9), ("CN", "China", "Shanghai", 31.2, 121.5, 8),
    ("CN", "China", "Shenzhen", 22.5, 114.1, 7), ("CN", "China", "Chengdu", 30.7, 104.1, 4),
    ("US", "United States", "Ashburn", 39.0, -77.5, 8), ("US", "United States", "San Jose", 37.3, -121.9, 6),
    ("US", "United States", "Chicago", 41.9, -87.6, 4), ("US", "United States", "Dallas", 32.8, -96.8, 4),
    ("US", "United States", "Seattle", 47.6, -122.3, 3), ("NL", "The Netherlands", "Amsterdam", 52.4, 4.9, 7),
    ("DE", "Germany", "Frankfurt am Main", 50.1, 8.7, 6), ("DE", "Germany", "Berlin", 52.5, 13.4, 3),
    ("RU", "Russia", "Moscow", 55.8, 37.6, 6), ("RU", "Russia", "Saint Petersburg", 59.9, 30.3, 3),
    ("IN", "India", "Mumbai", 19.1, 72.9, 6), ("IN", "India", "Bengaluru", 13.0, 77.6, 4),
    ("IN", "India", "Delhi", 28.7, 77.1, 4), ("BR", "Brazil", "São Paulo", -23.5, -46.6, 6),
    ("BR", "Brazil", "Rio de Janeiro", -22.9, -43.2, 3), ("VN", "Vietnam", "Hanoi", 21.0, 105.8, 5),
    ("VN", "Vietnam", "Ho Chi Minh City", 10.8, 106.7, 5), ("ID", "Indonesia", "Jakarta", -6.2, 106.8, 5),
    ("KR", "South Korea", "Seoul", 37.6, 127.0, 5), ("SG", "Singapore", "Singapore", 1.3, 103.9, 5),
    ("HK", "Hong Kong", "Hong Kong", 22.3, 114.2, 5), ("JP", "Japan", "Tokyo", 35.7, 139.7, 4),
    ("GB", "United Kingdom", "London", 51.5, -0.1, 4), ("FR", "France", "Paris", 48.9, 2.4, 4),
    ("RO", "Romania", "Bucharest", 44.4, 26.1, 3), ("BG", "Bulgaria", "Sofia", 42.7, 23.3, 3),
    ("UA", "Ukraine", "Kyiv", 50.5, 30.5, 3), ("PL", "Poland", "Warsaw", 52.2, 21.0, 2),
    ("TR", "Türkiye", "Istanbul", 41.0, 29.0, 3), ("IR", "Iran", "Tehran", 35.7, 51.4, 3),
    ("TH", "Thailand", "Bangkok", 13.8, 100.5, 3), ("PK", "Pakistan", "Karachi", 24.9, 67.0, 2),
    ("BD", "Bangladesh", "Dhaka", 23.8, 90.4, 2), ("PH", "Philippines", "Manila", 14.6, 121.0, 2),
    ("MY", "Malaysia", "Kuala Lumpur", 3.1, 101.7, 2), ("TW", "Taiwan", "Taipei", 25.0, 121.6, 3),
    ("AU", "Australia", "Sydney", -33.9, 151.2, 2), ("NZ", "New Zealand", "Auckland", -36.8, 174.8, 1),
    ("CA", "Canada", "Toronto", 43.7, -79.4, 3), ("CA", "Canada", "Montréal", 45.5, -73.6, 2),
    ("MX", "Mexico", "Mexico City", 19.4, -99.1, 3), ("AR", "Argentina", "Buenos Aires", -34.6, -58.4, 2),
    ("CO", "Colombia", "Bogotá", 4.7, -74.1, 2), ("CL", "Chile", "Santiago", -33.4, -70.7, 1),
    ("PE", "Peru", "Lima", -12.0, -77.0, 1), ("ZA", "South Africa", "Johannesburg", -26.2, 28.0, 2),
    ("NG", "Nigeria", "Lagos", 6.5, 3.4, 2), ("KE", "Kenya", "Nairobi", -1.3, 36.8, 1),
    ("EG", "Egypt", "Cairo", 30.0, 31.2, 2), ("MA", "Morocco", "Casablanca", 33.6, -7.6, 1),
    ("IT", "Italy", "Milan", 45.5, 9.2, 2), ("ES", "Spain", "Madrid", 40.4, -3.7, 2),
    ("SE", "Sweden", "Stockholm", 59.3, 18.1, 2), ("FI", "Finland", "Helsinki", 60.2, 24.9, 1),
    ("CH", "Switzerland", "Zürich", 47.4, 8.5, 1), ("CZ", "Czechia", "Prague", 50.1, 14.4, 1),
    ("LT", "Lithuania", "Vilnius", 54.7, 25.3, 2), ("MD", "Moldova", "Chișinău", 47.0, 28.9, 1),
    ("KZ", "Kazakhstan", "Almaty", 43.2, 76.9, 1), ("UZ", "Uzbekistan", "Tashkent", 41.3, 69.2, 1),
    ("SA", "Saudi Arabia", "Riyadh", 24.7, 46.7, 1), ("AE", "United Arab Emirates", "Dubai", 25.2, 55.3, 2),
    ("IL", "Israel", "Tel Aviv", 32.1, 34.8, 1), ("SC", "Seychelles", "Victoria", -4.6, 55.5, 2),
    ("PA", "Panama", "Panama City", 9.0, -79.5, 1), ("IS", "Iceland", "Reykjavík", 64.1, -21.9, 1),
]
# Made-up operators. The AS numbers are the ones set aside for documentation.
NETWORKS = [name for name in (
    "Tin Can Hosting", "Sprocket Cloud", "Rustbucket Telecom", "Copper Coil Broadband",
    "Gearbox Datacentres", "Bolt and Rivet Networks", "Solder Point Internet", "Flywheel Mobile",
    "Ratchet VPS", "Cog and Sons Telecom", "Piston Fibre", "Dynamo Colocation", "Camshaft Cloud",
    "Gasket Online", "Servo Systems Hosting", "Anvil Wireless", "Crankshaft Communications",
    "Washer Net", "Turbine Telecom", "Greasepoint Hosting", "Loose Screw Labs", "Idle Valve Internet",
    "Spare Parts Cloud", "Ball Bearing Broadband", "Tappet Transit", "Sump Pump Hosting",
    "Manifold Networks", "Bent Antenna Mobile", "Lug Nut Data", "Overclocked Colo",
    "Third Gear Telecom", "Zinc Plate Internet")]
ASN = {name: f"AS{(list(range(64496, 64512)) + list(range(65536, 65552)))[i]}" for i, name in enumerate(NETWORKS)}

USERS = ["root", "admin", "ubuntu", "user", "test", "oracle", "postgres", "git", "deploy", "pi", "guest",
         "ftpuser", "mysql", "hadoop", "jenkins", "ansible", "docker", "debian", "centos", "support",
         "minecraft", "steam", "www", "backup", "nagios", "tomcat", "student", "dev", "vagrant", "operator"]
PATHS = ["GET /.env", "GET /wp-login.php", "GET /.git/config", "POST /xmlrpc.php", "GET /admin/",
         "GET /phpmyadmin/", "GET /actuator/health", "GET /cgi-bin/luci", "GET /config.json", "POST /login",
         "GET /server-status", "GET /.aws/credentials", "GET /api/v1/users", "POST /", "GET /backup.zip",
         "GET /owa/", "GET /manager/html", "GET /debug/default/view", "GET /solr/admin/info/system",
         "PROPFIND /"]
AGENTS = ["curl/8.5.0", "python-requests/2.31.0", "Go-http-client/1.1", "Mozilla/5.0 (compatible; TinScanner/1.0)",
          "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
          "masscan/1.3", "zgrab/0.x", "", "libwww-perl/6.72", "Wget/1.21.4"]


def pick(rng, rows, weight=lambda r: r[-1]):
    return rng.choices(rows, weights=[weight(r) for r in rows])[0]


def address(rng):
    if rng.random() < 0.08:
        return f"2001:db8:{rng.randrange(1, 0xffff):x}:{rng.randrange(1, 0xffff):x}::{rng.randrange(1, 0xffff):x}"
    return f"{rng.choice(('192.0.2', '198.51.100', '203.0.113'))}.{rng.randrange(1, 255)}"


def stamp(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(ts))


def replay(sid, now):
    """Every booking from EPOCH to now. Returns {(jail, ip): [booking, ...]}, oldest first."""
    spec = SERVERS[sid]
    history = collections.defaultdict(list)
    busy, due = {}, collections.defaultdict(list)      # ip -> free again at; step -> who comes back

    def book(who, at, rng):
        door = spec["jails"][who["jail"]]["door"]
        ban_no = len(history[who["jail"], who["ip"]]) + 1
        sentence = min(RULES[door]["bantime"] * 2 ** (ban_no - 1), RULES[door]["maxtime"])
        early = at + int(sentence * rng.uniform(0.2, 0.8)) if rng.random() < 0.03 else None
        history[who["jail"], who["ip"]].append(
            {"at": at, "sentence": sentence, "release": at + sentence, "ban_no": ban_no, "early": early, "who": who})
        out = early or at + sentence
        who["left"] -= 1
        if early or who["left"] <= 0:
            busy[who["ip"]] = out + (KEEP_DAYS + WINDOW_DAYS) * DAY     # nobody else gets this address meanwhile
            return
        back = out + int(rng.choice((90, 400, 1800, 7200, 30000, 90000)) * rng.uniform(0.5, 1.5))
        busy[who["ip"]] = back + STEP
        due[back // STEP].append(who)

    for step in range(EPOCH // STEP, now // STEP + 1):
        rng = random.Random(f"{sid}:{step}")
        at = step * STEP
        for who in due.pop(step, ()):
            book(who, at + rng.randrange(STEP), rng)
        for jail, chance in spec["arrivals"].items():
            if rng.random() >= chance:
                continue
            ip = address(rng)
            while busy.get(ip, 0) > at:
                ip = address(rng)
            for other in spec["jails"]:
                history.pop((other, ip), None)          # a new tenant at an old address starts with a clean sheet
            city = pick(rng, CITIES)
            net = random.Random(f"{city[0]}:{rng.randrange(4)}").choice(NETWORKS)    # a few operators per country
            # most are caught once; a stubborn few keep coming back for weeks
            stays = 1 if rng.random() < 0.8 else rng.choice((2, 2, 3, 3, 4, 5, 6, 8))
            book({"ip": ip, "jail": jail, "city": city, "org": net, "left": stays,
                  "names": rng.sample(USERS, rng.choice((1, 1, 1, 2, 3, 5))), "paths": rng.sample(PATHS, rng.choice((1, 2, 3))),
                  "agent": rng.choice(AGENTS), "pid": rng.randrange(1200, 990000), "port": rng.randrange(1024, 65000)},
                 at + rng.randrange(STEP), rng)
    for bookings in history.values():
        bookings[:] = [b for b in bookings if b["at"] <= now]
    return {key: bookings for key, bookings in history.items() if bookings}


def geo_of(who):
    cc, country, city, lat, lon, _ = who["city"]
    return {"cc": cc, "country": country, "city": city, "lat": lat, "lon": lon, "asn": ASN[who["org"]], "org": who["org"]}


def evidence(name, door, who, booking, rng):
    """The log lines fail2ban would have kept: the failures that led to this ban."""
    times, t = [], booking["at"]
    for _ in range(RULES[door]["maxretry"]):
        t -= rng.randrange(2, 400)
        times.append(t)
    lines = []
    for i, t in enumerate(reversed(times)):
        if door == "ssh":
            user = who["names"][i % len(who["names"])]
            said = (f"Connection closed by authenticating user {user} {who['ip']} port {who['port'] + i} [preauth]"
                    if user in ("root", "ubuntu", "backup", "www") else
                    f"Invalid user {user} from {who['ip']} port {who['port'] + i}")
            lines.append(f"{stamp(t)} {name} sshd[{who['pid'] + i * 7}]: {said}")
        else:
            path = who["paths"][i % len(who["paths"])]
            lines.append(f'{stamp(t)} {who["ip"]} "{path} HTTP/1.1" 401 0 auth=deny rt=0.000 ua="{who["agent"]}"')
    return lines


def export(sid, now=None):
    """One server's export, as the dictionary `jail-records export` prints as JSON."""
    now = int(now or time.time())
    spec, name = SERVERS[sid], sid
    since = now // DAY * DAY - WINDOW_DAYS * DAY
    today = random.Random(f"{sid}:day:{now // DAY}")

    records, geo, state, seen = [], {}, {}, {"ssh": {}, "web": {}}
    first_booking = now
    for (jail, ip), bookings in replay(sid, now).items():
        last, who = bookings[-1], bookings[-1]["who"]
        out = last["early"] if last["early"] and last["early"] <= now else last["release"]
        inside = out > now
        if not inside and out < now - KEEP_DAYS * DAY:
            continue
        door = spec["jails"][jail]["door"]
        rng = random.Random(f"{sid}:{ip}:{last['at']}")
        first_booking = min(first_booking, bookings[0]["at"])
        records.append({"ip": ip, "jail": jail, "banned_at": last["at"], "sentence": last["sentence"],
                        "release": last["release"], "inside": inside, "bancount": last["ban_no"],
                        "failures": RULES[door]["maxretry"],
                        "released_early": last["early"] if last["early"] and last["early"] <= now else None,
                        "evidence": evidence(name, door, who, last, rng)})
        geo[ip] = geo_of(who)
        state[ip] = "inside" if inside else "released"
        # what it did at the door during the window: the tries behind each ban in it
        tries = [b["at"] for b in bookings if b["at"] >= since]
        if tries:
            hits = len(tries) * RULES[door]["maxretry"] + rng.randrange(0, 6)
            if door == "ssh":
                counts = sorted(((u, 1 + rng.randrange(hits)) for u in who["names"]), key=lambda c: -c[1])
                seen["ssh"][ip] = {"attempts": hits, "users": [list(c) for c in counts[:8]],
                                   "distinct_users": len(counts), "first": tries[0] - rng.randrange(60, 3000),
                                   "last": tries[-1] - rng.randrange(1, 50)}
            else:
                counts = sorted(((p, 1 + rng.randrange(hits)) for p in who["paths"]), key=lambda c: -c[1])
                seen["web"][ip] = {"requests": hits, "paths": [list(c) for c in counts[:10]],
                                   "distinct_paths": len(counts), "uas": [[who["agent"], hits]],
                                   "first": tries[0] - rng.randrange(5, 500), "last": tries[-1] - rng.randrange(1, 5)}

    # the ones that knocked and got away: a handful by name, the rest only as numbers on the map
    doors = sorted({j["door"] for j in spec["jails"].values()})
    loose = {"ssh": 0, "web": 0}
    where = collections.Counter()                     # (city row, operator) -> loose addresses
    for door in doors:
        for _ in range(40 if door == "ssh" else 24):
            ip = address(today)
            while ip in geo:
                ip = address(today)
            city = pick(today, CITIES)
            who = {"city": city, "org": random.Random(f"{city[0]}:{today.randrange(4)}").choice(NETWORKS)}
            geo[ip] = geo_of(who)
            where[city, who["org"]] += 1
            loose[door] += 1
            first = since + today.randrange(now - since - 600)
            if door == "ssh":
                hits = max(1, int(today.paretovariate(1.1)))
                hits = min(hits, 140) if today.random() < 0.9 else 1
                names = today.sample(USERS, today.choice((0, 1, 1, 1, 2, 4)))
                seen["ssh"][ip] = {"attempts": hits, "users": [[u, 1 + today.randrange(hits)] for u in names],
                                   "distinct_users": len(names), "first": first,
                                   "last": min(now, first + today.randrange(60, 4 * DAY))}
            else:
                paths = today.sample(PATHS, 1)
                seen["web"][ip] = {"requests": 1, "paths": [[paths[0], 1]], "distinct_paths": 1,
                                   "uas": [[today.choice(AGENTS), 1]], "first": first, "last": first}
    crowd = spec["crowd"]
    for _ in range(crowd):
        city = pick(today, CITIES)
        where[city, random.Random(f"{city[0]}:{today.randrange(4)}").choice(NETWORKS)] += 1
    loose["ssh"] += crowd if "web" not in doors else int(crowd * 0.95)
    loose["web"] += 0 if "web" not in doors else crowd - int(crowd * 0.95)

    origins, countries, networks = {}, {}, {}

    def count(city, org, st, n, hits):
        cc, country, town, lat, lon, _ = city
        o = origins.setdefault((lat, lon), {"lat": lat, "lon": lon, "city": town, "cc": cc, "country": country,
                                            "inside": 0, "released": 0, "loose": 0, "hits": 0})
        c = countries.setdefault(cc, {"cc": cc, "country": country, "inside": 0, "released": 0, "loose": 0, "hits": 0})
        k = networks.setdefault(org, {"org": org, "asn": ASN[org], "cc": collections.Counter(),
                                      "inside": 0, "released": 0, "loose": 0, "hits": 0})
        for row in (o, c, k):
            row[st] += n
            row["hits"] += hits
        k["cc"][cc] += n

    by_ip = {r["ip"]: r for r in records}
    for ip, r in by_ip.items():
        g = geo[ip]
        city = next(c for c in CITIES if c[2] == g["city"] and c[0] == g["cc"])
        hits = seen["ssh"].get(ip, {}).get("attempts", 0) + seen["web"].get(ip, {}).get("requests", 0)
        count(city, g["org"], state[ip], 1, hits)
    for (city, org), n in where.items():
        count(city, org, "loose", n, n * today.randrange(2, 7))
    for k in networks.values():
        k["cc"] = k["cc"].most_common(1)[0][0]

    def timeline(door):
        if door not in doors:
            return [[h, 0] for h in range(since, now + 1, 3600)]
        rows = []
        for h in range(since, now + 1, 3600):
            rng = random.Random(f"{sid}:{door}:{h}")
            if door == "ssh":
                base = spec["knocks"] * (0.75 + 0.35 * abs(((h // 3600 + 7) % 24) - 12) / 12)
                v = int(rng.gauss(base, base * 0.25)) + (int(rng.uniform(40, 110)) if rng.random() < 0.05 else 0)
            else:
                v = int(rng.expovariate(0.9)) + (int(rng.uniform(20, 70)) if rng.random() < 0.03 else 0)
            rows.append([h, max(0, v)])
        return rows

    lines = {door: timeline(door) for door in ("ssh", "web")}
    top_users = collections.Counter({u: int(sum(v for _, v in lines["ssh"]) * w) for u, w in zip(
        USERS, (.31, .12, .07, .05, .04, .035, .03, .025, .02, .018, .015, .012))})
    top_paths = collections.Counter({p: max(1, int(sum(v for _, v in lines["web"]) * w)) for p, w in zip(
        PATHS, (.22, .14, .1, .08, .06, .05, .04, .035, .03, .025, .02, .015))}) if "web" in doors else {}
    booked = {door: sum(1 for ip in seen[door] if ip in by_ip) for door in ("ssh", "web")}

    return {
        "generated": now, "host": name, "window_days": WINDOW_DAYS, "window_start": since,
        "f2b_started": now // DAY * DAY - 3 * DAY + 7 * 3600 + 1260,
        "records_since": first_booking, "office_opened": EPOCH,
        "geo_source": "invented sample data", "home": spec["home"],
        "jails": {j: {**RULES[s["door"]], **s} for j, s in spec["jails"].items()},
        "records": records, "ssh": seen["ssh"], "web": seen["web"], "geo": geo,
        "origins": sorted(origins.values(), key=lambda o: -(o["inside"] * 1000 + o["released"] * 100 + o["loose"])),
        "countries": sorted(countries.values(), key=lambda c: -(c["inside"] + c["released"] + c["loose"])),
        "networks": sorted(networks.values(), key=lambda k: (-(k["inside"] + k["released"]), -k["loose"]))[:12],
        "totals": {
            "ssh_attempts": sum(v for _, v in lines["ssh"]), "ssh_addresses": booked["ssh"] + loose["ssh"],
            "ssh_loose": loose["ssh"],
            "web_requests": sum(v for _, v in lines["web"]), "web_addresses": booked["web"] + loose["web"],
            "web_loose": loose["web"],
            "top_users": [[u, v] for u, v in top_users.most_common(12)],
            "top_paths": [[p, v] for p, v in (top_paths.most_common(12) if top_paths else [])],
        },
        "timeline": lines,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in SERVERS:
        sys.exit(__doc__)
    print(json.dumps(export(sys.argv[1]), separators=(",", ":")))

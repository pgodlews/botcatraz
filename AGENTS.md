# Notes for coding agents

Read [`README.md`](README.md) for what the project does and
[`ARCHITECTURE.md`](ARCHITECTURE.md) for how the parts fit together. This file
covers the rules that are easy to break.

## Commands

Run these before you call a change done. All of them also run in CI.

```bash
python3 -m unittest discover -s tests
```

```bash
shellcheck ./*.sh server/install.sh webhost/install.sh tests/*.sh
```

```bash
tests/check_fail2ban.sh
```

```bash
tests/check_art.sh
```

```bash
./build.py --sample && node tests/check_pages.js
```

- `tests/check_fail2ban.sh` needs fail2ban installed. `FAIL2BAN_REGEX` points it
  at another `fail2ban-regex`.
- `tests/check_art.sh` needs Pillow 11.3.0. On Linux, add `--pixels`: zlib
  there writes different PNG bytes for the same pixels.
- `tests/check_pages.js` needs Playwright and its Chromium. `PW_CHANNEL=chrome`
  uses an installed Chrome instead.
- To look at the pages, run `./build.py --sample`, then
  `python3 -m http.server 8850 --bind 127.0.0.1 --directory www`.

## Privacy: the rule that matters most

The real pages hold real attackers' addresses and real log lines. None of that
may enter the repository.

- `out/`, `www/`, `servers.json`, `sites/` and `install.conf` are ignored. Keep
  it that way, and never commit a real export or a page built from one.
- Test logs, samples, examples and screenshots use only the documentation
  ranges: `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` and
  `2001:db8::/32`. Host names use `example.com`.
- In `tests/fail2ban/*.log`, a line that must count as a failure comes from
  `203.0.113.0/24` or `2001:db8::/32`. Lines that must not count come from
  `198.51.100.0/24`, and legitimate users from `192.0.2.0/24`.
- No real host names, user names, home directory paths or email addresses in
  code, comments, docs or commit messages.
- No agent session links (such as `Claude-Session:` trailers) in commit
  messages or files.
- Screenshots in `docs/` are taken with `docs/take_screenshots.js`, which blanks
  dates, times and the second half of every address. It blanks text only:
  look at every picture before committing it, and never commit a screenshot
  taken any other way from a real server.

## Code

- **No dependencies.** `server/jail-records`, `build.py` and
  `sample/make_sample.py` use the Python standard library only, and must run on
  Python 3.9. The one exception is `maxminddb` on the server, which
  `install.sh` installs. The art generators use Pillow and nothing else.
- **The pages have no libraries and no build step.** Each one is a single HTML
  file with inline script and style. Data and art are inlined by `build.py`.
  The only external request is the Google Fonts `<link>`.
- **Placeholders** (`/*__DATA__*/null`, `{{NAME}}`, `<!--NAV-->` and the
  others listed in `ARCHITECTURE.md`) must stay valid JavaScript or HTML before
  they are filled, and every one must be filled by `build.py`.
  `tests/test_build.py` fails if one is left over.
- **Write files in one step.** Use `write()` in `build.py` (a `.tmp` file, then
  rename), so the web server never serves half a file.
- **A failed export never replaces a good one.** One unreachable server must
  not take down the other servers' pages.
- **The server tool runs as root, in a sandbox.** `sync` keeps to what
  `jail-records.service` allows: write only under `/var/lib/jail-records`, no IP
  network (anything that downloads belongs in `geo-update`), no capability but
  reading files. If a change needs more, widen the unit on purpose and say why.
  `export` must stay a plain read of the snapshot that needs no root: the web
  host's SSH key is locked to it. Keep it read-only towards fail2ban and the
  logs. `is-trusted` is fail2ban's `ignorecommand`: it must read only, be fast,
  and answer "not trusted" on any error.
- **Web log format.** If you change the line format that `read_web()` parses,
  change `fail2ban/filter.d/web-auth.conf` and `fail2ban/README.md` with it.
  `POLITE` in `jail-records` must stay equal to the filter's `ignoreregex`
  alternation; `tests/test_server.py` checks that.
- Shell scripts use `set -euo pipefail` and must pass ShellCheck. Avoid
  `A && B || C`.

## Art

- [`docs/ART.md`](docs/ART.md) shows all the art and is the guide to changing it.
- Never edit the PNGs or JSON under `yard/art/`, or the pictures in `docs/art/`,
  by hand. Change a generator and run it. Order matters:

  ```bash
  python3 yard/art/robots/make_robots.py
  ```

  ```bash
  python3 yard/art/scene/make_scene.py
  ```

  ```bash
  python3 yard/art/mugshots/make_mugshots.py
  ```

  ```bash
  python3 docs/make_art_page.py
  ```

- The generators are deterministic, and the committed art was made with Pillow
  11.3.0 on macOS. After a change, commit the generator and every file it
  rewrote. `tests/check_art.sh` must then pass on macOS byte for byte.
- Their previews, reports and check transcripts are ignored by git. Look at the
  previews before committing art.
- The number of robot types comes from the files. If you add a type, add it to
  the type list in `make_robots.py` (and move `GUARD`, the guard's index, past
  it) and to `TYPES` in `make_mugshots.py` (and its `N_TYPES` assertion), together.
  `tests/test_build.py` checks that the sheets, `robots.json` and
  `mugshots.json` agree. The pages need no change.
- The palette is fixed by `yard/SPEC.md`. The generators check it.

## Docs

- Keep `README.md`, `ARCHITECTURE.md` and the docstrings in step with the code
  in the same commit. That covers the export commands, options, placeholders,
  units and the number of robot types.
- `ARCHITECTURE.md` diagrams are Mermaid. Keep them small enough to read on
  GitHub.
- Third-party material and its licence go in `THIRD-PARTY.md`.

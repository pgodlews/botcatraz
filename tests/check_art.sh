#!/usr/bin/env bash
# Runs the three art generators in order, then docs/make_art_page.py, and checks
# that they write exactly the committed images, JSON and docs/ART.md. Needs
# Python 3 with Pillow; the committed art was made with Pillow 11.3.0 on macOS.
#
#   tests/check_art.sh            every file byte for byte (macOS)
#   tests/check_art.sh --pixels   PNGs may be compressed differently but must
#                                 decode to the same pixels; other files byte for byte
#                                 (Linux, whose zlib writes different PNG bytes)
set -euo pipefail

pixels=0
case "${1:-}" in
    "") ;;
    --pixels) pixels=1 ;;
    *) echo "usage: $0 [--pixels]" >&2; exit 2 ;;
esac

cd "$(dirname "$0")/../yard/art"
for step in robots/make_robots.py scene/make_scene.py mugshots/make_mugshots.py; do
    echo "== $step"
    python3 "$step" > /dev/null
done
echo "== docs/make_art_page.py"
python3 ../../docs/make_art_page.py > /dev/null

changed=$(git status --porcelain --untracked-files=all -- . ../../docs/art ../../docs/ART.md)
if [ -z "$changed" ]; then
    echo "ok   all generated art matches the committed files byte for byte"
    exit 0
fi
if [ "$pixels" = 0 ]; then
    echo "The generators wrote different art from what is committed:"
    echo "$changed"
    exit 1
fi

# Paths from git status are relative to the repository root.
cd "$(git rev-parse --show-toplevel)"
printf '%s\n' "$changed" | python3 -c '
import io, subprocess, sys
from PIL import Image

bad, same = [], 0
for line in sys.stdin.read().splitlines():
    status, path = line[:2], line[3:]
    if status != " M" or not path.endswith(".png"):
        bad.append(f"{status.strip()} {path}")
        continue
    old = Image.open(io.BytesIO(subprocess.run(["git", "show", "HEAD:" + path],
                                               check=True, capture_output=True).stdout))
    new = Image.open(path)
    if (old.mode, old.size, old.tobytes(), old.getpalette()) != (new.mode, new.size, new.tobytes(), new.getpalette()):
        bad.append(f"pixels differ: {path}")
    else:
        same += 1
if bad:
    print("The generators wrote different art from what is committed:")
    print("\n".join(bad))
    sys.exit(1)
print(f"ok   all generated art matches; {same} PNGs have the same pixels in different bytes")
'

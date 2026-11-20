#!/usr/bin/env bash
# Runs the filters in fail2ban/ over the test logs in tests/fail2ban/ and checks
# what they count.
#
# Convention in the test logs: a line that must count as a failure comes from
# 203.0.113.0/24 or 2001:db8::/32. Every other line (198.51.100.0/24 for what
# must be ignored, 192.0.2.0/24 for legitimate users) must not count.
#
#   tests/check_fail2ban.sh [CONFIG_DIR]
#
# CONFIG_DIR is a stock fail2ban configuration (default /etc/fail2ban); it is
# copied, never changed. FAIL2BAN_REGEX overrides the command to run.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
repo=$(dirname "$here")
stock=${1:-/etc/fail2ban}
regex=${FAIL2BAN_REGEX:-fail2ban-regex}

conf=$(mktemp -d)
trap 'rm -rf "$conf"' EXIT
cp -R "$stock/." "$conf/"
cp "$repo"/fail2ban/filter.d/* "$conf/filter.d/"

failed=0
for pair in sshd.log:sshd web.log:web-auth; do
    log=$here/fail2ban/${pair%%:*}
    filter=${pair##*:}
    want=$(grep -oE '^[^"]*(203\.0\.113\.[0-9]+|2001:db8::[0-9a-f]+)' "$log" \
        | grep -oE '(203\.0\.113\.[0-9]+|2001:db8::[0-9a-f]+)$' | sort)
    # shellcheck disable=SC2086  # FAIL2BAN_REGEX may be a command with arguments
    got=$($regex --config "$conf" --out ip "$log" "$filter" | sort)
    if [ "$want" = "$got" ]; then
        echo "ok   $filter: $(echo "$got" | wc -l | tr -d ' ') failures counted, as expected"
    else
        echo "FAIL $filter"
        diff <(echo "$want") <(echo "$got") | sed 's/^</  expected but not counted:/; s/^>/  counted but not expected:/' | grep counted || true
        failed=1
    fi
done
exit $failed

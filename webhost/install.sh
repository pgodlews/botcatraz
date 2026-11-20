#!/usr/bin/env bash
# Install or update the page builder and its web service on this machine.
# Run as root from the copy ../deploy-web.sh put here. Safe to re-run.
#
#   sudo bash webhost/install.sh [--unit NAME] [--user USER] [--port N] [--bind ADDR] [--every MIN]
#   bash webhost/install.sh --print [...]    show the three unit files, install nothing
#   sudo bash webhost/install.sh --remove    stop and remove the units (the files stay)
#
#   --unit   base name of the systemd units          default jail-pages
#            (NAME.service, NAME-build.service, NAME-build.timer)
#   --user   account that fetches, builds and serves  default: the owner of this directory
#   --port   port the pages are served on             default 8850
#   --bind   address to listen on                     default 127.0.0.1
#            (0.0.0.0 to serve the whole network; see the README first)
#   --every  minutes between rebuilds, 1 to 30        default 5
#
# The install directory is wherever this copy lives (the parent of webhost/).
# What you choose is remembered in install.conf there, so a later run without
# options keeps it.
set -euo pipefail
cd "$(dirname "$0")/.."
dir=$(pwd -P)

unit=jail-pages user='' port=8850 bind=127.0.0.1 every=5
if [ -f install.conf ]; then
    while IFS='=' read -r key value; do
        case $key in unit|user|port|bind|every) printf -v "$key" %s "$value" ;; esac
    done < install.conf
fi
mode=install
while [ $# -gt 0 ]; do
    case $1 in
        --unit|--user|--port|--bind|--every)
            [ $# -ge 2 ] || { echo "install.sh: $1 needs a value" >&2; exit 2; }
            printf -v "${1#--}" %s "$2"; shift 2 ;;
        --print) mode=print; shift ;;
        --remove) mode=remove; shift ;;
        *) echo "install.sh: unknown option $1" >&2; exit 2 ;;
    esac
done
[ -n "$user" ] || user=$(stat -c %U . 2>/dev/null || stat -f %Su .)

bad() { echo "install.sh: $1" >&2; exit 2; }
in_range() { [[ $1 =~ ^[0-9]+$ ]] && [ "$1" -ge "$2" ] && [ "$1" -le "$3" ]; }
[[ $unit =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] || bad "--unit: letters, digits, . _ - only"
[[ $user =~ ^[a-z_][a-z0-9_-]*$ ]] || bad "--user: not an account name: $user"
in_range "$port" 1 65535 || bad "--port: 1 to 65535"
[[ $bind =~ ^[0-9A-Fa-f.:]+$ ]] || bad "--bind: an IPv4 or IPv6 address"
in_range "$every" 1 30 || bad "--every: 1 to 30"
[[ $dir =~ ^/[A-Za-z0-9_./-]+$ ]] || bad "install directory has characters systemd units cannot carry: $dir"

render() {
    sed -e "s|@USER@|$user|g" -e "s|@DIR@|$dir|g" -e "s|@PORT@|$port|g" \
        -e "s|@BIND@|$bind|g" -e "s|@EVERY@|$every|g" "webhost/$1"
}

if [ "$mode" = print ]; then
    for pair in "pages.service.in:$unit.service" "build.service.in:$unit-build.service" "build.timer.in:$unit-build.timer"; do
        echo "# /etc/systemd/system/${pair#*:}"; render "${pair%%:*}"; echo
    done
    exit 0
fi

[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }
if [ "$mode" = remove ]; then
    systemctl disable --now "$unit.service" "$unit-build.timer" 2>/dev/null || true
    rm -f "/etc/systemd/system/$unit.service" "/etc/systemd/system/$unit-build.service" "/etc/systemd/system/$unit-build.timer"
    systemctl daemon-reload
    echo "removed the $unit units; $dir is untouched"
    exit 0
fi

id "$user" >/dev/null 2>&1 || bad "--user: no such account: $user"
group=$(id -gn "$user")
render pages.service.in > "/etc/systemd/system/$unit.service"
render build.service.in > "/etc/systemd/system/$unit-build.service"
render build.timer.in   > "/etc/systemd/system/$unit-build.timer"
chmod 644 "/etc/systemd/system/$unit.service" "/etc/systemd/system/$unit-build.service" "/etc/systemd/system/$unit-build.timer"
install -d -o "$user" -g "$group" www out
printf 'unit=%s\nuser=%s\nport=%s\nbind=%s\nevery=%s\n' "$unit" "$user" "$port" "$bind" "$every" > install.conf
chown "$user:$group" install.conf
[ -f servers.json ] || echo "no servers.json in $dir yet: copy servers.example.json and edit it" >&2

systemctl daemon-reload
systemctl start "$unit-build.service" || echo "a build failed; see: journalctl -u $unit-build" >&2
systemctl enable --now "$unit-build.timer" "$unit.service"
systemctl restart "$unit.service"
systemctl --no-pager list-timers "$unit-build.timer" | sed -n 1,2p
echo "serving $dir/www on $bind:$port"

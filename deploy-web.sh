#!/usr/bin/env bash
# Put the page builder on a web host and (re)start its timer and web service.
# The web host is any Linux machine with systemd, Python 3 and SSH access to the
# servers; it can be one of the servers themselves.
#
# Usage: ./deploy-web.sh <ssh-host> [--dir DIR] [--servers FILE] [install options]
#   --dir DIR       where it lives on the web host (default jail-pages, in the
#                   login's home directory; an absolute path works too)
#   --servers FILE  installed there as servers.json (default: servers.json here,
#                   if there is one; without it the host keeps what it has)
#   anything else is passed to webhost/install.sh: --unit --user --port --bind --every
#
# Example: ./deploy-web.sh webhost --port 8080 --bind 0.0.0.0
set -euo pipefail
host=${1:?usage: ./deploy-web.sh <ssh-host> [--dir DIR] [--servers FILE] [install options]}
shift
cd "$(dirname "$0")"
dir=jail-pages servers='' pass=()
[ ! -f servers.json ] || servers=servers.json
while [ $# -gt 0 ]; do
    case $1 in
        --dir) dir=${2:?--dir needs a value}; shift 2 ;;
        --servers) servers=${2:?--servers needs a value}; shift 2 ;;
        --unit|--user|--port|--bind|--every) pass+=("$1" "${2:?$1 needs a value}"); shift 2 ;;
        *) echo "deploy-web.sh: unknown option $1" >&2; exit 2 ;;
    esac
done
[[ $dir =~ ^[A-Za-z0-9_./-]+$ ]] || { echo "deploy-web.sh: --dir: plain path characters only" >&2; exit 2; }
# shellcheck disable=SC2029  # $dir is meant to expand here
ssh "$host" "mkdir -p '$dir'"
rsync -a --delete --exclude .DS_Store --exclude preview --exclude __pycache__ \
    build.py template.html landing.html land-110m.json servers.example.json webhost yard "$host:$dir/"
[ -z "$servers" ] || scp -q "$servers" "$host:$dir/servers.json"
# printf with no arguments would still print '' once, so only quote real options.
args=""
[ ${#pass[@]} -eq 0 ] || args=$(printf ' %q' "${pass[@]}")
# shellcheck disable=SC2029
ssh "$host" "sudo bash '$dir/webhost/install.sh'$args"

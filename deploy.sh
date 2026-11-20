#!/usr/bin/env bash
# Copy server/ to a server and run its install.sh there. Safe to re-run.
# Usage: ./deploy.sh <ssh-host> [settings.json] [--export-key KEY.pub]
#   settings.json becomes /etc/jail-records.json on that server (see
#   server/jail-records.example.json). Without it the server keeps what it has.
#   --export-key installs the web host's public key for the jail-export account,
#   locked to `jail-records export`. Without it the account keeps what it has.
# Needs: SSH access as a user who can sudo, and rsync on both ends.
set -euo pipefail
usage="usage: ./deploy.sh <ssh-host> [settings.json] [--export-key KEY.pub]"
host="" settings="" key=""
while [ $# -gt 0 ]; do
    case $1 in
        --export-key) key=${2:?$usage}; shift 2 ;;
        -*) echo "$usage" >&2; exit 2 ;;
        *) if [ -z "$host" ]; then host=$1; elif [ -z "$settings" ]; then settings=$1; else echo "$usage" >&2; exit 2; fi
           shift ;;
    esac
done
[ -n "$host" ] || { echo "$usage" >&2; exit 2; }
cd "$(dirname "$0")"
rsync -a --delete --exclude .DS_Store server/ "$host:jail-records/"
[ -z "$settings" ] || scp -q "$settings" "$host:jail-records/site.json"
[ -z "$key" ] || scp -q "$key" "$host:jail-records/export-key.pub"
ssh "$host" 'sudo bash ~/jail-records/install.sh'

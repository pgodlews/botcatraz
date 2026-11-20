#!/usr/bin/env bash
# Install or update the jail record office on this server. Idempotent.
# Run as root from a copy of this directory (../deploy.sh does that from your own machine).
#
# Optional files next to this script:
#   site.json        becomes /etc/jail-records.json
#   export-key.pub   public SSH key(s) of the web host. Creates the jail-export account,
#                    whose keys may run only `jail-records export`. Replaces its keys.
set -euo pipefail
cd "$(dirname "$0")"
[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }

# The reader for the offline country/network databases, from Ubuntu's own archive
python3 -c 'import maxminddb' 2>/dev/null || \
    DEBIAN_FRONTEND=noninteractive apt-get install -y -q python3-maxminddb >/dev/null

[ ! -f site.json ] || install -m 644 site.json /etc/jail-records.json

# Records: root only. Snapshot: root and the jail-export group, and the directory
# is setgid so each new snapshot takes that group.
getent group jail-export >/dev/null || groupadd --system jail-export
install -d -m 711 /var/lib/jail-records
install -d -m 2750 -g jail-export /var/lib/jail-records/export
chmod 600 /var/lib/jail-records/records.sqlite3 2>/dev/null || true

install -m 755 jail-records /usr/local/sbin/jail-records
install -m 644 jail-records.service jail-records.timer jail-records-geo.service jail-records-geo.timer \
    /etc/systemd/system/

if [ -f export-key.pub ]; then
    # The account the web host logs in as. Its keys are locked to one command, with
    # no shell, no forwarding and no terminal, and it cannot change its own keys:
    # the home directory and the key file belong to root.
    home=/var/lib/jail-export
    getent passwd jail-export >/dev/null ||
        useradd --system --gid jail-export --home-dir "$home" --no-create-home --shell /bin/sh jail-export
    usermod -p '*' jail-export   # no password, but not "locked": sshd refuses locked accounts
    install -d -m 750 -o root -g jail-export "$home" "$home/.ssh"
    grep -E '^(ssh-|ecdsa-|sk-)' export-key.pub |
        sed 's|^|command="/usr/local/sbin/jail-records export",restrict |' > "$home/.ssh/authorized_keys.new"
    [ -s "$home/.ssh/authorized_keys.new" ] || { echo "export-key.pub holds no SSH public key" >&2; exit 1; }
    chown root:jail-export "$home/.ssh/authorized_keys.new"
    chmod 640 "$home/.ssh/authorized_keys.new"
    mv "$home/.ssh/authorized_keys.new" "$home/.ssh/authorized_keys"
    echo "jail-export: $(wc -l < "$home/.ssh/authorized_keys") key(s), locked to 'jail-records export'"
    if sshd -T 2>/dev/null | grep -qiE '^(allowusers|allowgroups) '; then
        echo "note: sshd has AllowUsers/AllowGroups set; add jail-export there or it cannot log in" >&2
    fi
fi

# An earlier version ran sync from the export; the old sudo rule is no longer needed.
if grep -rqs 'jail-records export' /etc/sudoers.d/; then
    echo "note: a sudoers rule for 'jail-records export' is no longer needed; remove it from /etc/sudoers.d" >&2
fi

systemctl daemon-reload
systemctl enable jail-records.timer jail-records-geo.timer >/dev/null
systemctl restart jail-records.timer jail-records-geo.timer

systemctl start jail-records-geo.service ||
    echo "no geo databases yet: records will have no countries until 'jail-records geo-update' works" >&2
systemctl start jail-records.service || { journalctl -u jail-records.service -n 20 --no-pager >&2; exit 1; }
jail-records stats

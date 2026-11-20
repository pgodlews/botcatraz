# fail2ban recipes (optional)

The record keeper works with fail2ban as you already run it: it records whatever
jails you name in `/etc/jail-records.json`. These two recipes are the jails the
pages were first built around. Use them, adapt them or ignore them.

Both were written against fail2ban 1.0.2, the version in Ubuntu 24.04 and
Debian 12. Before you rely on a filter, dry-run it over your own logs and look
for your own addresses in the matches:

```bash
sudo fail2ban-regex systemd-journal -m _SYSTEMD_UNIT=ssh.service sshd --print-all-matched
```

```bash
sudo fail2ban-regex /var/log/nginx/protected.access.log web-auth --print-all-matched
```

## 1. Count key-only SSH guesses

On a server where SSH accepts keys only, most guessing bots name a user and hang
up when they find there is no password to try. fail2ban's stock `sshd` filter
does not count that in its normal mode, so the busiest guessers are never banned,
and `mode = aggressive` goes too far the other way (it also counts key scans and
health checks).

| File | Install as | What it does |
|---|---|---|
| [`filter.d/sshd.local`](filter.d/sshd.local) | `/etc/fail2ban/filter.d/sshd.local` | Counts a hang-up during authentication by a real account name as one failure |
| [`jail.local.example`](jail.local.example) | `/etc/fail2ban/jail.local` | Three failures in an hour: 24 hours, doubling per repeat up to 7 days |

The example jail never bans an address that has logged in over SSH: before
counting a failure, fail2ban asks `jail-records is-trusted <address>`
(`ignorecommand`). That is true for the addresses listed under `own` in
`/etc/jail-records.json`, for any address on the record keeper's trusted list
for an SSH login, and for one that logged in during the last day. So install
`jail-records` first.

The addresses in `ignoreip` are placeholders from the documentation ranges
(203.0.113.0/24, 198.51.100.0/24, 2001:db8::/32). Replace them with your own.

```bash
sudo install -m 644 filter.d/sshd.local /etc/fail2ban/filter.d/sshd.local
```

```bash
sudo install -m 644 jail.local.example /etc/fail2ban/jail.local
```

```bash
sudo fail2ban-client -t && sudo fail2ban-client reload
```

The second command replaces an existing `jail.local`: merge by hand if you have
one. Keep a second way in to the server before you tighten an SSH jail.

## 2. A jail for a token-protected web site

For a site behind nginx where every legitimate request carries a token (an API,
a webhook receiver, a private tool), so a request without one is a stranger
trying the door. nginx decides whether the token was valid and writes that in
its log; fail2ban and `jail-records` both read the log.

In the `http` block, for example:

```nginx
# A long token needs a bigger bucket than nginx's default, or nginx will not start.
map_hash_bucket_size 128;

# "ok" only when the Authorization header carries the token.
map $http_authorization $door_auth {
    default deny;
    "Bearer REPLACE-WITH-A-LONG-RANDOM-TOKEN" ok;
}

# Never logs the Authorization header.
log_format door '$time_iso8601 $remote_addr "$request" $status $body_bytes_sent '
                'auth=$door_auth rt=$request_time ua="$http_user_agent"';
```

and in the site's `server` block:

```nginx
access_log /var/log/nginx/protected.access.log door;
if ($door_auth = deny) { return 401; }
```

The fields the readers need are the time, the address, the quoted request, the
status, the byte count, `auth=ok|deny` and, last on the line, `ua="..."`. Any
`name=value` fields in between are ignored.

| File | Install as | What it does |
|---|---|---|
| [`filter.d/web-auth.conf`](filter.d/web-auth.conf) | `/etc/fail2ban/filter.d/web-auth.conf` | A failure is a request without a valid token; ordinary front-door requests are ignored |
| [`jail.d/web-auth.conf`](jail.d/web-auth.conf) | `/etc/fail2ban/jail.d/web-auth.conf` | Two failures in 10 minutes: 24 hours, web ports only |

The filter ignores what a browser or a polite crawler asks any server for
(`/`, `/favicon.ico`, `/robots.txt` and the like; the full list is in the filter
file) and anything under `/.well-known/`. `jail-records` uses the same list to
decide what counts as a knock at the web door.

Then name the jail and the log in `/etc/jail-records.json`:

```json
{
  "jails": {
    "sshd": {"door": "ssh", "wing": "S", "label": "SSH"},
    "web-auth": {"door": "web", "wing": "W", "label": "web endpoint"}
  },
  "web_logs": "/var/log/nginx/protected.access.log*"
}
```

"""Checks for server/jail-records that need no root, no fail2ban and no database.

    python3 -m unittest discover -s tests
"""
import importlib.machinery
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_jail_records():
    loader = importlib.machinery.SourceFileLoader("jail_records", str(ROOT / "server" / "jail-records"))
    spec = importlib.util.spec_from_loader("jail_records", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class WebLog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jr = load_jail_records()
        cls.jr.ACCESS_LOGS = str(ROOT / "tests" / "fail2ban" / "web.log")
        cls.rows, cls.friends = cls.jr.read_web()

    def test_knocks(self):
        # Every tokenless request except the polite ones and certificate checks.
        self.assertEqual(sorted(r["ip"] for r in self.rows), sorted([
            "203.0.113.21", "203.0.113.22", "2001:db8::21", "203.0.113.23", "203.0.113.24",
            "198.51.100.34"]))

    def test_rows(self):
        first = self.rows[0]
        self.assertEqual(first["req"], "GET /wp-login.php")
        self.assertEqual(first["ts"], self.jr.utc("2026-11-20 10:00:01"))
        self.assertTrue(first["ua"].startswith("Mozilla/5.0"))

    def test_token_holders_are_friends(self):
        self.assertEqual(self.friends, {"192.0.2.10"})

    def test_polite_list_matches_the_fail2ban_filter(self):
        # jail-records and the web-auth filter must agree on what is not a knock.
        text = (ROOT / "fail2ban" / "filter.d" / "web-auth.conf").read_text()
        filter_polite = re.search(r'"\(\?:GET\|HEAD\) (/\S+) HTTP$', text, re.M).group(1)
        self.assertIn(filter_polite + " HTTP", self.jr.POLITE.pattern)
        self.assertEqual(self.jr.POLITE.pattern, "(?:GET|HEAD) " + filter_polite + " HTTP")


class Config(unittest.TestCase):
    def test_example_settings_load(self):
        import json
        cfg = json.loads((ROOT / "server" / "jail-records.example.json").read_text())
        self.assertIn("jails", cfg)
        for spec in cfg["jails"].values():
            self.assertIn(spec.get("door", "ssh"), ("ssh", "web"))


if __name__ == "__main__":
    unittest.main()


class Snapshot(unittest.TestCase):
    """sync writes the export snapshot; export only prints it."""

    def test_written_in_one_step_and_printed_as_is(self):
        import contextlib
        import io
        import os
        import stat
        import tempfile
        jr = load_jail_records()
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "export", "jail.json")
            jr.write_snapshot('{"records":[]}', path)
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o640)
            self.assertEqual(os.listdir(os.path.dirname(path)), ["jail.json"])
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                jr.print_snapshot(path)
            self.assertEqual(out.getvalue(), '{"records":[]}\n')

    def test_missing_snapshot_is_an_error(self):
        jr = load_jail_records()
        with self.assertRaises(SystemExit) as caught:
            jr.print_snapshot("/nonexistent/jail.json")
        self.assertIn("jail-records sync", str(caught.exception.code))


class Units(unittest.TestCase):
    """The sandbox must leave sync its records to write, and keep it off the network."""

    def unit(self, name):
        lines = (ROOT / "server" / name).read_text().splitlines()
        return dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))

    def test_sync_is_sandboxed_and_offline(self):
        jr = load_jail_records()
        sync = self.unit("jail-records.service")
        self.assertEqual(sync["ExecStart"], "/usr/local/sbin/jail-records sync")
        self.assertEqual(sync["ProtectSystem"], "strict")
        self.assertEqual(sync["ReadWritePaths"], jr.HOME)
        self.assertEqual(sync["CapabilityBoundingSet"], "CAP_DAC_READ_SEARCH")
        self.assertNotIn("AF_INET", sync["RestrictAddressFamilies"])
        self.assertEqual(sync["IPAddressDeny"], "any")

    def test_geo_download_has_no_root_powers(self):
        geo = self.unit("jail-records-geo.service")
        self.assertEqual(geo["ExecStart"], "/usr/local/sbin/jail-records geo-update")
        self.assertEqual(geo["CapabilityBoundingSet"], "")
        self.assertEqual(geo["ProtectSystem"], "strict")


class SshJournal(unittest.TestCase):
    """read_ssh over journal lines, without journalctl."""

    LINES = """\
2026-11-20T10:00:00+00:00 server1 sshd[100]: Server listening on 0.0.0.0 port 22.
2026-11-20T10:00:00+00:00 server1 sshd[100]: Server listening on :: port 22.
2026-11-20T10:01:00+00:00 server1 sshd[201]: Connection closed by authenticating user root 203.0.113.5 port 40000 [preauth]
2026-11-20T10:02:00+00:00 server1 sshd[202]: Invalid user oracle from 203.0.113.8 port 40001
2026-11-20T10:03:00+00:00 server1 sshd[203]: Accepted publickey for alice from 192.0.2.10 port 40002 ssh2: ED25519 SHA256:x
"""

    def test_connections_and_logins(self):
        jr = load_jail_records()
        jr.run = lambda *cmd: self.LINES
        conns, accepted = jr.read_ssh(0)
        self.assertEqual(sorted((c["ip"], c["user"]) for c in conns),
                         [("203.0.113.5", "root"), ("203.0.113.8", "oracle")])
        self.assertEqual(accepted, {"192.0.2.10"})

"""Tests for the pure parts of watch.py (no network). Run: python3 -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import watch  # noqa: E402


def ev(eid, film="Odyssea", dt="2026-11-20T18:00:00", cinema="Praha Flora"):
    return {"id": eid, "film": film, "filmLink": f"https://x.test/{film}", "cinema": cinema, "cinemaId": "1",
            "datetime": dt, "auditorium": "IMAX", "attrs": [], "booking": f"https://x.test/order/{eid}", "soldOut": False}


class TitleAndReport(unittest.TestCase):
    def test_single_film_title_is_unchanged(self):
        self.assertEqual(watch.title_for([ev("1")]), "🎬 Odyssea v IMAXu: 1 nový termín (20. 11.)")

    def test_title_does_not_claim_one_film_for_several(self):
        title = watch.title_for([ev("1"), ev("2", film="Duna")])
        self.assertIn("Odyssea a 1 další", title)

    def test_report_names_film_per_line_only_when_ambiguous(self):
        one = watch.render([ev("1"), ev("2")], [])
        self.assertNotIn("- Odyssea · ", one)
        self.assertIn("[Stránka filmu na Cinema City]", one)
        many = watch.render([ev("1"), ev("2", film="Duna")], [])
        self.assertIn("- Odyssea · ", many)
        self.assertIn("- Duna · ", many)
        self.assertIn("[Duna na Cinema City]", many)


class State(unittest.TestCase):
    def test_prune_keeps_recent_and_future(self):
        with mock.patch.object(watch, "now", return_value=watch.datetime(2026, 11, 12, 12, 0)):
            kept = watch.prune_past({"old": ev("old", dt="2026-11-10T10:00:00"), "new": ev("new")})
        self.assertEqual(list(kept), ["new"])


class Api(unittest.TestCase):
    def test_truncated_or_malformed_response_is_retried_then_reported(self):
        calls = []

        def boom(*a, **kw):
            calls.append(1)
            raise watch.http.client.IncompleteRead(b"")

        with mock.patch.object(watch.urllib.request, "urlopen", boom), mock.patch.object(watch.time, "sleep"):
            with self.assertRaises(SystemExit):
                watch.api("/x")
        self.assertEqual(len(calls), watch.API_ATTEMPTS)


if __name__ == "__main__":
    unittest.main()

"""Run with: python3 -m unittest discover tests"""

import contextlib
import io
import os
import sys
import unittest
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "visualizer"))

import mock_hardware  # noqa: E402

sys.modules["board"] = mock_hardware
sys.modules["neopixel"] = mock_hardware

from core import config, mix, scale  # noqa: E402
from core.matrix import _build_map  # noqa: E402
import main  # noqa: E402


def at(hhmm):
    hours, minutes = map(int, hhmm.split(":"))
    return datetime(2026, 1, 1, hours, minutes)


SCHEDULED = {
    "mode_settings": {"led-sort": {"other": 1}},
    "schedule": {
        "07:00": {"mode": "clock", "brightness": 0.2},
        "19:00": {"mode": "collision"},
        "21:30": {"brightness": 0.05, "mode_settings": {"led-sort": {"speed": 0.5}}},
        "23:00": {"brightness": 0},
    },
}


class ScheduleTest(unittest.TestCase):
    def test_without_schedule_returns_config(self):
        self.assertEqual(config.active({"brightness": 0.3}), {"brightness": 0.3})

    def test_entries_stack_until_changed(self):
        active = config.active(SCHEDULED, at("21:45"))
        self.assertEqual(active["mode"], "collision")
        self.assertEqual(active["brightness"], 0.05)

    def test_wraps_around_midnight(self):
        active = config.active(SCHEDULED, at("02:00"))
        self.assertEqual(active["mode"], "collision")
        self.assertEqual(active["brightness"], 0)

    def test_entry_applies_from_its_minute(self):
        self.assertEqual(config.active(SCHEDULED, at("06:59"))["brightness"], 0)
        self.assertEqual(config.active(SCHEDULED, at("07:00"))["brightness"], 0.2)

    def test_nested_settings_merge(self):
        active = config.active(SCHEDULED, at("22:00"))
        self.assertEqual(active["mode_settings"]["led-sort"], {"speed": 0.5, "other": 1})
        self.assertNotIn("schedule", active)

    def test_does_not_modify_input(self):
        config.active(SCHEDULED, at("22:00"))
        self.assertEqual(SCHEDULED["mode_settings"]["led-sort"], {"other": 1})

    def test_warns_once_about_keys_set_in_and_outside_the_schedule(self):
        conf = {
            "brightness": 0.3,
            "display": {"rotate": 90},
            "mode_settings": {"ntfy-sh": {"topic": "a"}, "clock": {"x": 1}},
            "schedule": {"08:00": {"brightness": 1, "mode_settings": {"ntfy-sh": {"topic": "b"}}}},
        }
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            config.active(conf, at("12:00"))
            config.active(conf, at("12:00"))
        self.assertEqual(output.getvalue().count("'brightness' is set both"), 1)
        self.assertIn("'mode_settings.ntfy-sh.topic' is set both", output.getvalue())
        self.assertNotIn("display", output.getvalue())
        self.assertNotIn("clock", output.getvalue())

    def test_invalid_entries_are_ignored(self):
        conf = {"brightness": 0.2, "schedule": {"25:00": {"brightness": 1}, "x": {"brightness": 1}, "08:00": 1}}
        self.assertEqual(config.active(conf, at("12:00"))["brightness"], 0.2)

    def test_schedule_without_times_as_keys_is_ignored(self):
        conf = {"brightness": 0.2, "schedule": [{"from": "08:00", "brightness": 1}]}
        self.assertEqual(config.active(conf, at("12:00"))["brightness"], 0.2)


class UpgradeTest(unittest.TestCase):
    OLD = {
        "selected_mode": "clock",
        "brightness": 0.1,
        "modes": {"ntfy-sh": {"topic": "abc"}},
    }

    def test_old_names_still_work(self):
        active = config.active(self.OLD, at("12:00"))
        self.assertEqual(active["mode"], "clock")
        self.assertEqual(active["mode_settings"], {"ntfy-sh": {"topic": "abc"}})

    def test_upgrade_keeps_order_and_is_idempotent(self):
        upgraded = config.upgrade(self.OLD)
        self.assertEqual(list(upgraded), ["mode", "brightness", "mode_settings"])
        self.assertEqual(config.upgrade(upgraded), upgraded)

    def test_new_name_wins_over_old(self):
        self.assertEqual(config.upgrade({"selected_mode": "a", "mode": "b"}), {"mode": "b"})


class PlaylistTest(unittest.TestCase):
    MODES = ["a", "b", "c", "d"]

    def mode_at(self, conf, when):
        return config.active(conf, when)["mode"]

    def test_in_order_and_switches_on_the_hour(self):
        conf = {"mode": self.MODES, "every": "1h"}
        self.assertEqual(self.mode_at(conf, at("10:00")), self.mode_at(conf, at("10:59")))
        seq = [self.mode_at(conf, at(f"{h:02d}:00")) for h in range(8)]
        first = self.MODES.index(seq[0])
        self.assertEqual(seq, [self.MODES[(first + i) % 4] for i in range(8)])

    def test_every_is_written_with_a_unit(self):
        conf = {"mode": self.MODES, "every": "30m"}
        self.assertEqual(self.mode_at(conf, at("10:00")), self.mode_at(conf, at("10:29")))
        self.assertNotEqual(self.mode_at(conf, at("10:00")), self.mode_at(conf, at("10:30")))
        two_hours = {"mode": self.MODES, "every": "2h"}
        self.assertEqual(self.mode_at(two_hours, at("10:00")), self.mode_at(two_hours, at("11:59")))

    def test_invalid_every_uses_the_default(self):
        hourly = {"mode": self.MODES}
        for every in (30, "30", "0m", "1d", True):
            conf = {"mode": self.MODES, "every": every}
            self.assertEqual(self.mode_at(conf, at("10:30")), self.mode_at(hourly, at("10:30")))

    def test_shuffle_plays_each_once_per_round_without_repeats(self):
        conf = {"mode": self.MODES, "every": "1m", "shuffle": True}
        start = datetime(2026, 3, 1, 0, 0)
        seq = [self.mode_at(conf, start.replace(hour=m // 60, minute=m % 60)) for m in range(400)]
        self.assertTrue(all(a != b for a, b in zip(seq, seq[1:])))
        # Slots are aligned to rounds of len(MODES), find the first round boundary
        slot0 = (start.toordinal() * 1440) % 4
        offset = (4 - slot0) % 4
        for i in range(offset, 396 - 4, 4):
            self.assertEqual(sorted(seq[i:i + 4]), self.MODES)

    def test_shuffle_is_deterministic(self):
        conf = {"mode": self.MODES, "every": "30m", "shuffle": True}
        self.assertEqual(self.mode_at(conf, at("14:20")), self.mode_at(conf, at("14:00")))

    def test_schedule_switches_between_mode_and_playlist(self):
        conf = {
            "schedule": {
                "08:00": {"mode": "clock"},
                "18:00": {"mode": ["x", "y"], "every": "30m"},
            },
        }
        self.assertEqual(self.mode_at(conf, at("12:00")), "clock")
        self.assertIn(self.mode_at(conf, at("19:00")), ["x", "y"])
        self.assertIn(self.mode_at(conf, at("07:00")), ["x", "y"])

    def test_a_new_playlist_replaces_the_list_and_keeps_every_until_changed(self):
        conf = {
            "schedule": {
                "08:00": {"mode": ["a", "b", "c"], "every": "30m"},
                "18:00": {"mode": ["x", "y", "z"]},
                "21:00": {"every": "2h"},
            },
        }
        self.assertIn(self.mode_at(conf, at("19:00")), ["x", "y", "z"])
        self.assertNotEqual(self.mode_at(conf, at("19:00")), self.mode_at(conf, at("19:30")))
        self.assertEqual(self.mode_at(conf, at("22:00")), self.mode_at(conf, at("23:59")))

    def test_invalid_mode(self):
        self.assertIsNone(self.mode_at({"mode": []}, at("12:00")))
        self.assertIsNone(self.mode_at({"mode": ["a", 1]}, at("12:00")))
        self.assertIsNone(self.mode_at({"mode": {"playlist": ["a"]}}, at("12:00")))


class BrightnessTest(unittest.TestCase):
    def test_valid_and_clamped(self):
        self.assertEqual(config.brightness({"brightness": 0.5}), 0.5)
        self.assertEqual(config.brightness({"brightness": 3}), 1.0)
        self.assertEqual(config.brightness({"brightness": -1}), 0.0)

    def test_invalid_falls_back_to_default(self):
        for value in ("0.5", None, True, [1]):
            self.assertEqual(config.brightness({"brightness": value}), config.DEFAULT_BRIGHTNESS)
        self.assertEqual(config.brightness({}), config.DEFAULT_BRIGHTNESS)


class DisplayMapTest(unittest.TestCase):
    def source_xy(self, display, x, y):
        """Which canvas pixel ends up at physical (x, y)."""
        index = _build_map(display)[y * 8 + x]
        return index % 8, index // 8

    def test_no_transform_has_no_map(self):
        self.assertIsNone(_build_map({}))
        self.assertIsNone(_build_map({"rotate": 0, "flip_x": False}))

    def test_rotate_90_clockwise(self):
        # Canvas top-left ends up top-right
        self.assertEqual(self.source_xy({"rotate": 90}, 7, 0), (0, 0))
        self.assertEqual(self.source_xy({"rotate": 90}, 7, 7), (7, 0))

    def test_rotate_180(self):
        self.assertEqual(self.source_xy({"rotate": 180}, 7, 7), (0, 0))

    def test_flips(self):
        self.assertEqual(self.source_xy({"flip_x": True}, 7, 2), (0, 2))
        self.assertEqual(self.source_xy({"flip_y": True}, 2, 7), (2, 0))

    def test_maps_are_permutations(self):
        for display in ({"rotate": 90}, {"rotate": 270, "flip_x": True}, {"flip_y": True}):
            self.assertEqual(sorted(_build_map(display)), list(range(64)))

    def test_invalid_rotate_is_ignored(self):
        self.assertIsNone(_build_map({"rotate": 45}))


class UnknownModeTest(unittest.TestCase):
    def test_names_the_available_modes_once(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertIsNone(main.start("clokc"))
            self.assertIsNone(main.start("clokc"))
        self.assertEqual(output.getvalue().count("Unknown mode 'clokc'"), 1)
        self.assertIn("clock", output.getvalue())


class ColorTest(unittest.TestCase):
    def test_mix_matches_integer_average(self):
        for a in range(0, 256, 17):
            for b in range(0, 256, 13):
                self.assertEqual(mix((a, 0, 0), (b, 0, 0))[0], (a + b) // 2)

    def test_scale_clamps(self):
        self.assertEqual(scale((200, 100, 0), 2), (255, 200, 0))


if __name__ == "__main__":
    unittest.main()

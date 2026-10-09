"""Run with: python3 -m unittest discover tests"""

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
from core.matrix import _build_map, _build_gamma  # noqa: E402


def at(hhmm):
    hours, minutes = map(int, hhmm.split(":"))
    return datetime(2026, 1, 1, hours, minutes)


SCHEDULED = {
    "mode": "clock",
    "brightness": 0.2,
    "mode_settings": {"led-sort": {"speed": 0.1, "other": 1}},
    "schedule": [
        {"from": "07:00", "mode": "clock", "brightness": 0.2},
        {"from": "19:00", "mode": "collision"},
        {"from": "21:30", "brightness": 0.05, "mode_settings": {"led-sort": {"speed": 0.5}}},
        {"from": "23:00", "brightness": 0},
    ],
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
        self.assertEqual(SCHEDULED["mode_settings"]["led-sort"]["speed"], 0.1)

    def test_invalid_entries_are_ignored(self):
        conf = {"brightness": 0.2, "schedule": [{"from": "25:00", "brightness": 1}, {"brightness": 1}, "x"]}
        self.assertEqual(config.active(conf, at("12:00"))["brightness"], 0.2)


class UpgradeTest(unittest.TestCase):
    OLD = {
        "selected_mode": "clock",
        "brightness": 0.1,
        "modes": {"ntfy-sh": {"topic": "abc"}},
        "schedule": [
            {"from": "08:00", "selected_mode": "clock", "modes": {"ntfy-sh": {"topic": "abc"}}},
            {"from": "22:00", "selected_mode": "collision", "modes": {"ntfy-sh": {"topic": "x"}}},
        ],
    }

    def test_old_names_still_work(self):
        self.assertEqual(config.active(self.OLD, at("12:00"))["mode"], "clock")
        self.assertEqual(config.active(self.OLD, at("12:00"))["mode_settings"], {"ntfy-sh": {"topic": "abc"}})
        active = config.active(self.OLD, at("23:00"))
        self.assertEqual(active["mode"], "collision")
        self.assertEqual(active["mode_settings"], {"ntfy-sh": {"topic": "x"}})

    def test_upgrade_keeps_order_and_is_idempotent(self):
        upgraded = config.upgrade(self.OLD)
        self.assertEqual(list(upgraded), ["mode", "brightness", "mode_settings", "schedule"])
        self.assertEqual(config.upgrade(upgraded), upgraded)

    def test_new_name_wins_over_old(self):
        self.assertEqual(config.upgrade({"selected_mode": "a", "mode": "b"}), {"mode": "b"})


class PlaylistTest(unittest.TestCase):
    MODES = ["a", "b", "c", "d"]

    def mode_at(self, playlist, when):
        return config.active({"mode": playlist}, when)["mode"]

    def test_in_order_and_switches_on_the_hour(self):
        playlist = {"playlist": self.MODES, "every": 60}
        self.assertEqual(self.mode_at(playlist, at("10:00")), self.mode_at(playlist, at("10:59")))
        seq = [self.mode_at(playlist, at(f"{h:02d}:00")) for h in range(8)]
        first = self.MODES.index(seq[0])
        self.assertEqual(seq, [self.MODES[(first + i) % 4] for i in range(8)])

    def test_shuffle_plays_each_once_per_round_without_repeats(self):
        playlist = {"playlist": self.MODES, "every": 1, "shuffle": True}
        start = datetime(2026, 3, 1, 0, 0)
        seq = [self.mode_at(playlist, start.replace(hour=m // 60, minute=m % 60)) for m in range(400)]
        self.assertTrue(all(a != b for a, b in zip(seq, seq[1:])))
        # Slots are aligned to rounds of len(MODES), find the first round boundary
        slot0 = (start.toordinal() * 1440) % 4
        offset = (4 - slot0) % 4
        for i in range(offset, 396 - 4, 4):
            self.assertEqual(sorted(seq[i:i + 4]), self.MODES)

    def test_shuffle_is_deterministic(self):
        playlist = {"playlist": self.MODES, "every": 30, "shuffle": True}
        self.assertEqual(self.mode_at(playlist, at("14:20")), self.mode_at(playlist, at("14:00")))

    def test_schedule_switches_between_mode_and_playlist(self):
        conf = {
            "mode": "clock",
            "schedule": [
                {"from": "08:00", "mode": "clock"},
                {"from": "18:00", "mode": {"playlist": ["x", "y"], "every": 30}},
            ],
        }
        self.assertEqual(config.active(conf, at("12:00"))["mode"], "clock")
        self.assertIn(config.active(conf, at("19:00"))["mode"], ["x", "y"])
        self.assertEqual(config.active(conf, at("07:00"))["mode"] in ["x", "y"], True)

    def test_invalid_playlist(self):
        self.assertIsNone(self.mode_at({"playlist": []}, at("12:00")))
        self.assertIsNone(self.mode_at({"every": 5}, at("12:00")))
        self.assertIn(self.mode_at({"playlist": ["a"], "every": 0}, at("12:00")), ["a"])


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


class ColorTest(unittest.TestCase):
    def test_gamma_off_by_default(self):
        self.assertIsNone(_build_gamma(1))
        lut = _build_gamma(2.2)
        self.assertEqual((lut[0], lut[255]), (0, 255))

    def test_mix_matches_integer_average(self):
        for a in range(0, 256, 17):
            for b in range(0, 256, 13):
                self.assertEqual(mix((a, 0, 0), (b, 0, 0))[0], (a + b) // 2)

    def test_scale_clamps(self):
        self.assertEqual(scale((200, 100, 0), 2), (255, 200, 0))


if __name__ == "__main__":
    unittest.main()

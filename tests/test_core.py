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
    "selected_mode": "clock",
    "brightness": 0.2,
    "modes": {"led-sort": {"speed": 0.1, "other": 1}},
    "schedule": [
        {"from": "07:00", "selected_mode": "clock", "brightness": 0.2},
        {"from": "19:00", "selected_mode": "collision"},
        {"from": "21:30", "brightness": 0.05, "modes": {"led-sort": {"speed": 0.5}}},
        {"from": "23:00", "brightness": 0},
    ],
}


class ScheduleTest(unittest.TestCase):
    def test_without_schedule_returns_config(self):
        self.assertEqual(config.active({"brightness": 0.3}), {"brightness": 0.3})

    def test_entries_stack_until_changed(self):
        active = config.active(SCHEDULED, at("21:45"))
        self.assertEqual(active["selected_mode"], "collision")
        self.assertEqual(active["brightness"], 0.05)

    def test_wraps_around_midnight(self):
        active = config.active(SCHEDULED, at("02:00"))
        self.assertEqual(active["selected_mode"], "collision")
        self.assertEqual(active["brightness"], 0)

    def test_entry_applies_from_its_minute(self):
        self.assertEqual(config.active(SCHEDULED, at("06:59"))["brightness"], 0)
        self.assertEqual(config.active(SCHEDULED, at("07:00"))["brightness"], 0.2)

    def test_nested_settings_merge(self):
        active = config.active(SCHEDULED, at("22:00"))
        self.assertEqual(active["modes"]["led-sort"], {"speed": 0.5, "other": 1})
        self.assertNotIn("schedule", active)

    def test_does_not_modify_input(self):
        config.active(SCHEDULED, at("22:00"))
        self.assertEqual(SCHEDULED["modes"]["led-sort"]["speed"], 0.1)

    def test_invalid_entries_are_ignored(self):
        conf = {"brightness": 0.2, "schedule": [{"from": "25:00", "brightness": 1}, {"brightness": 1}, "x"]}
        self.assertEqual(config.active(conf, at("12:00"))["brightness"], 0.2)


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

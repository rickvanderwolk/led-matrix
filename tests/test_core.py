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


class TimesTest(unittest.TestCase):
    CONF = {
        "mode": {"07:00": "clock", "19:00": "collision"},
        "brightness": {"07:00": 0.2, "21:30": 0.05, "23:00": 0},
    }

    def test_plain_values_are_returned_as_is(self):
        self.assertEqual(config.active({"brightness": 0.3}), {"brightness": 0.3})

    def test_value_of_the_latest_time_that_passed(self):
        active = config.active(self.CONF, at("21:45"))
        self.assertEqual(active["mode"], "collision")
        self.assertEqual(active["brightness"], 0.05)

    def test_wraps_around_midnight(self):
        active = config.active(self.CONF, at("02:00"))
        self.assertEqual(active["mode"], "collision")
        self.assertEqual(active["brightness"], 0)

    def test_applies_from_its_minute(self):
        self.assertEqual(config.active(self.CONF, at("06:59"))["brightness"], 0)
        self.assertEqual(config.active(self.CONF, at("07:00"))["brightness"], 0.2)

    def test_settings_have_their_own_times(self):
        conf = {"mode": ["a", "b"], "brightness": {"07:00": 0.2, "23:00": 0}}
        self.assertIn(config.active(conf, at("23:30"))["mode"], ["a", "b"])

    def test_does_not_modify_input(self):
        config.active(self.CONF, at("22:00"))
        self.assertEqual(self.CONF["brightness"], {"07:00": 0.2, "21:30": 0.05, "23:00": 0})

    def test_invalid_times_are_ignored(self):
        conf = {"brightness": {"25:00": 1, "x": 1, "08:00": 0.4}}
        self.assertEqual(config.active(conf, at("12:00"))["brightness"], 0.4)
        self.assertNotIn("brightness", config.active({"brightness": {"x": 1}}, at("12:00")))
        self.assertEqual(config.brightness(config.active({"brightness": {"x": 1}}, at("12:00"))),
                         config.DEFAULT_BRIGHTNESS)

    def test_settings_that_are_not_objects_are_ignored(self):
        conf = {"display": [90], "mode_settings": {"ntfy-sh": "abc", "clock": {"x": 1}}}
        active = config.active(conf, at("12:00"))
        self.assertNotIn("display", active)
        self.assertEqual(active["mode_settings"], {"clock": {"x": 1}})
        self.assertEqual(conf["mode_settings"]["ntfy-sh"], "abc")
        self.assertNotIn("mode_settings", config.active({"mode_settings": [1]}, at("12:00")))


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
        return config.active(conf, when).get("mode")

    def test_in_order_and_switches_on_the_hour(self):
        conf = {"mode": self.MODES, "switch_every": "1h"}
        self.assertEqual(self.mode_at(conf, at("10:00")), self.mode_at(conf, at("10:59")))
        seq = [self.mode_at(conf, at(f"{h:02d}:00")) for h in range(8)]
        first = self.MODES.index(seq[0])
        self.assertEqual(seq, [self.MODES[(first + i) % 4] for i in range(8)])

    def test_switch_every_is_written_with_a_unit(self):
        conf = {"mode": self.MODES, "switch_every": "30m"}
        self.assertEqual(self.mode_at(conf, at("10:00")), self.mode_at(conf, at("10:29")))
        self.assertNotEqual(self.mode_at(conf, at("10:00")), self.mode_at(conf, at("10:30")))
        ten_seconds = {"mode": self.MODES, "switch_every": "10s"}
        t = datetime(2026, 3, 1, 10, 0, 0)
        self.assertEqual(self.mode_at(ten_seconds, t), self.mode_at(ten_seconds, t.replace(second=9)))
        self.assertNotEqual(self.mode_at(ten_seconds, t), self.mode_at(ten_seconds, t.replace(second=10)))
        two_hours = {"mode": self.MODES, "switch_every": "2h"}
        self.assertEqual(self.mode_at(two_hours, at("10:00")), self.mode_at(two_hours, at("11:59")))

    def test_invalid_switch_every_uses_the_default(self):
        hourly = {"mode": self.MODES}
        for every in (30, "30", "0m", "1d", True):
            conf = {"mode": self.MODES, "switch_every": every}
            self.assertEqual(self.mode_at(conf, at("10:30")), self.mode_at(hourly, at("10:30")))

    def test_shuffle_plays_each_once_per_round_without_repeats(self):
        conf = {"mode": self.MODES, "switch_every": "1m", "shuffle": True}
        start = datetime(2026, 3, 1, 0, 0)
        seq = [self.mode_at(conf, start.replace(hour=m // 60, minute=m % 60)) for m in range(400)]
        self.assertTrue(all(a != b for a, b in zip(seq, seq[1:])))
        # Slots are aligned to rounds of len(MODES), find the first round boundary
        slot0 = (start.toordinal() * 1440) % 4
        offset = (4 - slot0) % 4
        for i in range(offset, 396 - 4, 4):
            self.assertEqual(sorted(seq[i:i + 4]), self.MODES)

    def test_shuffle_is_deterministic(self):
        conf = {"mode": self.MODES, "switch_every": "30m", "shuffle": True}
        self.assertEqual(self.mode_at(conf, at("14:20")), self.mode_at(conf, at("14:00")))

    def test_mode_per_time_switches_between_a_mode_and_a_list(self):
        conf = {"mode": {"08:00": "clock", "18:00": ["x", "y"]}, "switch_every": "30m"}
        self.assertEqual(self.mode_at(conf, at("12:00")), "clock")
        self.assertIn(self.mode_at(conf, at("19:00")), ["x", "y"])
        self.assertIn(self.mode_at(conf, at("07:00")), ["x", "y"])

    def test_switch_every_per_time(self):
        conf = {
            "mode": {"08:00": ["a", "b", "c"], "18:00": ["x", "y", "z"]},
            "switch_every": {"08:00": "30m", "18:00": "2h"},
        }
        self.assertNotEqual(self.mode_at(conf, at("10:00")), self.mode_at(conf, at("10:30")))
        self.assertEqual(self.mode_at(conf, at("18:00")), self.mode_at(conf, at("19:59")))

    def test_invalid_mode(self):
        self.assertIsNone(self.mode_at({"mode": []}, at("12:00")))
        self.assertIsNone(self.mode_at({"mode": ["a", 1]}, at("12:00")))
        self.assertIsNone(self.mode_at({"mode": {"playlist": ["a"]}}, at("12:00")))


class AllModesTest(unittest.TestCase):
    def modes_in_all(self, conf):
        """Every mode "all" plays, by switching every second for a few minutes."""
        conf = dict(conf, mode="all", switch_every="1s")
        start = datetime(2026, 3, 1, 12, 0, 0)
        config._warned.clear()  # warnings show once per process
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            seen = {config.active(conf, start.replace(second=s))["mode"] for s in range(60)}
        return seen, output.getvalue()

    def test_plays_every_mode_except_ones_missing_a_required_setting(self):
        seen, log = self.modes_in_all({})
        self.assertEqual(seen, set(config.available_modes()) - {"ntfy-sh"})
        self.assertIn("Skipping ntfy-sh", log)

    def test_includes_a_mode_once_its_setting_is_there(self):
        seen, _ = self.modes_in_all({"mode_settings": {"ntfy-sh": {"topic": "abc"}}})
        self.assertIn("ntfy-sh", seen)

    def test_skip_modes(self):
        seen, _ = self.modes_in_all({"skip_modes": ["clock", "led-sort"]})
        self.assertNotIn("clock", seen)
        self.assertNotIn("led-sort", seen)
        self.assertIn("collision", seen)

    def test_all_per_time(self):
        conf = {"mode": {"07:00": "clock", "18:00": "all"}}
        self.assertEqual(config.active(conf, at("12:00"))["mode"], "clock")
        self.assertIn(config.active(conf, at("19:00"))["mode"], config.available_modes())


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

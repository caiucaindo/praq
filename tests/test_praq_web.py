import unittest
from unittest.mock import patch

from PRAQ_web import PraqApi, _Rect


class FakeService:
    def snapshot(self):
        return {"status": "Pronto", "revision": 1}


class FakeWindow:
    def __init__(self) -> None:
        self.scripts = []

    def get_current_url(self):
        return "http://127.0.0.1:42001/"

    def run_js(self, script):
        self.scripts.append(script)


class FakeNativeWindow:
    def __init__(self, maximized=False) -> None:
        self.rect = _Rect(120, 80, 880, 740)
        self.maximized = maximized
        self.minimized = False
        self.restored = None

    def is_maximized(self):
        return self.maximized

    def window_rect(self):
        return self.rect

    def minimize(self):
        self.minimized = True

    def restore_after_capture(self, rect, was_maximized):
        self.restored = (rect, was_maximized)


class CaptureGeometryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = PraqApi(FakeService())
        self.api._window = FakeWindow()
        self.api._native_window = FakeNativeWindow()

    @patch("PRAQ_web.time.sleep")
    def test_rejected_capture_restores_original_geometry(self, _sleep) -> None:
        result = self.api._capture_job(lambda: {"accepted": False, "message": "rejected"})

        self.assertFalse(result["ok"])
        self.assertTrue(self.api._native_window.minimized)
        rect, was_maximized = self.api._native_window.restored
        self.assertIs(rect, self.api._native_window.rect)
        self.assertFalse(was_maximized)

    @patch("PRAQ_web.time.sleep")
    def test_accepted_capture_restores_geometry_on_analysis_event(self, _sleep) -> None:
        result = self.api._capture_job(lambda: {"accepted": True})

        self.assertTrue(result["ok"])
        self.assertIsNone(self.api._native_window.restored)
        self.api._dispatch_event(
            {
                "type": "state",
                "message": "Analisando texto...",
                "state": self.api._service.snapshot(),
            }
        )

        rect, was_maximized = self.api._native_window.restored
        self.assertIs(rect, self.api._native_window.rect)
        self.assertFalse(was_maximized)

    @patch("PRAQ_web.time.sleep")
    def test_maximized_capture_restores_maximized_state(self, _sleep) -> None:
        self.api._native_window = FakeNativeWindow(maximized=True)

        self.api._capture_job(lambda: {"accepted": False, "message": "rejected"})

        rect, was_maximized = self.api._native_window.restored
        self.assertIs(rect, self.api._native_window.rect)
        self.assertTrue(was_maximized)

    @patch("PRAQ_web.pyperclip.paste", return_value="  gsk_test_key  ")
    def test_read_clipboard_uses_native_clipboard(self, paste) -> None:
        result = self.api.read_clipboard()

        self.assertTrue(result["ok"])
        self.assertEqual(result["value"], "  gsk_test_key  ")
        paste.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()

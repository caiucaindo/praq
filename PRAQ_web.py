import ctypes
import json
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import webview
import pyperclip

from app_service import ApplicationService


ALLOWED_EXTERNAL_URLS = {
    "https://aistudio.google.com/app/apikey",
    "https://console.groq.com/keys",
}

GWL_STYLE = -16
HTCLIENT = 1
HTCAPTION = 2
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17
SW_MINIMIZE = 6
SW_RESTORE = 9
SW_MAXIMIZE = 3
WM_CLOSE = 0x0010
WM_NCHITTEST = 0x0084
WM_NCCALCSIZE = 0x0083
WM_NCDESTROY = 0x0082
WM_GETMINMAXINFO = 0x0024
WS_CAPTION = 0x00C00000
WS_MAXIMIZEBOX = 0x00010000
WS_MINIMIZEBOX = 0x00020000
WS_THICKFRAME = 0x00040000
WS_SYSMENU = 0x00080000
TITLEBAR_HEIGHT = 46
WINDOW_CONTROLS_WIDTH = 126
MIN_WINDOW_WIDTH = 640
MIN_WINDOW_HEIGHT = 598
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_BORDER_COLOR = 34


class _Rect(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class _Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class _MonitorInfo(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_ulong),
        ("monitor", _Rect),
        ("work", _Rect),
        ("flags", ctypes.c_ulong),
    ]


class _MinMaxInfo(ctypes.Structure):
    _fields_ = [
        ("reserved", _Point),
        ("max_size", _Point),
        ("max_position", _Point),
        ("min_track_size", _Point),
        ("max_track_size", _Point),
    ]


class _NcCalcSizeParams(ctypes.Structure):
    _fields_ = [("rects", _Rect * 3)]


class WindowsFramelessController:
    def __init__(self) -> None:
        self._hwnd = 0
        self._old_wndproc = 0
        self._wndproc_callback = None

    def attach(self, native_window: Any) -> None:
        hwnd = int(native_window.Handle.ToInt64())
        if self._hwnd:
            if self._hwnd == hwnd:
                self._apply_frameless_style()
            return
        self._hwnd = hwnd
        user32 = ctypes.windll.user32
        user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.GetWindowLongPtrW.argtypes = [ctypes.c_void_p, ctypes.c_int]
        user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
        user32.SetWindowLongPtrW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_ssize_t,
        ]
        user32.CallWindowProcW.restype = ctypes.c_ssize_t
        user32.CallWindowProcW.argtypes = [
            ctypes.c_ssize_t,
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_ssize_t,
        ]
        user32.SetWindowPos.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint,
        ]
        user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
        user32.PostMessageW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_ssize_t,
        ]
        user32.SendMessageW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_ssize_t,
        ]
        user32.SendMessageW.restype = ctypes.c_ssize_t
        user32.IsZoomed.argtypes = [ctypes.c_void_p]
        user32.GetWindowRect.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_Rect),
        ]
        user32.GetDpiForWindow.argtypes = [ctypes.c_void_p]
        user32.MonitorFromWindow.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        user32.MonitorFromWindow.restype = ctypes.c_void_p
        user32.GetMonitorInfoW.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_MonitorInfo),
        ]

        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_ssize_t,
        )
        self._wndproc_callback = callback_type(self._wndproc)
        self._old_wndproc = user32.SetWindowLongPtrW(
            self._hwnd,
            -4,
            ctypes.cast(self._wndproc_callback, ctypes.c_void_p).value,
        )
        self._apply_frameless_style()

    def _apply_frameless_style(self) -> None:
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongPtrW(self._hwnd, GWL_STYLE)
        style &= ~WS_CAPTION
        style |= WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU
        user32.SetWindowLongPtrW(self._hwnd, GWL_STYLE, style)
        dwmapi = ctypes.windll.dwmapi
        dwmapi.DwmSetWindowAttribute.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_uint,
        ]
        dark_mode = ctypes.c_int(1)
        border_color = ctypes.c_uint32(0x002B2521)
        dwmapi.DwmSetWindowAttribute(
            self._hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(dark_mode),
            ctypes.sizeof(dark_mode),
        )
        dwmapi.DwmSetWindowAttribute(
            self._hwnd,
            DWMWA_BORDER_COLOR,
            ctypes.byref(border_color),
            ctypes.sizeof(border_color),
        )
        user32.SetWindowPos(
            self._hwnd,
            None,
            0,
            0,
            0,
            0,
            0x0027,
        )

    def minimize(self) -> None:
        if self._hwnd:
            ctypes.windll.user32.ShowWindow(self._hwnd, SW_MINIMIZE)

    def toggle_maximize(self) -> None:
        if not self._hwnd:
            return
        if self.is_maximized():
            self.restore()
        else:
            self.maximize()

    def maximize(self) -> None:
        if not self._hwnd:
            return
        ctypes.windll.user32.ShowWindow(self._hwnd, SW_MAXIMIZE)

    def restore(self) -> None:
        if not self._hwnd:
            return
        ctypes.windll.user32.ShowWindow(self._hwnd, SW_RESTORE)

    def close(self) -> None:
        if self._hwnd:
            ctypes.windll.user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)

    def start_drag(self) -> None:
        if not self._hwnd or not ctypes.windll.user32.GetAsyncKeyState(1) & 0x8000:
            return
        user32 = ctypes.windll.user32
        cursor = _Point()
        window_rect = _Rect()
        if not user32.GetCursorPos(ctypes.byref(cursor)):
            return
        if not user32.GetWindowRect(self._hwnd, ctypes.byref(window_rect)):
            return
        if self.is_maximized():
            maximized_rect = window_rect
            self.restore()
            if not user32.GetWindowRect(self._hwnd, ctypes.byref(window_rect)):
                return
            width = window_rect.right - window_rect.left
            height = window_rect.bottom - window_rect.top
            ratio = (cursor.x - maximized_rect.left) / max(
                1,
                maximized_rect.right - maximized_rect.left,
            )
            window_rect.left = round(cursor.x - width * ratio)
            window_rect.top = cursor.y - round(
                22 * user32.GetDpiForWindow(self._hwnd) / 96
            )
            window_rect.right = window_rect.left + width
            window_rect.bottom = window_rect.top + height
            user32.SetWindowPos(
                self._hwnd,
                None,
                window_rect.left,
                window_rect.top,
                width,
                height,
                0x0014,
            )
        origin = _Point(cursor.x, cursor.y)
        origin_rect = _Rect(
            window_rect.left,
            window_rect.top,
            window_rect.right,
            window_rect.bottom,
        )

        def move_window() -> None:
            try:
                while self._hwnd and user32.GetAsyncKeyState(1) & 0x8000:
                    current = _Point()
                    if user32.GetCursorPos(ctypes.byref(current)):
                        user32.SetWindowPos(
                            self._hwnd,
                            None,
                            origin_rect.left + current.x - origin.x,
                            origin_rect.top + current.y - origin.y,
                            0,
                            0,
                            0x0015,
                        )
                    time.sleep(0.008)
            finally:
                pass

        threading.Thread(target=move_window, daemon=True).start()

    def detach(self) -> None:
        if not self._hwnd or not self._old_wndproc:
            return
        ctypes.windll.user32.SetWindowLongPtrW(
            self._hwnd,
            -4,
            self._old_wndproc,
        )
        self._hwnd = 0
        self._old_wndproc = 0
        self._wndproc_callback = None

    def is_maximized(self) -> bool:
        return bool(self._hwnd and ctypes.windll.user32.IsZoomed(self._hwnd))

    def window_rect(self) -> _Rect | None:
        if not self._hwnd:
            return None
        rect = _Rect()
        if ctypes.windll.user32.GetWindowRect(self._hwnd, ctypes.byref(rect)):
            return rect
        return None

    def restore_after_capture(
        self,
        rect: _Rect | None,
        was_maximized: bool,
    ) -> None:
        if was_maximized:
            self.maximize()
            return
        if not self._hwnd:
            return
        user32 = ctypes.windll.user32
        user32.ShowWindow(self._hwnd, SW_RESTORE)
        if rect is not None:
            user32.SetWindowPos(
                self._hwnd,
                None,
                rect.left,
                rect.top,
                rect.right - rect.left,
                rect.bottom - rect.top,
                0x0044,
            )

    def _wndproc(self, hwnd: int, message: int, wparam: int, lparam: int) -> int:
        user32 = ctypes.windll.user32
        if message == WM_NCCALCSIZE and wparam:
            if lparam:
                params = ctypes.cast(
                    lparam,
                    ctypes.POINTER(_NcCalcSizeParams),
                ).contents
                dpi = user32.GetDpiForWindow(hwnd)
                border = max(6, round(7 * dpi / 96))
                client = params.rects[0]
                client.left += border
                client.right -= border
                client.top += max(1, round(dpi / 96))
                client.bottom -= border
            return 0
        if message == WM_GETMINMAXINFO:
            monitor = user32.MonitorFromWindow(hwnd, 2)
            if monitor:
                monitor_info = _MonitorInfo()
                monitor_info.size = ctypes.sizeof(_MonitorInfo)
                if user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
                    info = ctypes.cast(
                        lparam,
                        ctypes.POINTER(_MinMaxInfo),
                    ).contents
                    work = monitor_info.work
                    screen = monitor_info.monitor
                    info.max_position.x = work.left - screen.left
                    info.max_position.y = work.top - screen.top
                    info.max_size.x = work.right - work.left
                    info.max_size.y = work.bottom - work.top
                    dpi = user32.GetDpiForWindow(hwnd)
                    info.min_track_size.x = round(MIN_WINDOW_WIDTH * dpi / 96)
                    info.min_track_size.y = round(MIN_WINDOW_HEIGHT * dpi / 96)
                    return 0
        if message == WM_NCDESTROY and self._old_wndproc:
            old_wndproc = self._old_wndproc
            user32.SetWindowLongPtrW(hwnd, -4, old_wndproc)
            self._hwnd = 0
            self._old_wndproc = 0
            return user32.CallWindowProcW(
                old_wndproc,
                hwnd,
                message,
                wparam,
                lparam,
            )
        if message == WM_NCHITTEST:
            window_rect = _Rect()
            if user32.GetWindowRect(hwnd, ctypes.byref(window_rect)):
                x = ctypes.c_short(lparam & 0xFFFF).value
                y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
                dpi = user32.GetDpiForWindow(hwnd)
                titlebar_height = round(TITLEBAR_HEIGHT * dpi / 96)
                controls_width = round(WINDOW_CONTROLS_WIDTH * dpi / 96)
                if not self.is_maximized():
                    border = max(6, round(7 * dpi / 96))
                    left = x < window_rect.left + border
                    right = x >= window_rect.right - border
                    top = y < window_rect.top + border
                    bottom = y >= window_rect.bottom - border
                    if top and left:
                        return HTTOPLEFT
                    if top and right:
                        return HTTOPRIGHT
                    if bottom and left:
                        return HTBOTTOMLEFT
                    if bottom and right:
                        return HTBOTTOMRIGHT
                    if left:
                        return HTLEFT
                    if right:
                        return HTRIGHT
                    if top:
                        return HTTOP
                    if bottom:
                        return HTBOTTOM
                in_titlebar = y < window_rect.top + titlebar_height
                in_drag_band = x < window_rect.right - controls_width
                if in_titlebar and in_drag_band:
                    return HTCAPTION
        if self._old_wndproc:
            return user32.CallWindowProcW(
                self._old_wndproc,
                hwnd,
                message,
                wparam,
                lparam,
            )
        return HTCLIENT


def resource_path(*parts: str) -> Path:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_dir.joinpath(*parts)


class PraqApi:
    def __init__(self, service: ApplicationService) -> None:
        self._service = service
        self._window: webview.Window | None = None
        self._trusted_origin = ""
        self._trusted_url = ""
        self._capture_lock = threading.Lock()
        self._capture_window_hidden = False
        self._capture_was_maximized = False
        self._capture_window_rect: _Rect | None = None
        self._native_window = WindowsFramelessController()

    def _bind_window(self, window: webview.Window) -> None:
        self._window = window

    def _on_loaded(self) -> None:
        window = self._window
        if window is None:
            return
        current_url = window.get_current_url() or ""
        if not self._is_trusted_url(current_url):
            if not self._trusted_url:
                window.destroy()
                return
            window.load_url(self._trusted_url)
            return
        if window.native is not None:
            self._native_window.attach(window.native)
        self._service.set_event_sink(self._dispatch_event)

    def _on_closing(self) -> None:
        self._native_window.detach()

    def initialize(self) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        window = self._window
        if window is not None and window.native is not None:
            self._native_window.attach(window.native)
        self._service.initialize()
        self._service.start_hotkeys()
        return self._success(self._service.snapshot())

    def read_clipboard(self) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        try:
            return {"ok": True, "value": pyperclip.paste()}
        except Exception as exception:
            return {"ok": False, "message": f"Não foi possível acessar a área de transferência: {exception}"}

    def set_provider(self, provider: str) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        self._service.set_provider(provider)
        return self._success(self._service.snapshot())

    def set_model(self, model: str) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        self._service.set_model(model)
        return self._success(self._service.snapshot())

    def analyze_selected_text(self) -> dict[str, Any]:
        return self._capture_job(self._service.analyze_selected_text)

    def capture_single(self) -> dict[str, Any]:
        return self._capture_job(self._service.capture_single)

    def capture_scroll(self) -> dict[str, Any]:
        return self._capture_job(self._service.capture_scroll)

    def save_keys(self, gemini_key: str = "", groq_key: str = "") -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        state = self._service.save_keys(gemini_key, groq_key)
        if state["status"] != "Chaves salvas com proteção local.":
            return self._failure(state, state["status"])
        return self._success(state)

    def clear_keys(self) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        state = self._service.clear_keys()
        if state["status"] != "Chaves removidas do cofre local.":
            return self._failure(state, state["status"])
        return self._success(state)

    def clear_key(self, provider: str) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        return self._success(self._service.clear_key(provider))

    def history_prev(self) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        return self._success(self._service.history_prev())

    def history_next(self) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        return self._success(self._service.history_next())

    def history_delete(self) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        return self._success(self._service.history_delete())

    def open_external(self, url: str) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        if url not in ALLOWED_EXTERNAL_URLS:
            return self._failure(
                self._service.snapshot(),
                "Este endereço externo não é permitido.",
            )
        if not webbrowser.open(url, new=2):
            return self._failure(
                self._service.snapshot(),
                "Não foi possível abrir o navegador.",
            )
        return self._success(self._service.snapshot())

    def window_minimize(self) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        self._native_window.minimize()
        return self._success(self._service.snapshot())

    def window_toggle_maximize(self) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        self._native_window.toggle_maximize()
        return self._success(self._service.snapshot())

    def window_close(self) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        threading.Timer(0.05, self._native_window.close).start()
        return self._success(self._service.snapshot())

    def window_start_drag(self) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        self._native_window.start_drag()
        return self._success(self._service.snapshot())

    def _stop(self) -> None:
        self._service.set_event_sink(None)
        self._service.stop()

    def _capture_job(self, operation: Any) -> dict[str, Any]:
        denied = self._deny_untrusted()
        if denied:
            return denied
        window = self._window
        if window is None:
            return self._failure(
                self._service.snapshot(),
                "A janela da aplicação não está disponível.",
            )
        with self._capture_lock:
            if self._capture_window_hidden:
                return self._failure(
                    self._service.snapshot(),
                    "Uma captura já está sendo iniciada.",
                )
            self._capture_window_hidden = True
            self._capture_was_maximized = self._native_window.is_maximized()
            self._capture_window_rect = self._native_window.window_rect()
        try:
            self._native_window.minimize()
            time.sleep(0.2)
            result = operation()
        except Exception as exception:
            self._restore_after_capture()
            return self._failure(
                self._service.snapshot(),
                f"Não foi possível iniciar a captura: {exception}",
            )
        if not result.get("accepted"):
            self._restore_after_capture()
        return self._job_envelope(result)

    def _job_envelope(self, result: dict[str, Any]) -> dict[str, Any]:
        state = self._service.snapshot()
        if result.get("accepted"):
            return self._success(state)
        return self._failure(
            state,
            result.get("message") or state["status"],
        )

    def _dispatch_event(self, event: dict[str, Any]) -> None:
        message = event.get("message", "")
        job_error = event.get("type") == "error" and bool(event.get("jobId"))
        if job_error or message.startswith(("Analisando", "Enviando")):
            self._restore_after_capture()
        window = self._window
        if window is None:
            return
        payload = json.dumps(event, ensure_ascii=False).replace("</", "<\\/")
        script = (
            "window.dispatchEvent(new CustomEvent('praq:event', "
            f"{{ detail: {payload} }}));"
        )
        try:
            window.run_js(script)
        except Exception:
            pass

    def _restore_after_capture(self) -> None:
        with self._capture_lock:
            if not self._capture_window_hidden:
                return
            self._capture_window_hidden = False
            was_maximized = self._capture_was_maximized
            self._capture_was_maximized = False
            window_rect = self._capture_window_rect
            self._capture_window_rect = None
        self._native_window.restore_after_capture(window_rect, was_maximized)

    def _deny_untrusted(self) -> dict[str, Any] | None:
        window = self._window
        if window is None:
            return self._failure(
                self._service.snapshot(),
                "A interface ainda não está pronta.",
            )
        current_url = window.get_current_url() or ""
        if self._is_trusted_url(current_url):
            return None
        return self._failure(
            self._service.snapshot(),
            "A operação foi bloqueada por segurança.",
        )

    def _is_trusted_url(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if not self._trusted_origin:
            if parsed.scheme != "http" or parsed.hostname not in {
                "127.0.0.1",
                "localhost",
            }:
                return False
            self._trusted_origin = origin
            self._trusted_url = url
        return origin == self._trusted_origin

    @staticmethod
    def _success(state: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "state": state}

    @staticmethod
    def _failure(state: dict[str, Any], message: str) -> dict[str, Any]:
        return {"ok": False, "state": state, "message": message}


def main() -> None:
    frontend = resource_path("frontend", "dist", "index.html")
    if not frontend.exists():
        raise FileNotFoundError(
            "Frontend não compilado. Execute `npm run build` em `frontend`."
        )

    service = ApplicationService(resource_path())
    api = PraqApi(service)
    window = webview.create_window(
        "PRAQ",
        str(frontend),
        js_api=api,
        width=760,
        height=660,
        min_size=(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT),
        background_color="#21252b",
        text_select=False,
        frameless=True,
        easy_drag=False,
    )
    api._bind_window(window)
    window.events.loaded += api._on_loaded
    window.events.closing += api._on_closing
    window.events.closed += api._stop
    try:
        webview.start(gui="edgechromium", debug=False, http_server=True)
    finally:
        api._stop()


if __name__ == "__main__":
    main()

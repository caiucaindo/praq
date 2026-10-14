"""UI-independent application service for PRAQ.

The service owns application state, global hotkeys, in-memory screen captures,
AI jobs, and serializable frontend events. It deliberately has no Qt imports so
it can be exposed directly to a future pywebview frontend.
"""

from __future__ import annotations

import contextlib
import ctypes
import os
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, TypeAlias

import keyboard
import pyautogui
import pyperclip
from google import genai
from google.genai import types as gemini_types
from groq import Groq
from PIL import Image

from core import (
    IMAGE_PROMPT,
    TEXT_PROMPT_TEMPLATE,
    Config,
    SecretStore,
    carregar_configuracao,
)


Provider: TypeAlias = Literal["gemini", "groq"]
Event: TypeAlias = dict[str, Any]
EventSink: TypeAlias = Callable[[Event], None]
JobResult: TypeAlias = dict[str, Any]

MAX_HISTORY = 10
REQUEST_TIMEOUT_SECONDS = 60
GMEM_MOVEABLE_ZEROINIT = 0x0042


class ServiceOperationError(Exception):
    """Represent an expected operation failure safe to show to the user.

    Example:
        >>> str(ServiceOperationError("Falha"))
        'Falha'
    """


@dataclass(frozen=True, slots=True)
class _JobContext:
    """Hold immutable values captured when an AI job starts.

    Attributes:
        job_id: UUID string identifying the job.
        provider: Provider selected when the job was accepted.
        model: Model selected when the job was accepted.
        api_key: Secret copied for this job and never emitted.

    Example:
        ``_JobContext("id", "groq", "model", "secret")`` creates context.
    """

    job_id: str
    provider: Provider
    model: str
    api_key: str


class ApplicationService:
    """Coordinate PRAQ operations without depending on a UI framework.

    Args:
        base_dir: Directory containing ``config.json``. Defaults to this
            module's directory.

    Example:
        >>> service = ApplicationService()
        >>> service.snapshot()["provider"]
        'groq'
        >>> service.stop()["busy"]
        False
    """

    def __init__(self, base_dir: str | os.PathLike[str] | None = None) -> None:
        """Initialize state used by serialized daemon background jobs.

        Args:
            base_dir: Directory containing the model configuration.

        Example:
            >>> service = ApplicationService(".")
            >>> service.snapshot()["selectedModel"]
            ''
            >>> service.stop()["busy"]
            False
        """
        self._base_dir = Path(base_dir or Path(__file__).resolve().parent)
        self._lock = threading.RLock()
        self._secret_store = SecretStore()
        self._event_sink: EventSink | None = None
        self._config: Config = {
            "gemini": {"modelos": []},
            "groq": {"modelos": []},
        }
        self._provider: Provider = "groq"
        self._selected_model = ""
        self._has_gemini_key = False
        self._has_groq_key = False
        self._gemini_key_suffix = ""
        self._groq_key_suffix = ""
        self._busy = False
        self._status = "Inicializando..."
        self._revision = 0
        self._active_job_id: str | None = None
        self._history: list[str] = []
        self._history_index = -1
        self._hotkey_handles: list[Any] = []
        self._hotkeys_started = False
        self._hotkeys_starting = False
        self._initialized = False
        self._stopped = False

    def set_event_sink(self, callback: EventSink | None) -> dict[str, Any]:
        """Set the callback that receives serializable event dictionaries.

        Args:
            callback: Callable accepting one event dictionary, or ``None`` to
                detach the current sink.

        Returns:
            The current serializable state snapshot.

        Raises:
            TypeError: If callback is neither callable nor ``None``.

        Example:
            >>> service = ApplicationService()
            >>> events = []
            >>> service.set_event_sink(events.append)
            {'provider': 'groq', 'models': [], 'selectedModel': '', ...}
            >>> service.stop()["busy"]
            False
        """
        if callback is not None and not callable(callback):
            raise TypeError("O callback de eventos deve ser chamável.")

        with self._lock:
            self._event_sink = callback
            state = self._snapshot_locked()

        if callback is not None:
            self._emit({"type": "state", "state": state})
        return self.snapshot()

    def initialize(self) -> dict[str, Any]:
        """Load configuration, key availability, and the default Groq model.

        Returns:
            The initialized serializable state snapshot.

        Example:
            >>> service = ApplicationService()
            >>> state = service.initialize()
            >>> state["provider"]
            'groq'
            >>> service.stop()["busy"]
            False
        """
        with self._lock:
            if self._stopped:
                state = self._snapshot_locked()
                error = "O serviço já foi encerrado."
            else:
                try:
                    config = carregar_configuracao(self._base_dir)
                    gemini_secret = self._secret_store.get_secret("gemini")
                    groq_secret = self._secret_store.get_secret("groq")
                    has_gemini = bool(gemini_secret)
                    has_groq = bool(groq_secret)
                except Exception as exception:
                    state = self._snapshot_locked()
                    error = (
                        "Falha ao carregar a configuração: "
                        f"{exception}"
                    )
                else:
                    self._config = config
                    self._provider = "groq"
                    self._selected_model = self._first_model_locked("groq")
                    self._has_gemini_key = has_gemini
                    self._has_groq_key = has_groq
                    self._gemini_key_suffix = gemini_secret[-4:] if gemini_secret else ""
                    self._groq_key_suffix = groq_secret[-4:] if groq_secret else ""
                    self._initialized = True
                    self._status = "Modelos carregados."
                    state = self._snapshot_locked()
                    error = None

        if error is not None:
            self._emit_error(error)
        else:
            self._emit_state("Modelos carregados.")
        return self.snapshot()

    def start_hotkeys(self) -> bool:
        """Register F2, F8, and F9 global hotkeys.

        F8 and F9 callbacks verify that Gemini is active before starting work.

        Returns:
            ``True`` when hotkeys are active, otherwise ``False``.

        Example:
            ``service.start_hotkeys()`` registers the global shortcuts.
        """
        with self._lock:
            if self._stopped:
                error = "Não foi possível iniciar atalhos: serviço encerrado."
            elif self._hotkeys_started:
                return True
            elif self._hotkeys_starting:
                error = "Os atalhos globais já estão sendo iniciados."
            else:
                error = None
                self._hotkeys_starting = True

        if error is not None:
            self._emit_error(error)
            return False

        handles: list[Any] = []
        try:
            text_handle = keyboard.add_hotkey(
                "f2",
                self.analyze_selected_text,
            )
            handles.append(text_handle)
            handles.append(keyboard.add_hotkey("f8", self._hotkey_single))
            handles.append(keyboard.add_hotkey("f9", self._hotkey_scroll))
        except Exception as exception:
            with self._lock:
                self._hotkeys_starting = False
            self._remove_hotkeys(handles)
            self._emit_error(f"Erro ao iniciar atalhos globais: {exception}")
            return False

        with self._lock:
            self._hotkeys_starting = False
            if self._stopped:
                should_remove = True
            else:
                self._hotkey_handles = handles
                self._hotkeys_started = True
                should_remove = False

        if should_remove:
            self._remove_hotkeys(handles)
            return False

        self._emit_state("Atalhos globais iniciados.")
        return True

    def stop(self) -> dict[str, Any]:
        """Stop hotkeys and request non-blocking best-effort shutdown.

        Running third-party API calls cannot be forcefully interrupted, so this
        method detaches their state and returns without waiting indefinitely.

        Returns:
            A final snapshot with ``busy`` set to ``False``.

        Example:
            >>> service = ApplicationService()
            >>> service.stop()["busy"]
            False
        """
        with self._lock:
            if self._stopped:
                return self._snapshot_locked()
            self._stopped = True
            handles = self._hotkey_handles.copy()
            self._hotkey_handles.clear()
            self._hotkeys_started = False
            self._hotkeys_starting = False
            self._busy = False
            self._status = "Serviço encerrado."
            self._revision += 1
            self._active_job_id = None
            state = self._snapshot_locked()

        self._remove_hotkeys(handles)
        self._emit(
            {
                "type": "state",
                "message": "Serviço encerrado.",
                "state": state,
            }
        )
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable copy of frontend state.

        Returns:
            State containing provider, models, selected model, key-presence
            booleans, busy flag, history, and history index.

        Example:
            >>> service = ApplicationService()
            >>> isinstance(service.snapshot()["history"], list)
            True
            >>> service.stop()["busy"]
            False
        """
        with self._lock:
            return self._snapshot_locked()

    def set_provider(self, provider: str) -> dict[str, Any]:
        """Select Gemini or Groq and reset selection to its first model.

        Args:
            provider: Case-insensitive provider name.

        Returns:
            The resulting state snapshot.

        Example:
            >>> service = ApplicationService()
            >>> service.set_provider("Gemini")["provider"]
            'gemini'
            >>> service.stop()["busy"]
            False
        """
        normalized = (
            provider.strip().lower() if isinstance(provider, str) else ""
        )
        if normalized not in ("gemini", "groq"):
            self._emit_error("Provider inválido. Use Gemini ou Groq.")
            return self.snapshot()

        selected_provider: Provider = normalized
        with self._lock:
            if self._stopped:
                state = self._snapshot_locked()
                error = "Não é possível alterar o provider após encerrar."
            else:
                self._provider = selected_provider
                self._selected_model = self._first_model_locked(
                    selected_provider
                )
                state = self._snapshot_locked()
                error = None

        if error is not None:
            self._emit_error(error)
        else:
            provider_name = "Gemini" if normalized == "gemini" else "Groq"
            self._emit_state(f"Provider alterado para {provider_name}.")
        return self.snapshot()

    def set_model(self, model: str) -> dict[str, Any]:
        """Select a model from the active provider's configured list.

        Args:
            model: Exact configured model identifier.

        Returns:
            The resulting state snapshot.

        Example:
            ``service.set_model(state["models"][0])`` selects a model.
        """
        selected = model.strip() if isinstance(model, str) else ""
        with self._lock:
            models = self._models_locked(self._provider)
            if self._stopped:
                error = "Não é possível alterar o modelo após encerrar."
            elif selected not in models:
                error = "Modelo inválido para o provider selecionado."
            else:
                self._selected_model = selected
                error = None
            state = self._snapshot_locked()

        if error is not None:
            self._emit_error(error)
        else:
            self._emit_state(f"Modelo selecionado: {selected}.")
        return self.snapshot()

    def analyze_selected_text(self) -> JobResult:
        """Capture selected text and asynchronously analyze it with the AI.

        Returns:
            An acceptance dictionary containing a UUID ``jobId`` when started.

        Example:
            Calling ``service.analyze_selected_text()`` starts an F2-style job.
        """
        context = self._begin_job(
            require_gemini=False,
            message="Capturando texto selecionado...",
        )
        if context is None:
            return self._rejected_job_result()
        return self._submit_job(context, self._capture_and_analyze_text)

    def capture_single(self) -> JobResult:
        """Capture one screenshot in memory and analyze it with Gemini.

        Returns:
            An acceptance dictionary containing a UUID ``jobId`` when started.

        Example:
            ``result = service.capture_single()`` starts an F8-style job.
        """
        context = self._begin_job(
            require_gemini=True,
            message="Capturando print único...",
        )
        if context is None:
            return self._rejected_job_result()
        return self._submit_job(context, self._capture_single_and_analyze)

    def capture_scroll(self) -> JobResult:
        """Capture two in-memory screenshots around a Page Down operation.

        Returns:
            An acceptance dictionary containing a UUID ``jobId`` when started.

        Example:
            ``result = service.capture_scroll()`` starts an F9-style job.
        """
        context = self._begin_job(
            require_gemini=True,
            message="Capturando primeira parte...",
        )
        if context is None:
            return self._rejected_job_result()
        return self._submit_job(context, self._capture_scroll_and_analyze)

    def save_keys(
        self,
        gemini_key: str = "",
        groq_key: str = "",
    ) -> dict[str, Any]:
        """Validate and save non-empty API keys using DPAPI.

        Empty arguments leave existing provider keys unchanged.

        Args:
            gemini_key: New Gemini key, expected to start with ``AIza``.
            groq_key: New Groq key, expected to start with ``gsk_``.

        Returns:
            State showing only whether each key now exists.

        Example:
            ``service.save_keys(groq_key="gsk_...")`` saves a Groq key.
        """
        gemini = gemini_key.strip() if isinstance(gemini_key, str) else ""
        groq = groq_key.strip() if isinstance(groq_key, str) else ""

        errors = []
        if gemini and not self._api_key_valid("gemini", gemini):
            errors.append("Chave Gemini inválida.")
        if groq and not self._api_key_valid("groq", groq):
            errors.append("Chave Groq inválida.")
        if errors:
            self._emit_error(" ".join(errors))
            return self.snapshot()
        if not gemini and not groq:
            self._emit_error("Nenhuma nova chave informada.")
            return self.snapshot()

        with self._lock:
            if self._stopped:
                state = self._snapshot_locked()
                error = "Não é possível salvar chaves após encerrar."
            else:
                try:
                    updates = {}
                    if gemini:
                        updates["gemini"] = gemini
                    if groq:
                        updates["groq"] = groq
                    self._secret_store.set_secrets(updates)
                    self._has_gemini_key = self._secret_store.has_secret(
                        "gemini"
                    )
                    self._has_groq_key = self._secret_store.has_secret("groq")
                    if gemini:
                        self._gemini_key_suffix = gemini[-4:]
                    if groq:
                        self._groq_key_suffix = groq[-4:]
                except Exception as exception:
                    error = f"Erro ao salvar chaves: {exception}"
                else:
                    error = None
                state = self._snapshot_locked()

        if error is not None:
            self._emit_error(error)
        else:
            self._emit_state("Chaves salvas com proteção local.")
        return self.snapshot()

    def clear_keys(self) -> dict[str, Any]:
        """Remove all locally stored API keys.

        Returns:
            State with both key-presence flags cleared on success.

        Example:
            ``state = service.clear_keys()`` removes both provider keys.
        """
        with self._lock:
            if self._stopped:
                state = self._snapshot_locked()
                error = "Não é possível remover chaves após encerrar."
            else:
                try:
                    self._secret_store.clear()
                except Exception as exception:
                    error = f"Erro ao remover chaves: {exception}"
                else:
                    self._has_gemini_key = False
                    self._has_groq_key = False
                    self._gemini_key_suffix = ""
                    self._groq_key_suffix = ""
                    error = None
                state = self._snapshot_locked()

        if error is not None:
            self._emit_error(error)
        else:
            self._emit_state("Chaves removidas do cofre local.")
        return self.snapshot()

    def clear_key(self, provider: str) -> dict[str, Any]:
        """Remove only the locally stored key for one provider."""
        if provider not in {"gemini", "groq"}:
            self._emit_error("Provedor inválido.")
            return self.snapshot()

        with self._lock:
            if self._stopped:
                state = self._snapshot_locked()
                error = "Não é possível remover chaves após encerrar."
            else:
                try:
                    self._secret_store.set_secrets({provider: ""})
                    if provider == "gemini":
                        self._has_gemini_key = False
                        self._gemini_key_suffix = ""
                    else:
                        self._has_groq_key = False
                        self._groq_key_suffix = ""
                except Exception as exception:
                    error = f"Erro ao remover chave: {exception}"
                else:
                    error = None
                state = self._snapshot_locked()

        if error is not None:
            self._emit_error(error)
        else:
            self._emit_state("Chave removida do cofre local.")
        return self.snapshot()

    def history_prev(self) -> dict[str, Any]:
        """Move the history cursor to the previous response when possible.

        Returns:
            The resulting state snapshot.

        Example:
            ``state = service.history_prev()`` navigates toward older results.
        """
        with self._lock:
            if self._history_index > 0:
                self._history_index -= 1
            state = self._snapshot_locked()
        self._emit_state()
        return self.snapshot()

    def history_next(self) -> dict[str, Any]:
        """Move the history cursor to the next response when possible.

        Returns:
            The resulting state snapshot.

        Example:
            ``state = service.history_next()`` navigates toward newer results.
        """
        with self._lock:
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
            state = self._snapshot_locked()
        self._emit_state()
        return self.snapshot()

    def history_delete(self) -> dict[str, Any]:
        """Delete the response at the current history cursor.

        Returns:
            The resulting state snapshot with a normalized cursor.

        Example:
            ``state = service.history_delete()`` removes the visible result.
        """
        with self._lock:
            if self._history and self._history_index >= 0:
                self._history.pop(self._history_index)
                if not self._history:
                    self._history_index = -1
                elif self._history_index >= len(self._history):
                    self._history_index = len(self._history) - 1
            state = self._snapshot_locked()
        self._emit_state("Resposta removida do histórico.")
        return self.snapshot()

    def _hotkey_single(self) -> None:
        """Start single capture only while Gemini is selected.

        Example:
            This method is registered internally as the F8 callback.
        """
        with self._lock:
            enabled = self._provider == "gemini" and not self._stopped
        if enabled:
            self.capture_single()

    def _hotkey_scroll(self) -> None:
        """Start scroll capture only while Gemini is selected.

        Example:
            This method is registered internally as the F9 callback.
        """
        with self._lock:
            enabled = self._provider == "gemini" and not self._stopped
        if enabled:
            self.capture_scroll()

    def _begin_job(
        self,
        require_gemini: bool,
        message: str,
    ) -> _JobContext | None:
        """Validate and atomically reserve the single AI job slot.

        Args:
            require_gemini: Whether this operation requires Gemini images.
            message: Portuguese progress text included in the state event.

        Returns:
            Immutable job context when accepted, otherwise ``None``.

        Example:
            This helper is called by each public capture method.
        """
        with self._lock:
            provider = self._provider
            model = self._selected_model
            if self._stopped:
                error = "O serviço já foi encerrado."
            elif self._busy:
                error = "Já existe uma operação de IA em andamento."
            elif require_gemini and provider != "gemini":
                error = (
                    "Capturas de imagem estão disponíveis apenas no Gemini."
                )
            elif not model:
                error = "Nenhum modelo selecionado."
            else:
                api_key = self._secret_store.get_secret(provider)
                if not api_key:
                    provider_name = (
                        "Gemini" if provider == "gemini" else "Groq"
                    )
                    error = (
                        f"Configure a chave {provider_name} em configurações."
                    )
                    if provider == "gemini":
                        self._has_gemini_key = False
                    else:
                        self._has_groq_key = False
                else:
                    job_id = str(uuid.uuid4())
                    context = _JobContext(
                        job_id=job_id,
                        provider=provider,
                        model=model,
                        api_key=api_key,
                    )
                    self._busy = True
                    self._active_job_id = job_id
                    error = None

        if error is not None:
            self._emit_error(error)
            return None

        self._emit_state(message, context.job_id)
        return context

    def _submit_job(
        self,
        context: _JobContext,
        operation: Callable[[_JobContext], str],
    ) -> JobResult:
        """Submit a reserved operation to the sole background worker.

        Args:
            context: Values captured at job start.
            operation: Blocking capture and/or AI callable.

        Returns:
            A serializable acceptance result.

        Example:
            This helper is used after ``_begin_job`` succeeds.
        """
        worker = threading.Thread(
            target=self._run_job,
            args=(context, operation),
            name=f"praq-ai-{context.job_id[:8]}",
            daemon=True,
        )
        with self._lock:
            can_start = (
                not self._stopped
                and self._active_job_id == context.job_id
            )
        if not can_start:
            return {
                "accepted": False,
                "jobId": context.job_id,
                "message": "A operação foi cancelada pelo encerramento.",
            }

        try:
            worker.start()
        except RuntimeError as exception:
            self._finish_error(
                context,
                f"Não foi possível iniciar a operação: {exception}",
            )
            return {
                "accepted": False,
                "jobId": context.job_id,
                "message": "Não foi possível iniciar a operação.",
            }

        return {"accepted": True, "jobId": context.job_id}

    def _run_job(
        self,
        context: _JobContext,
        operation: Callable[[_JobContext], str],
    ) -> None:
        """Execute one job and convert all failures into frontend events.

        Args:
            context: Immutable job context.
            operation: Blocking operation to execute.

        Example:
            This method runs only inside the service executor.
        """
        try:
            answer = operation(context).strip()
            if not answer:
                raise ServiceOperationError(
                    "A API retornou uma resposta vazia."
                )
        except ServiceOperationError as exception:
            self._finish_error(context, str(exception))
        except Exception as exception:
            self._finish_error(
                context,
                f"Erro inesperado durante a operação: {exception}",
            )
        else:
            self._finish_success(context, answer)

    def _capture_and_analyze_text(self, context: _JobContext) -> str:
        """Copy selected text, restore clipboard, and invoke the chosen AI.

        Args:
            context: Immutable provider, model, and key values.

        Returns:
            AI response text.

        Raises:
            ServiceOperationError: If capture or API processing fails.

        Example:
            This operation implements F2 behavior in the worker thread.
        """
        try:
            clipboard_snapshot = self._snapshot_clipboard()
        except Exception as exception:
            raise ServiceOperationError(
                f"Erro ao acessar a área de transferência: {exception}"
            ) from exception

        capture_error: Exception | None = None
        selected_text = ""
        try:
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.2)
            selected_text = pyperclip.paste()
        except Exception as exception:
            capture_error = exception
        finally:
            try:
                self._restore_clipboard(clipboard_snapshot)
            except Exception as exception:
                if capture_error is None:
                    capture_error = exception

        if capture_error is not None:
            raise ServiceOperationError(
                f"Erro ao capturar texto: {capture_error}"
            ) from capture_error
        if not isinstance(selected_text, str) or not selected_text.strip():
            raise ServiceOperationError(
                "Nenhum texto selecionado. Selecione o texto e pressione F2."
            )
        self._emit_state("Analisando texto...", context.job_id)
        return self._analyze_text(context, selected_text)

    @staticmethod
    def _snapshot_clipboard() -> list[tuple[int, bytes]]:
        """Copy Windows clipboard formats backed by movable global memory."""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        user32.GetClipboardData.argtypes = [ctypes.c_uint]
        user32.GetClipboardData.restype = ctypes.c_void_p
        kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalSize.argtypes = [ctypes.c_void_p]
        kernel32.GlobalSize.restype = ctypes.c_size_t
        if not ApplicationService._open_clipboard():
            raise ctypes.WinError()
        snapshot: list[tuple[int, bytes]] = []
        try:
            clipboard_format = 0
            while True:
                clipboard_format = user32.EnumClipboardFormats(clipboard_format)
                if clipboard_format == 0:
                    break
                handle = user32.GetClipboardData(clipboard_format)
                if not handle:
                    continue
                size = kernel32.GlobalSize(handle)
                if not size:
                    continue
                pointer = kernel32.GlobalLock(handle)
                if not pointer:
                    continue
                try:
                    snapshot.append(
                        (clipboard_format, ctypes.string_at(pointer, size))
                    )
                finally:
                    kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()
        return snapshot

    @staticmethod
    def _restore_clipboard(snapshot: list[tuple[int, bytes]]) -> None:
        """Restore a clipboard snapshot and transfer allocated handles to Windows."""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = ctypes.c_void_p
        kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
        user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
        user32.SetClipboardData.restype = ctypes.c_void_p
        if not ApplicationService._open_clipboard():
            raise ctypes.WinError()
        try:
            if not user32.EmptyClipboard():
                raise ctypes.WinError()
            for clipboard_format, data in snapshot:
                handle = kernel32.GlobalAlloc(GMEM_MOVEABLE_ZEROINIT, len(data))
                if not handle:
                    continue
                pointer = kernel32.GlobalLock(handle)
                if not pointer:
                    kernel32.GlobalFree(handle)
                    continue
                ctypes.memmove(pointer, data, len(data))
                kernel32.GlobalUnlock(handle)
                if not user32.SetClipboardData(clipboard_format, handle):
                    kernel32.GlobalFree(handle)
        finally:
            user32.CloseClipboard()

    @staticmethod
    def _open_clipboard() -> bool:
        user32 = ctypes.windll.user32
        for _ in range(10):
            if user32.OpenClipboard(None):
                return True
            time.sleep(0.01)
        return False

    def _capture_single_and_analyze(self, context: _JobContext) -> str:
        """Take one in-memory screenshot and send it to Gemini.

        Args:
            context: Immutable Gemini model and key values.

        Returns:
            Gemini response text.

        Raises:
            ServiceOperationError: If capture or API processing fails.

        Example:
            This operation implements F8 behavior in the worker thread.
        """
        try:
            image = pyautogui.screenshot()
        except Exception as exception:
            raise ServiceOperationError(
                f"Erro ao capturar a tela: {exception}"
            ) from exception
        self._emit_state("Enviando imagem para análise...", context.job_id)
        return self._analyze_images(context, [image])

    def _capture_scroll_and_analyze(self, context: _JobContext) -> str:
        """Take two in-memory screenshots and restore the previous page.

        Args:
            context: Immutable Gemini model and key values.

        Returns:
            Gemini response text.

        Raises:
            ServiceOperationError: If capture or API processing fails.

        Example:
            This operation implements F9 behavior in the worker thread.
        """
        paged_down = False
        try:
            first_image = pyautogui.screenshot()
            pyautogui.press("pagedown")
            paged_down = True
            time.sleep(0.5)
            second_image = pyautogui.screenshot()
        except Exception as exception:
            raise ServiceOperationError(
                f"Erro ao capturar imagens com rolagem: {exception}"
            ) from exception
        finally:
            if paged_down:
                with contextlib.suppress(Exception):
                    pyautogui.press("pageup")

        self._emit_state("Enviando imagens para análise...", context.job_id)
        return self._analyze_images(context, [first_image, second_image])

    def _analyze_text(self, context: _JobContext, text: str) -> str:
        """Send text to the provider captured by a job.

        Args:
            context: Immutable provider, model, and key values.
            text: Selected question text.

        Returns:
            Provider response text.

        Raises:
            ServiceOperationError: If the provider request fails.

        Example:
            This helper preserves the original text prompt and temperature.
        """
        prompt = TEXT_PROMPT_TEMPLATE.format(texto=text)
        if context.provider == "gemini":
            client: Any = None
            try:
                client = genai.Client(
                    api_key=context.api_key,
                    http_options=gemini_types.HttpOptions(
                        timeout=REQUEST_TIMEOUT_SECONDS * 1000
                    ),
                )
                response = client.models.generate_content(
                    model=context.model,
                    contents=prompt,
                    config=gemini_types.GenerateContentConfig(
                        temperature=0.2
                    ),
                )
                return str(response.text or "")
            except Exception as exception:
                raise ServiceOperationError(
                    "Erro na API do Gemini: "
                    f"{self._safe_error_text(exception, context.api_key)}"
                ) from exception
            finally:
                self._close_client(client)

        client = None
        try:
            client = Groq(
                api_key=context.api_key,
                timeout=REQUEST_TIMEOUT_SECONDS,
                max_retries=1,
            )
            response = client.chat.completions.create(
                model=context.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return str(response.choices[0].message.content or "")
        except Exception as exception:
            raise ServiceOperationError(
                "Erro na API do Groq: "
                f"{self._safe_error_text(exception, context.api_key)}"
            ) from exception
        finally:
            self._close_client(client)

    def _analyze_images(
        self,
        context: _JobContext,
        images: list[Image.Image],
    ) -> str:
        """Send in-memory PIL images to the captured Gemini model.

        Args:
            context: Immutable Gemini model and key values.
            images: PIL images kept entirely in memory.

        Returns:
            Gemini response text.

        Raises:
            ServiceOperationError: If the Gemini request fails.

        Example:
            This helper preserves the original image prompt and temperature.
        """
        client: Any = None
        try:
            client = genai.Client(
                api_key=context.api_key,
                http_options=gemini_types.HttpOptions(
                    timeout=REQUEST_TIMEOUT_SECONDS * 1000
                ),
            )
            response = client.models.generate_content(
                model=context.model,
                contents=[IMAGE_PROMPT, *images],
                config=gemini_types.GenerateContentConfig(temperature=0.2),
            )
            return str(response.text or "")
        except Exception as exception:
            raise ServiceOperationError(
                "Erro na API do Gemini: "
                f"{self._safe_error_text(exception, context.api_key)}"
            ) from exception
        finally:
            self._close_client(client)

    def _finish_success(self, context: _JobContext, answer: str) -> None:
        """Commit a successful answer to history and emit result/state events.

        Args:
            context: Completed job context.
            answer: Non-empty provider response.

        Example:
            This helper runs after a background operation succeeds.
        """
        with self._lock:
            if self._active_job_id != context.job_id:
                return
            self._history.append(answer)
            if len(self._history) > MAX_HISTORY:
                self._history.pop(0)
            self._history_index = len(self._history) - 1
            self._busy = False
            self._active_job_id = None
            self._status = "Resposta recebida."
            self._revision += 1
            state = self._snapshot_locked()

        self._emit(
            {
                "type": "result",
                "jobId": context.job_id,
                "provider": context.provider,
                "model": context.model,
                "result": answer,
                "state": state,
            }
        )

    def _finish_error(self, context: _JobContext, message: str) -> None:
        """Release a failed job slot and emit error/state events.

        Args:
            context: Failed job context.
            message: Portuguese user-facing failure message.

        Example:
            This helper runs after a background operation fails.
        """
        with self._lock:
            if self._active_job_id != context.job_id:
                return
            self._busy = False
            self._active_job_id = None
            self._status = message
            self._revision += 1
            state = self._snapshot_locked()

        self._emit(
            {
                "type": "error",
                "jobId": context.job_id,
                "message": message,
                "state": state,
            }
        )

    def _emit_state(
        self,
        message: str | None = None,
        job_id: str | None = None,
    ) -> None:
        """Emit a state event without exposing internal mutable references.

        Args:
            message: Optional Portuguese status message.
            job_id: Optional job UUID related to the transition.

        Example:
            ``service._emit_state("Pronto.")`` notifies the frontend.
        """
        if message is not None:
            with self._lock:
                self._status = message
                self._revision += 1
                state = self._snapshot_locked()
        else:
            with self._lock:
                self._revision += 1
                state = self._snapshot_locked()
        event: Event = {"type": "state", "state": state}
        if message is not None:
            event["message"] = message
        if job_id is not None:
            event["jobId"] = job_id
        self._emit(event)

    def _emit_error(
        self,
        message: str,
        job_id: str | None = None,
    ) -> None:
        """Emit a serializable user-facing error event.

        Args:
            message: Portuguese error message.
            job_id: Optional related job UUID.

        Example:
            ``service._emit_error("Falha.")`` reports an operation error.
        """
        with self._lock:
            self._status = message
            self._revision += 1
            state = self._snapshot_locked()
        event: Event = {
            "type": "error",
            "message": message,
            "state": state,
        }
        if job_id is not None:
            event["jobId"] = job_id
        self._emit(event)

    def _emit(self, event: Event) -> None:
        """Call the current sink while isolating service state from its errors.

        Args:
            event: Fully serializable event dictionary.

        Example:
            Sink exceptions are ignored so workers remain healthy.
        """
        with self._lock:
            sink = self._event_sink
        if sink is None:
            return
        try:
            sink(event)
        except Exception:
            pass

    def _snapshot_locked(self) -> dict[str, Any]:
        """Build a state copy while the caller holds the service lock.

        Returns:
            A JSON-serializable state dictionary containing no secrets.

        Example:
            This helper is called only from lock-protected sections.
        """
        return {
            "provider": self._provider,
            "models": self._models_locked(self._provider).copy(),
            "selectedModel": self._selected_model,
            "hasGeminiKey": self._has_gemini_key,
            "hasGroqKey": self._has_groq_key,
            "geminiKeySuffix": self._gemini_key_suffix,
            "groqKeySuffix": self._groq_key_suffix,
            "busy": self._busy,
            "status": self._status,
            "revision": self._revision,
            "history": self._history.copy(),
            "historyIndex": self._history_index,
        }

    def _models_locked(self, provider: Provider) -> list[str]:
        """Return the internal configured model list for a provider.

        Args:
            provider: Provider whose models are requested.

        Returns:
            Internal model list. Callers must not mutate it.

        Example:
            This helper is used while holding the service lock.
        """
        return self._config.get(provider, {}).get("modelos", [])

    def _first_model_locked(self, provider: Provider) -> str:
        """Return the first configured provider model or an empty string.

        Args:
            provider: Provider whose default model is requested.

        Returns:
            First model identifier, or ``""`` when none exists.

        Example:
            This helper preserves the original combobox default selection.
        """
        models = self._models_locked(provider)
        return models[0] if models else ""

    def _rejected_job_result(self) -> JobResult:
        """Create the standard result returned for a rejected operation.

        Returns:
            A serializable rejection dictionary.

        Example:
            >>> ApplicationService()._rejected_job_result()["accepted"]
            False
        """
        with self._lock:
            active_job_id = self._active_job_id
        return {"accepted": False, "jobId": active_job_id}

    @staticmethod
    def _api_key_valid(provider: Provider, key: str) -> bool:
        """Validate a key using the original PRAQ prefix and length rules.

        Args:
            provider: Provider associated with the key.
            key: Trimmed API key.

        Returns:
            Whether the key matches the provider's basic format.

        Example:
            >>> ApplicationService._api_key_valid("groq", "gsk_" + "x" * 26)
            True
        """
        if provider == "gemini":
            return key.startswith("AIza") and len(key) >= 30
        return key.startswith("gsk_") and len(key) >= 30

    @staticmethod
    def _close_client(client: Any) -> None:
        """Best-effort close a third-party client when supported.

        Args:
            client: Gemini or Groq client, possibly ``None``.

        Example:
            ``ApplicationService._close_client(None)`` is a no-op.
        """
        if client is None:
            return
        close = getattr(client, "close", None)
        if callable(close):
            with contextlib.suppress(Exception):
                close()

    @staticmethod
    def _safe_error_text(exception: Exception, secret: str) -> str:
        """Render an exception while redacting the job's API key.

        Args:
            exception: Third-party exception to present to the frontend.
            secret: API key that must never occur in an emitted event.

        Returns:
            User-facing exception text with exact secret matches redacted.

        Example:
            >>> error = ValueError("key-secret")
            >>> ApplicationService._safe_error_text(error, "secret")
            'key-[SEGREDO REMOVIDO]'
        """
        message = str(exception)
        if secret:
            message = message.replace(secret, "[SEGREDO REMOVIDO]")
        return message

    @staticmethod
    def _remove_hotkeys(handles: list[Any]) -> None:
        """Best-effort remove only hotkeys registered by this service.

        Args:
            handles: Keyboard-library registration handles.

        Example:
            ``ApplicationService._remove_hotkeys([])`` is a no-op.
        """
        for handle in handles:
            with contextlib.suppress(Exception):
                keyboard.remove_hotkey(handle)

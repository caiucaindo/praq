import json
import os
import time
import base64
import ctypes
from ctypes import wintypes

import keyboard
from PySide6.QtCore import QThread, Signal
from google.genai import types as gemini_types


APP_NAME = "PRAQ"
APP_VERSION = "0.1.0"

DEFAULT_CONFIG = {
    "gemini": {
        "modelos": [
            "models/gemini-2.5-flash",
            "models/gemini-2.5-pro",
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-lite-001",
            "models/gemini-flash-latest",
            "models/gemini-pro-latest",
            "models/gemini-2.5-flash-lite",
        ]
    },
    "groq": {
        "modelos": [
            "allam-2-7b",
            "llama-3.1-8b-instant",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "openai/gpt-oss-20b",
            "qwen/qwen3-32b",
            "llama-3.3-70b-versatile",
            "moonshotai/kimi-k2-instruct-0905",
            "openai/gpt-oss-120b",
        ]
    },
}


IMAGE_PROMPT = (
    "Analise a(s) imagem(ns) desta questao de multipla escolha. "
    "Identifique o enunciado e as alternativas, e diga qual e a alternativa correta. "
    "Regra prioritaria: nao retorne motivo, alternativas (fora a correta), ou enunciado. "
    "Seja direto e explique brevemente o motivo."
)


TEXT_PROMPT_TEMPLATE = (
    "Analise o seguinte texto de uma questao de multipla escolha:\n\n"
    "{texto}\n\n"
    "Identifique o enunciado e as alternativas, e diga qual e a alternativa correta. "
    "Regra prioritaria: nao retorne motivo, alternativas (fora a correta), ou enunciado. "
    "Seja direto e explique brevemente o motivo."
)


def carregar_configuracao(base_dir):
    """Carrega modelos do config.json e aplica defaults seguros."""
    config_path = os.path.join(base_dir, "config.json")
    if not os.path.exists(config_path):
        salvar_configuracao(base_dir, DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    for provider in ("gemini", "groq"):
        provider_config = config.get(provider, {})
        modelos = provider_config.get("modelos")
        if isinstance(modelos, list) and modelos:
            merged[provider]["modelos"] = modelos

    return merged


def salvar_configuracao(base_dir, config):
    """Salva apenas configuracoes nao sensiveis."""
    config_path = os.path.join(base_dir, "config.json")
    sanitized = json.loads(json.dumps(DEFAULT_CONFIG))

    for provider in ("gemini", "groq"):
        modelos = config.get(provider, {}).get("modelos", [])
        if isinstance(modelos, list):
            sanitized[provider]["modelos"] = modelos

    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(sanitized, file, indent=2, ensure_ascii=False)


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


class SecretStore:
    """Cofre local protegido pelo Windows DPAPI para chaves de API."""

    def __init__(self):
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        self.store_dir = os.path.join(appdata, APP_NAME)
        self.store_path = os.path.join(self.store_dir, "secrets.json")

    def get_secret(self, provider):
        data = self._read_store()
        encrypted_value = data.get(provider)
        if not encrypted_value:
            return ""

        try:
            encrypted_bytes = base64.b64decode(encrypted_value)
            return self._unprotect(encrypted_bytes).decode("utf-8")
        except Exception:
            return ""

    def set_secret(self, provider, value):
        data = self._read_store()
        value = value.strip()

        if value:
            protected = self._protect(value.encode("utf-8"))
            data[provider] = base64.b64encode(protected).decode("ascii")
        else:
            data.pop(provider, None)

        self._write_store(data)

    def clear(self):
        self._write_store({})

    def has_secret(self, provider):
        return bool(self.get_secret(provider))

    def _read_store(self):
        if not os.path.exists(self.store_path):
            return {}

        try:
            with open(self.store_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_store(self, data):
        os.makedirs(self.store_dir, exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def _protect(self, raw):
        in_blob, in_buffer = self._blob_from_bytes(raw)
        out_blob = _DataBlob()
        if not ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(in_blob),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(out_blob),
        ):
            raise ctypes.WinError()

        try:
            _ = in_buffer
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    def _unprotect(self, encrypted):
        in_blob, in_buffer = self._blob_from_bytes(encrypted)
        out_blob = _DataBlob()
        if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(in_blob),
            None,
            None,
            None,
            None,
            0,
            ctypes.byref(out_blob),
        ):
            raise ctypes.WinError()

        try:
            _ = in_buffer
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    def _blob_from_bytes(self, raw):
        buffer = ctypes.create_string_buffer(raw)
        blob = _DataBlob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
        return blob, buffer


class ModelLoader(QThread):
    """Carrega os modelos da API selecionada a partir da configuracao."""

    modelos_carregados = Signal(list, str)
    erro_carregamento = Signal(str)

    def __init__(self, config, api_provider):
        super().__init__()
        self.config = config
        self.api_provider = api_provider

    def run(self):
        try:
            if self.api_provider == "gemini":
                modelos = self.config["gemini"]["modelos"]
            else:
                modelos = self.config["groq"]["modelos"]

            if modelos:
                self.modelos_carregados.emit(modelos, self.api_provider)
            else:
                self.erro_carregamento.emit(
                    f"Nenhum modelo disponivel para {self.api_provider}."
                )
        except Exception as error:
            self.erro_carregamento.emit(f"Erro ao carregar modelos: {error}")


class GeminiImageProcessor(QThread):
    """Processa imagens com Gemini em thread separada."""

    resultado_pronto = Signal(str)
    erro_processamento = Signal(str)

    def __init__(self, client, model_name, images):
        super().__init__()
        self.client = client
        self.model_name = model_name
        self.images = images

    def run(self):
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[IMAGE_PROMPT] + self.images,
                config=gemini_types.GenerateContentConfig(temperature=0.2),
            )
            self.resultado_pronto.emit(response.text)
        except Exception as error:
            self.erro_processamento.emit(f"Erro na API do Gemini: {error}")


class GeminiTextProcessor(QThread):
    """Processa texto com Gemini em thread separada."""

    resultado_pronto = Signal(str)
    erro_processamento = Signal(str)

    def __init__(self, client, model_name, text):
        super().__init__()
        self.client = client
        self.model_name = model_name
        self.text = text

    def run(self):
        try:
            prompt = TEXT_PROMPT_TEMPLATE.format(texto=self.text)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=gemini_types.GenerateContentConfig(temperature=0.2),
            )
            self.resultado_pronto.emit(response.text)
        except Exception as error:
            self.erro_processamento.emit(f"Erro na API do Gemini: {error}")


class GroqTextProcessor(QThread):
    """Processa texto com Groq em thread separada."""

    resultado_pronto = Signal(str)
    erro_processamento = Signal(str)

    def __init__(self, client, model_name, text):
        super().__init__()
        self.client = client
        self.model_name = model_name
        self.text = text

    def run(self):
        try:
            prompt = TEXT_PROMPT_TEMPLATE.format(texto=self.text)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            self.resultado_pronto.emit(response.choices[0].message.content)
        except Exception as error:
            self.erro_processamento.emit(f"Erro na API do Groq: {error}")


class HotkeyListener(QThread):
    """Escuta hotkeys globais sem travar a interface."""

    capture_text_signal = Signal()
    capture_single_signal = Signal()
    capture_scroll_signal = Signal()

    def __init__(self):
        super().__init__()
        self.keep_running = True
        self.image_hotkeys_enabled = True

    def set_image_hotkeys_enabled(self, enabled):
        self.image_hotkeys_enabled = enabled

    def run(self):
        text_hotkey = keyboard.add_hotkey("f2", self.capture_text_signal.emit)
        single_hotkey = keyboard.add_hotkey("f8", self._emit_single_if_enabled)
        scroll_hotkey = keyboard.add_hotkey("f9", self._emit_scroll_if_enabled)

        while self.keep_running:
            time.sleep(0.1)

        keyboard.remove_hotkey(text_hotkey)
        keyboard.remove_hotkey(single_hotkey)
        keyboard.remove_hotkey(scroll_hotkey)

    def _emit_single_if_enabled(self):
        if self.image_hotkeys_enabled:
            self.capture_single_signal.emit()

    def _emit_scroll_if_enabled(self):
        if self.image_hotkeys_enabled:
            self.capture_scroll_signal.emit()

    def stop(self):
        self.keep_running = False

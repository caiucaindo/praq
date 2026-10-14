import time

import keyboard
from PySide6.QtCore import QThread, Signal
from google.genai import types as gemini_types

from core import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_CONFIG,
    IMAGE_PROMPT,
    TEXT_PROMPT_TEMPLATE,
    SecretStore,
    carregar_configuracao,
    salvar_configuracao,
)


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

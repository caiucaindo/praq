import os
import sys
import time

import pyautogui
import pyperclip
from PySide6.QtWidgets import QApplication
from google import genai
from groq import Groq

from backend import (
    GeminiImageProcessor,
    GeminiTextProcessor,
    GroqTextProcessor,
    HotkeyListener,
    ModelLoader,
    SecretStore,
    carregar_configuracao,
)
from ui import ModernUI


class MainWindow(ModernUI):
    """Controlador principal: conecta UI e backend."""

    def __init__(self):
        super().__init__()

        # definir Groq como provider padrão
        self.api_provider = "groq"
        self.config = None
        self.secret_store = SecretStore()
        self.client_gemini = None
        self.client_groq = None

        self.model_loader = None
        self.text_processor = None
        self.image_processor = None
        self.hotkey_thread = None
        self.response_history = []
        self.response_history_index = -1

        self._configurar_aplicacao()

    def _configurar_aplicacao(self):
        try:
            self.config = carregar_configuracao(os.path.dirname(__file__))
            self._recriar_clientes()
        except Exception as error:
            self._desativar_interface_por_erro(f"Falha ao carregar configuracao: {error}")
            return

        self.combo_api.currentTextChanged.connect(self.mudar_api)
        self.btn_texto.clicked.connect(self.capturar_texto_selecionado)
        self.btn_print_unico.clicked.connect(self.capturar_tela_unica)
        self.btn_print_scroll.clicked.connect(self.capturar_scroll_snap)
        self.btn_settings.clicked.connect(self.abrir_configuracoes)
        self.btn_back_main.clicked.connect(self.voltar_principal)
        self.btn_save_settings.clicked.connect(self.salvar_configuracoes)
        self.btn_clear_settings.clicked.connect(self.limpar_configuracoes)
        self.btn_history_delete.clicked.connect(self.excluir_resposta_atual)
        self.btn_history_prev.clicked.connect(self.mostrar_resposta_anterior)
        self.btn_history_next.clicked.connect(self.mostrar_proxima_resposta)
        self.input_gemini_key.textEdited.connect(
            lambda: self._resetar_estado_campo_chave("gemini")
        )
        self.input_groq_key.textEdited.connect(
            lambda: self._resetar_estado_campo_chave("groq")
        )

        # ajustar UI/estado para Groq por padrão
        self.set_groq_mode(True)
        # refletir seleção no combobox (mostra Groq ao abrir)
        try:
            self.combo_api.setCurrentText("Groq")
        except Exception:
            pass

        self.iniciar_listener_hotkeys()
        self.iniciar_carregamento_modelos()
        self._atualizar_aviso_chaves()
        self._atualizar_botoes_historico()

    def _recriar_clientes(self):
        gemini_key = self.secret_store.get_secret("gemini")
        groq_key = self.secret_store.get_secret("groq")

        self.client_gemini = genai.Client(api_key=gemini_key) if gemini_key else None
        self.client_groq = Groq(api_key=groq_key) if groq_key else None

    def _atualizar_aviso_chaves(self):
        if not self.secret_store.has_secret(self.api_provider):
            api_nome = "Gemini" if self.api_provider == "gemini" else "Groq"
            self.text_resposta.setPlainText(
                f"Configure a chave da API {api_nome} em configurações para iniciar."
            )
            self._atualizar_botoes_historico()

    def _cliente_disponivel(self):
        if self.api_provider == "gemini":
            return self.client_gemini is not None
        return self.client_groq is not None

    def _desativar_interface_por_erro(self, mensagem):
        self.combo_api.setEnabled(False)
        self.combo_modelos.setEnabled(False)
        self.btn_texto.setEnabled(False)
        self.btn_print_unico.setEnabled(False)
        self.btn_print_scroll.setEnabled(False)
        self.text_resposta.setPlainText(mensagem)

    def iniciar_listener_hotkeys(self):
        self.hotkey_thread = HotkeyListener()
        self.hotkey_thread.capture_text_signal.connect(self.capturar_texto_selecionado)
        self.hotkey_thread.capture_single_signal.connect(self.capturar_tela_unica)
        self.hotkey_thread.capture_scroll_signal.connect(self.capturar_scroll_snap)
        self.hotkey_thread.set_image_hotkeys_enabled(True)
        self.hotkey_thread.start()

    def iniciar_carregamento_modelos(self):
        self.text_resposta.setPlainText("Carregando modelos...")
        self._atualizar_botoes_historico()

        self.model_loader = ModelLoader(self.config, self.api_provider)
        self.model_loader.modelos_carregados.connect(self.modelos_carregados_sucesso)
        self.model_loader.erro_carregamento.connect(self.modelos_erro_carregamento)
        self.model_loader.start()

    def mudar_api(self, selected_text):
        novo_provider = "gemini" if selected_text == "Gemini" else "groq"
        if novo_provider == self.api_provider:
            return

        self.api_provider = novo_provider
        is_groq = self.api_provider == "groq"
        self.set_groq_mode(is_groq)

        if self.hotkey_thread:
            self.hotkey_thread.set_image_hotkeys_enabled(not is_groq)

        self.combo_modelos.clear()
        self.iniciar_carregamento_modelos()
        self._atualizar_aviso_chaves()

    def modelos_carregados_sucesso(self, modelos, api_provider):
        if api_provider != self.api_provider:
            return

        self.combo_modelos.clear()
        for modelo in modelos:
            self.combo_modelos.addItem(modelo)

        api_nome = "Gemini" if api_provider == "gemini" else "Groq"
        self.text_resposta.setPlainText(f"{len(modelos)} modelo(s) de {api_nome} carregado(s).")

        if self.combo_modelos.count() > 0:
            self.combo_modelos.setCurrentIndex(0)

        self._atualizar_aviso_chaves()

    def modelos_erro_carregamento(self, erro):
        self.text_resposta.setPlainText(erro)

    def capturar_tela_unica(self):
        if self.api_provider == "groq":
            return

        self.text_resposta.setPlainText("Capturando print unico...")
        QApplication.processEvents()

        image = pyautogui.screenshot()
        self.processar_imagens(image_list=[image])

    def capturar_scroll_snap(self):
        if self.api_provider == "groq":
            return

        self.text_resposta.setPlainText("Capturando primeira parte...")
        QApplication.processEvents()
        first_image = pyautogui.screenshot()

        pyautogui.press("pagedown")
        time.sleep(0.5)

        second_image = pyautogui.screenshot()
        pyautogui.press("pageup")

        self.processar_imagens(image_list=[first_image, second_image])

    def processar_imagens(self, image_list):
        if not self._cliente_disponivel():
            self.text_resposta.setPlainText("Configure a chave Gemini em configurações.")
            self.abrir_configuracoes()
            return

        model_name = self.combo_modelos.currentText().strip()
        if not model_name:
            self.text_resposta.setPlainText("Nenhum modelo selecionado.")
            return

        self.text_resposta.setPlainText(
            f"Enviando imagens para analise com {model_name}..."
        )

        self.image_processor = GeminiImageProcessor(
            client=self.client_gemini,
            model_name=model_name,
            images=image_list,
        )
        self.image_processor.resultado_pronto.connect(self.processamento_sucesso)
        self.image_processor.erro_processamento.connect(self.processamento_erro)
        self.image_processor.start()

    def capturar_texto_selecionado(self):
        try:
            clipboard_original = pyperclip.paste()

            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.2)

            texto = pyperclip.paste()
            pyperclip.copy(clipboard_original)

            if not texto or not texto.strip():
                self.text_resposta.setPlainText(
                    "Nenhum texto selecionado. Selecione o texto e pressione F2."
                )
                return

            self.processar_texto(texto)
        except Exception as error:
            self.text_resposta.setPlainText(f"Erro ao capturar texto: {error}")

    def processar_texto(self, texto):
        if not self._cliente_disponivel():
            api_nome = "Gemini" if self.api_provider == "gemini" else "Groq"
            self.text_resposta.setPlainText(
                f"Configure a chave {api_nome} em configurações."
            )
            self.abrir_configuracoes()
            return

        model_name = self.combo_modelos.currentText().strip()
        if not model_name:
            self.text_resposta.setPlainText("Nenhum modelo selecionado.")
            return

        self.text_resposta.setPlainText(f"Analisando texto com {model_name}...")

        if self.api_provider == "gemini":
            self.text_processor = GeminiTextProcessor(
                client=self.client_gemini,
                model_name=model_name,
                text=texto,
            )
        else:
            self.text_processor = GroqTextProcessor(
                client=self.client_groq,
                model_name=model_name,
                text=texto,
            )

        self.text_processor.resultado_pronto.connect(self.processamento_sucesso)
        self.text_processor.erro_processamento.connect(self.processamento_erro)
        self.text_processor.start()

    def processamento_sucesso(self, resposta):
        self._adicionar_resposta_ao_historico(resposta)

    def processamento_erro(self, erro):
        self.text_resposta.setPlainText(erro)
        self._atualizar_botoes_historico()

    def _adicionar_resposta_ao_historico(self, resposta):
        resposta = resposta.strip()
        if not resposta:
            return

        self.response_history.append(resposta)
        if len(self.response_history) > 10:
            self.response_history.pop(0)

        self.response_history_index = len(self.response_history) - 1
        self.text_resposta.setPlainText(resposta)
        self._atualizar_botoes_historico()

    def mostrar_resposta_anterior(self):
        if self.response_history_index <= 0:
            return

        self.response_history_index -= 1
        self._mostrar_resposta_historico_atual()

    def mostrar_proxima_resposta(self):
        if self.response_history_index >= len(self.response_history) - 1:
            return

        self.response_history_index += 1
        self._mostrar_resposta_historico_atual()

    def excluir_resposta_atual(self):
        if not self.response_history or self.response_history_index < 0:
            return

        self.response_history.pop(self.response_history_index)
        if not self.response_history:
            self.response_history_index = -1
            self.text_resposta.setPlainText("Resposta removida do histórico.")
            self._atualizar_botoes_historico()
            return

        if self.response_history_index >= len(self.response_history):
            self.response_history_index = len(self.response_history) - 1

        self._mostrar_resposta_historico_atual()

    def _mostrar_resposta_historico_atual(self):
        if not self.response_history:
            return

        self.text_resposta.setPlainText(
            self.response_history[self.response_history_index]
        )
        self._atualizar_botoes_historico()

    def _atualizar_botoes_historico(self):
        has_history = bool(self.response_history)
        can_go_prev = has_history and self.response_history_index > 0
        can_go_next = (
            has_history
            and self.response_history_index < len(self.response_history) - 1
        )
        self.set_history_navigation_state(can_go_prev, can_go_next, has_history)

    def abrir_configuracoes(self):
        gemini_configurada = self.secret_store.has_secret("gemini")
        groq_configurada = self.secret_store.has_secret("groq")

        self.set_key_field_state(
            self.input_gemini_key,
            "ready" if gemini_configurada else "",
            "Chave Pronta" if gemini_configurada else "Cole a chave Gemini",
        )
        self.set_key_field_state(
            self.input_groq_key,
            "ready" if groq_configurada else "",
            "Chave Pronta" if groq_configurada else "Cole a chave Groq",
        )

        if gemini_configurada or groq_configurada:
            self.set_settings_status("", ok=True)
        else:
            self.set_settings_status("Nenhuma chave configurada ainda.", ok=False)

        self.show_settings_screen()

    def voltar_principal(self):
        self.show_main_screen()
        self._atualizar_aviso_chaves()

    def salvar_configuracoes(self):
        gemini_key = self.input_gemini_key.text().strip()
        groq_key = self.input_groq_key.text().strip()
        has_error = False

        if gemini_key:
            if not self._api_key_valida("gemini", gemini_key):
                self.set_key_field_state(
                    self.input_gemini_key,
                    "invalid",
                    "Chave invalida",
                )
                has_error = True
            else:
                self.secret_store.set_secret("gemini", gemini_key)
                self.set_key_field_state(
                    self.input_gemini_key,
                    "ready",
                    "Chave Pronta",
                )
        elif self.secret_store.has_secret("gemini"):
            self.set_key_field_state(
                self.input_gemini_key,
                "ready",
                "Chave Pronta",
            )

        if groq_key:
            if not self._api_key_valida("groq", groq_key):
                self.set_key_field_state(
                    self.input_groq_key,
                    "invalid",
                    "Chave invalida",
                )
                has_error = True
            else:
                self.secret_store.set_secret("groq", groq_key)
                self.set_key_field_state(
                    self.input_groq_key,
                    "ready",
                    "Chave Pronta",
                )
        elif self.secret_store.has_secret("groq"):
            self.set_key_field_state(
                self.input_groq_key,
                "ready",
                "Chave Pronta",
            )

        if has_error:
            self.set_settings_status("Revise os campos marcados em vermelho.", ok=False)
            self.clear_settings_input_focus()
            return

        if not gemini_key and not groq_key:
            self.set_settings_status("Nenhuma nova chave informada.", ok=False)
            self.clear_settings_input_focus()
            return

        self._recriar_clientes()
        self.set_settings_status("Chaves salvas com proteção local.", ok=True)
        self.clear_settings_input_focus()
        self.iniciar_carregamento_modelos()

    def _api_key_valida(self, provider, key):
        if provider == "gemini":
            return key.startswith("AIza") and len(key) >= 30
        return key.startswith("gsk_") and len(key) >= 30

    def _resetar_estado_campo_chave(self, provider):
        if provider == "gemini":
            self.input_gemini_key.setPlaceholderText("Cole a chave Gemini")
            self.set_key_field_visual(self.input_gemini_key, "")
        else:
            self.input_groq_key.setPlaceholderText("Cole a chave Groq")
            self.set_key_field_visual(self.input_groq_key, "")

        self.set_settings_status("", ok=False)

    def limpar_configuracoes(self):
        self.secret_store.clear()
        self._recriar_clientes()
        self.set_key_field_state(self.input_gemini_key, "", "Cole a chave Gemini")
        self.set_key_field_state(self.input_groq_key, "", "Cole a chave Groq")
        self.set_settings_status("Chaves removidas do cofre local.", ok=False)
        self.clear_settings_input_focus()
        self._atualizar_aviso_chaves()

    def closeEvent(self, event):
        if self.hotkey_thread and self.hotkey_thread.isRunning():
            self.hotkey_thread.stop()
            self.hotkey_thread.quit()
            self.hotkey_thread.wait()

        if self.model_loader and self.model_loader.isRunning():
            self.model_loader.quit()
            self.model_loader.wait()

        if self.image_processor and self.image_processor.isRunning():
            self.image_processor.quit()
            self.image_processor.wait()

        if self.text_processor and self.text_processor.isRunning():
            self.text_processor.quit()
            self.text_processor.wait()

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

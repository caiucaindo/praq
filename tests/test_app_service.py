import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_service import ApplicationService, MAX_HISTORY, _JobContext
from core import (
    DEFAULT_CONFIG,
    GEMINI_DEPRECATED_MODELS,
    GROQ_DEPRECATED_MODELS,
    carregar_configuracao,
)


class FakeSecretStore:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get_secret(self, provider: str) -> str:
        return self.values.get(provider, "")

    def has_secret(self, provider: str) -> bool:
        return bool(self.get_secret(provider))

    def set_secrets(self, values: dict[str, str]) -> None:
        for provider, value in values.items():
            if value:
                self.values[provider] = value
            else:
                self.values.pop(provider, None)

    def clear(self) -> None:
        self.values.clear()


class ApplicationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        config_path = Path(self.temp_dir.name) / "config.json"
        config_path.write_text(json.dumps(DEFAULT_CONFIG), encoding="utf-8")
        patcher = patch("app_service.SecretStore", FakeSecretStore)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.service = ApplicationService(self.temp_dir.name)

    def tearDown(self) -> None:
        self.service.stop()
        self.temp_dir.cleanup()

    def test_initialize_returns_serializable_default_state(self) -> None:
        state = self.service.initialize()

        self.assertEqual(state["provider"], "groq")
        self.assertEqual(state["selectedModel"], DEFAULT_CONFIG["groq"]["modelos"][0])
        self.assertEqual(state["historyIndex"], -1)
        self.assertIn("revision", state)
        self.assertNotIn("apiKey", state)

    def test_provider_and_model_selection_use_provider_snapshot(self) -> None:
        self.service.initialize()
        state = self.service.set_provider("gemini")
        selected = DEFAULT_CONFIG["gemini"]["modelos"][-1]
        state = self.service.set_model(selected)

        self.assertEqual(state["provider"], "gemini")
        self.assertEqual(state["selectedModel"], selected)
        self.assertIn(selected, state["models"])

    def test_save_and_clear_keys_expose_only_presence(self) -> None:
        self.service.initialize()
        groq_key = "gsk_" + "x" * 30
        state = self.service.save_keys(groq_key=groq_key)

        self.assertTrue(state["hasGroqKey"])
        self.assertEqual(state["groqKeySuffix"], "xxxx")
        self.assertNotIn(groq_key, json.dumps(state))

        state = self.service.clear_keys()
        self.assertFalse(state["hasGroqKey"])
        self.assertFalse(state["hasGeminiKey"])
        self.assertEqual(state["groqKeySuffix"], "")

    def test_clear_key_removes_only_selected_provider(self) -> None:
        self.service.initialize()
        self.service.save_keys(
            gemini_key="AIza" + "g" * 30,
            groq_key="gsk_" + "r" * 30,
        )

        state = self.service.clear_key("groq")

        self.assertFalse(state["hasGroqKey"])
        self.assertTrue(state["hasGeminiKey"])
        self.assertEqual(state["groqKeySuffix"], "")
        self.assertEqual(state["geminiKeySuffix"], "gggg")

    def test_history_keeps_latest_ten_answers(self) -> None:
        self.service.initialize()
        for index in range(MAX_HISTORY + 2):
            job_id = str(index)
            self.service._active_job_id = job_id
            self.service._busy = True
            context = _JobContext(job_id, "groq", "model", "secret")
            self.service._finish_success(context, f"answer-{index}")

        state = self.service.snapshot()
        self.assertEqual(len(state["history"]), MAX_HISTORY)
        self.assertEqual(state["history"][0], "answer-2")
        self.assertEqual(state["historyIndex"], MAX_HISTORY - 1)

        self.service.history_delete()
        self.assertEqual(len(self.service.snapshot()["history"]), MAX_HISTORY - 1)


class CoreConfigurationTests(unittest.TestCase):
    def test_invalid_provider_shape_falls_back_to_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps({"groq": {"modelos": []}, "gemini": "invalid"}),
                encoding="utf-8",
            )

            config = carregar_configuracao(temp_dir)

        self.assertEqual(config, DEFAULT_CONFIG)

    def test_deprecated_groq_models_migrate_to_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "groq": {
                            "modelos": [
                                "llama-3.1-8b-instant",
                                "openai/gpt-oss-20b",
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            config = carregar_configuracao(temp_dir)

        self.assertEqual(
            config["groq"]["modelos"], DEFAULT_CONFIG["groq"]["modelos"]
        )
        self.assertNotIn("llama-3.1-8b-instant", config["groq"]["modelos"])

    def test_default_groq_models_are_all_active(self) -> None:
        modelos = DEFAULT_CONFIG["groq"]["modelos"]

        self.assertIn("allam-2-7b", modelos)
        for modelo in modelos:
            self.assertNotIn(modelo, GROQ_DEPRECATED_MODELS)

    def test_deprecated_gemini_models_migrate_to_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "gemini": {
                            "modelos": [
                                "models/gemini-2.5-flash",
                                "models/gemini-flash-latest",
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )

            config = carregar_configuracao(temp_dir)

        self.assertEqual(
            config["gemini"]["modelos"], DEFAULT_CONFIG["gemini"]["modelos"]
        )
        self.assertNotIn(
            "models/gemini-2.5-flash", config["gemini"]["modelos"]
        )

    def test_default_gemini_models_are_all_active(self) -> None:
        modelos = DEFAULT_CONFIG["gemini"]["modelos"]

        self.assertIn("models/gemini-3.8-flash", modelos)
        for modelo in modelos:
            self.assertNotIn(modelo, GEMINI_DEPRECATED_MODELS)


if __name__ == "__main__":
    unittest.main()

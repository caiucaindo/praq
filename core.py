"""Core configuration and Windows DPAPI secret storage for PRAQ.

This module contains no Qt dependencies and can be reused by desktop
frontends. It preserves the configuration schema, prompts, and encrypted
secret format used by the original application.
"""

from __future__ import annotations

import base64
import ctypes
import json
import os
import tempfile
from ctypes import wintypes
from pathlib import Path
from typing import Any, TypeAlias


APP_NAME = "PRAQ"
APP_VERSION = "2.0.0"

DEFAULT_CONFIG = {
    "gemini": {
        "modelos": [
            "models/gemini-3.1-flash-lite",
            "models/gemini-3.5-flash-lite",
            "models/gemini-3.5-flash",
            "models/gemini-3.8-flash",
        ]
    },
    "groq": {
        "modelos": [
            "allam-2-7b",
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b",
        ]
    },
}

# Model IDs retired by Google (2.0 retired 2026-06-01; 2.5 retires
# 2026-10-20). Aliases like *-latest are also dropped because they
# silently change meaning. Sources: https://ai.google.dev/models/gemini
# and https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions
# (checked 2026-10-14).
GEMINI_DEPRECATED_MODELS = frozenset(
    {
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro",
        "models/gemini-2.5-flash-lite",
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-lite-001",
        "models/gemini-2.0-flash-lite",
        "models/gemini-flash-latest",
        "models/gemini-pro-latest",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-flash-latest",
        "gemini-pro-latest",
    }
)

# Model IDs retired by Groq (shutdown dates through 2026-09-21). Any
# config file still referencing them is migrated to the defaults above.
# Sources: https://console.groq.com/docs/models and
# https://console.groq.com/docs/deprecations (checked 2026-10-14).
GROQ_DEPRECATED_MODELS = frozenset(
    {
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen/qwen3-32b",
        "qwen/qwen3.6-27b",
        "moonshotai/kimi-k2-instruct-0905",
        "groq/compound",
        "groq/compound-mini",
    }
)

IMAGE_PROMPT = (
    "Analise a(s) imagem(ns) desta questao de multipla escolha. "
    "Identifique o enunciado e as alternativas, e diga qual e a alternativa "
    "correta. "
    "Regra prioritaria: nao retorne motivo, alternativas (fora a correta), "
    "ou enunciado. "
    "Seja direto e explique brevemente o motivo."
)

TEXT_PROMPT_TEMPLATE = (
    "Analise o seguinte texto de uma questao:\n\n"
    "{texto}\n\n"
    "Identifique e diga qual e a alternativa correta. "
    "Regra prioritaria: nao retorne enunciado ou alternativas (fora a "
    "correta). "
    "Seja direto e faça uma explicação breve [até 30 palavras] do motivo."
)

Config: TypeAlias = dict[str, dict[str, list[str]]]
PathLike: TypeAlias = str | os.PathLike[str]


def _copy_default_config() -> Config:
    """Create an independent copy of the default configuration.

    Returns:
        A deep copy containing the default provider model lists.

    Example:
        >>> copied = _copy_default_config()
        >>> copied is DEFAULT_CONFIG
        False
    """
    return json.loads(json.dumps(DEFAULT_CONFIG))


def carregar_configuracao(base_dir: PathLike) -> Config:
    """Load model configuration and merge it with safe defaults.

    Args:
        base_dir: Directory containing ``config.json``.

    Returns:
        Configuration with non-empty model lists for both providers.

    Raises:
        OSError: If an existing configuration file cannot be read.
        json.JSONDecodeError: If an existing file contains invalid JSON.

    Example:
        >>> config = carregar_configuracao(".")
        >>> "groq" in config
        True
    """
    config_path = Path(base_dir) / "config.json"
    if not config_path.exists():
        salvar_configuracao(base_dir, DEFAULT_CONFIG)
        return _copy_default_config()

    with config_path.open("r", encoding="utf-8") as file:
        loaded: Any = json.load(file)

    if not isinstance(loaded, dict):
        loaded = {}

    merged = _copy_default_config()
    for provider in ("gemini", "groq"):
        provider_config = loaded.get(provider, {})
        if not isinstance(provider_config, dict):
            continue
        modelos = provider_config.get("modelos")
        if (
            isinstance(modelos, list)
            and modelos
            and all(isinstance(modelo, str) for modelo in modelos)
        ):
            merged[provider]["modelos"] = modelos.copy()

    groq_modelos = merged["groq"]["modelos"]
    gemini_modelos = merged["gemini"]["modelos"]
    migrated = False
    if any(modelo in GROQ_DEPRECATED_MODELS for modelo in groq_modelos):
        merged["groq"]["modelos"] = _copy_default_config()["groq"][
            "modelos"
        ]
        migrated = True
    if any(modelo in GEMINI_DEPRECATED_MODELS for modelo in gemini_modelos):
        merged["gemini"]["modelos"] = _copy_default_config()["gemini"][
            "modelos"
        ]
        migrated = True
    if migrated:
        try:
            salvar_configuracao(base_dir, merged)
        except OSError:
            pass

    return merged


def salvar_configuracao(base_dir: PathLike, config: Config) -> None:
    """Save only non-sensitive model configuration.

    Args:
        base_dir: Directory in which ``config.json`` will be written.
        config: Provider model configuration to sanitize and persist.

    Raises:
        OSError: If the destination cannot be written.
        TypeError: If the supplied data cannot be JSON serialized.

    Example:
        >>> salvar_configuracao(".", DEFAULT_CONFIG)
    """
    config_path = Path(base_dir) / "config.json"
    sanitized = _copy_default_config()

    for provider in ("gemini", "groq"):
        provider_config = config.get(provider, {})
        modelos = provider_config.get("modelos", [])
        if isinstance(modelos, list):
            sanitized[provider]["modelos"] = modelos.copy()

    with config_path.open("w", encoding="utf-8") as file:
        json.dump(sanitized, file, indent=2, ensure_ascii=False)


def load_config(base_dir: PathLike) -> Config:
    """Load configuration through an English-language API alias.

    Args:
        base_dir: Directory containing ``config.json``.

    Returns:
        Merged application configuration.

    Raises:
        OSError: If an existing configuration file cannot be read.
        json.JSONDecodeError: If its JSON is invalid.

    Example:
        >>> config = load_config(".")
        >>> bool(config["gemini"]["modelos"])
        True
    """
    return carregar_configuracao(base_dir)


def save_config(base_dir: PathLike, config: Config) -> None:
    """Save configuration through an English-language API alias.

    Args:
        base_dir: Directory in which ``config.json`` will be written.
        config: Provider model configuration to persist.

    Raises:
        OSError: If the destination cannot be written.
        TypeError: If data cannot be serialized.

    Example:
        >>> save_config(".", DEFAULT_CONFIG)
    """
    salvar_configuracao(base_dir, config)


class _DataBlob(ctypes.Structure):
    """Represent the Windows ``DATA_BLOB`` structure used by DPAPI.

    Example:
        >>> blob = _DataBlob()
        >>> blob.cbData
        0
    """

    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


class SecretStore:
    """Store API keys locally using Windows DPAPI encryption.

    The encrypted JSON schema is intentionally identical to the original PRAQ
    implementation: provider names map to base64-encoded DPAPI byte strings.

    Example:
        >>> store = SecretStore()
        >>> isinstance(store.has_secret("groq"), bool)
        True
    """

    def __init__(self) -> None:
        """Initialize paths under the current user's application data folder.

        Example:
            >>> store = SecretStore()
            >>> store.store_path.endswith("secrets.json")
            True
        """
        appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
        self.store_dir = os.path.join(appdata, APP_NAME)
        self.store_path = os.path.join(self.store_dir, "secrets.json")

    def get_secret(self, provider: str) -> str:
        """Return a decrypted provider secret or an empty string on failure.

        Args:
            provider: Provider key, normally ``gemini`` or ``groq``.

        Returns:
            The decrypted API key, or ``""`` when absent or unreadable.

        Example:
            >>> isinstance(SecretStore().get_secret("groq"), str)
            True
        """
        data = self._read_store()
        encrypted_value = data.get(provider)
        if not encrypted_value or not isinstance(encrypted_value, str):
            return ""

        try:
            encrypted_bytes = base64.b64decode(encrypted_value)
            return self._unprotect(encrypted_bytes).decode("utf-8")
        except Exception:
            return ""

    def set_secret(self, provider: str, value: str) -> None:
        """Encrypt and save a secret, or remove it when empty.

        Args:
            provider: Provider key used in the encrypted JSON object.
            value: Plaintext API key. Surrounding whitespace is removed.

        Raises:
            OSError: If DPAPI or file persistence fails.

        Example:
            ``store.set_secret("groq", "gsk_...")`` saves a Groq key.
        """
        self.set_secrets({provider: value})

    def set_secrets(self, values: dict[str, str]) -> None:
        """Encrypt and persist multiple secrets in one atomic write."""
        data = self._read_store()
        updates: dict[str, str | None] = {}
        for provider, value in values.items():
            trimmed = value.strip()
            if trimmed:
                protected = self._protect(trimmed.encode("utf-8"))
                updates[provider] = base64.b64encode(protected).decode("ascii")
            else:
                updates[provider] = None

        for provider, encrypted in updates.items():
            if encrypted is None:
                data.pop(provider, None)
            else:
                data[provider] = encrypted
        self._write_store(data)

    def clear(self) -> None:
        """Remove all stored secrets while retaining the store file.

        Raises:
            OSError: If the store cannot be written.

        Example:
            ``SecretStore().clear()`` empties the local secret store.
        """
        self._write_store({})

    def has_secret(self, provider: str) -> bool:
        """Report whether a provider has a decryptable secret.

        Args:
            provider: Provider key to inspect.

        Returns:
            ``True`` only when a non-empty secret can be decrypted.

        Example:
            >>> isinstance(SecretStore().has_secret("gemini"), bool)
            True
        """
        return bool(self.get_secret(provider))

    def _read_store(self) -> dict[str, Any]:
        """Read the secret JSON object, tolerating missing or corrupt data.

        Returns:
            A parsed dictionary, or an empty dictionary on read failure.

        Example:
            >>> isinstance(SecretStore()._read_store(), dict)
            True
        """
        if not os.path.exists(self.store_path):
            return {}

        try:
            with open(self.store_path, "r", encoding="utf-8") as file:
                data: Any = json.load(file)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_store(self, data: dict[str, Any]) -> None:
        """Write the exact JSON object used by the legacy secret store.

        Args:
            data: Provider-to-base64 mapping to persist.

        Raises:
            OSError: If the directory or file cannot be written.
            TypeError: If data cannot be serialized.

        Example:
            ``store._write_store({})`` writes an empty store.
        """
        os.makedirs(self.store_dir, exist_ok=True)
        file_descriptor, temp_path = tempfile.mkstemp(
            dir=self.store_dir,
            prefix="secrets-",
            suffix=".tmp",
            text=True,
        )
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_path, self.store_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _protect(self, raw: bytes) -> bytes:
        """Encrypt bytes for the current Windows user with DPAPI.

        Args:
            raw: Plain bytes to protect.

        Returns:
            DPAPI-protected bytes.

        Raises:
            OSError: If ``CryptProtectData`` fails.

        Example:
            ``protected = store._protect(b"secret")`` encrypts bytes.
        """
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

    def _unprotect(self, encrypted: bytes) -> bytes:
        """Decrypt bytes protected for the current Windows user.

        Args:
            encrypted: DPAPI-protected bytes.

        Returns:
            Decrypted plaintext bytes.

        Raises:
            OSError: If ``CryptUnprotectData`` fails.

        Example:
            ``plain = store._unprotect(protected)`` decrypts DPAPI bytes.
        """
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

    @staticmethod
    def _blob_from_bytes(raw: bytes) -> tuple[_DataBlob, ctypes.Array[Any]]:
        """Create a ``DATA_BLOB`` while retaining its backing buffer.

        Args:
            raw: Bytes to expose to a Windows API call.

        Returns:
            A tuple containing the blob and its live backing buffer.

        Example:
            >>> blob, _ = SecretStore._blob_from_bytes(b"x")
            >>> blob.cbData
            1
        """
        buffer = ctypes.create_string_buffer(raw)
        pointer = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))
        return _DataBlob(len(raw), pointer), buffer

"""pipe.lib.providers.stt — a speech-to-text provider pipe (OpenRouter).

One atomic op: **audio bytes in → transcribed text out**. It calls OpenRouter's
dedicated transcription endpoint (``POST /api/v1/audio/transcriptions``), which
takes base64-encoded audio + a model and returns ``{text, usage}``.

This does *not* go through DSPy/LiteLLM — that path is for chat completions, not
the audio endpoint — so we make a direct HTTP call with ``httpx``. The pipe
stays pure (bytes → str); the serving layer is responsible for turning an
uploaded file into bytes and handing them here.

Key is read from ``$OPENROUTER_API_KEY`` by default and never logged or echoed.

    from pipe.lib.providers.stt import STT

    stt = STT(model="openai/whisper-large-v3")
    text = stt(open("clip.wav", "rb").read(), format="wav")   # -> str
    text = await stt.acall(audio_bytes, format="mp3")          # async
"""

from __future__ import annotations

import base64
import os
from typing import Any

from pipe.lib.providers.interface import ProviderPipe

__all__ = ["STT"]

_ENV_KEY = "OPENROUTER_API_KEY"
_ENDPOINT = "https://openrouter.ai/api/v1/audio/transcriptions"


class STT(ProviderPipe):
    """Transcribe audio to text via OpenRouter's STT endpoint.

    Args:
        model: STT model id (default ``"openai/whisper-large-v3"``; others
            include ``openai/whisper-large-v3-turbo``, ``openai/whisper-1``).
        default_format: audio container assumed when a call omits ``format``
            (e.g. ``"wav"``, ``"mp3"``, ``"webm"``, ``"mp4"``).
        language: optional ISO-639-1 hint (``"en"``, ``"hi"``, ...); OpenRouter
            auto-detects when omitted.
        api_key: OpenRouter key; defaults to ``$OPENROUTER_API_KEY``. Held only
            in memory, never logged or echoed.
        timeout: HTTP timeout in seconds (audio calls can be slow).
    """

    def __init__(
        self,
        model: str = "openai/whisper-large-v3",
        *,
        default_format: str = "wav",
        language: str | None = None,
        api_key: str | None = None,
        timeout: float = 120.0,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.model = model
        self.default_format = default_format
        self.language = language
        self.timeout = timeout
        self._api_key = api_key or os.environ.get(_ENV_KEY)

    # --- request/response helpers ----------------------------------------

    def _payload(self, audio: bytes, format: str | None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "input_audio": {
                "data": base64.b64encode(audio).decode("ascii"),
                "format": format or self.default_format,
            },
            "model": self.model,
        }
        if self.language:
            body["language"] = self.language
        return body

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            raise RuntimeError(
                f"No OpenRouter API key: set ${_ENV_KEY} or pass api_key=..."
            )
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _text_of(data: dict[str, Any]) -> str:
        text = data.get("text")
        if text is None:
            raise ValueError(f"transcription response missing 'text': keys={list(data)}")
        return text

    # --- the atomic op: audio in, text out --------------------------------

    def forward(self, audio: bytes, *, format: str | None = None) -> str:
        import httpx

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(_ENDPOINT, headers=self._headers(), json=self._payload(audio, format))
            resp.raise_for_status()
            return self._text_of(resp.json())

    async def aforward(self, audio: bytes, *, format: str | None = None) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(_ENDPOINT, headers=self._headers(), json=self._payload(audio, format))
            resp.raise_for_status()
            return self._text_of(resp.json())

    def __repr__(self) -> str:
        return (
            f"STT(model={self.model!r}, "
            f"default_format={self.default_format!r}, has_key={bool(self._api_key)})"
        )

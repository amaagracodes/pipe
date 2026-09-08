"""pipe.lib.providers.openrouter — an OpenRouter-backed provider pipe.

Wraps `OpenRouter <https://openrouter.ai>`_ as an atomic ``ProviderPipe``:
prompt in, completion out — so a model call chains like any other pipe. It
delegates to DSPy's ``LM`` (which uses LiteLLM under the hood); LiteLLM speaks
OpenRouter natively via the ``openrouter/<model>`` prefix.

DSPy is an *optional* dependency (the ``llm`` extra). This module stays
importable without it — the import happens lazily on first use, and a missing
install raises a clear, actionable error. The API key is read from the
environment by default and is never logged or echoed back.

    from pipe.lib.providers.openrouter import OpenRouterProvider

    llm = OpenRouterProvider(model="anthropic/claude-3.5-sonnet")
    llm("Summarize the doctrine of promissory estoppel.")   # -> str
    await llm.acall("...")                                    # async
"""

from __future__ import annotations

import os
from typing import Any

from pipe.lib.providers.interface import ProviderPipe

__all__ = ["OpenRouterProvider"]

_ENV_KEY = "OPENROUTER_API_KEY"


class OpenRouterProvider(ProviderPipe):
    """Call an OpenRouter-hosted model as a data-in/data-out pipe.

    Args:
        model: OpenRouter model id (e.g. ``"anthropic/claude-3.5-sonnet"``,
            ``"openai/gpt-4o-mini"``). The ``openrouter/`` prefix is added
            automatically if absent.
        api_key: OpenRouter key. Defaults to ``$OPENROUTER_API_KEY``. Held only
            in memory and passed to the client; never logged or echoed.
        temperature / max_tokens: usual generation controls.
        **lm_kwargs: forwarded to ``dspy.LM`` (e.g. ``base_url``, ``num_retries``).
    """

    def __init__(
        self,
        model: str = "openai/gpt-4o-mini",
        *,
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        name: str | None = None,
        **lm_kwargs: Any,
    ) -> None:
        super().__init__(name=name)
        self.model = model if model.startswith("openrouter/") else f"openrouter/{model}"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._lm_kwargs = lm_kwargs
        # Resolve the key once; keep it private and out of repr/logs.
        self._api_key = api_key or os.environ.get(_ENV_KEY)
        self._lm: Any | None = None  # lazily constructed dspy.LM

    # --- lazy client ------------------------------------------------------

    def _get_lm(self) -> Any:
        if self._lm is not None:
            return self._lm
        try:
            import dspy  # optional dependency (the `llm` extra)
        except ModuleNotFoundError as exc:  # pragma: no cover - import guard
            raise ModuleNotFoundError(
                "OpenRouterProvider requires DSPy. Install the optional extra: "
                "pip install 'pipe-broker[llm]'"
            ) from exc
        if not self._api_key:
            raise RuntimeError(
                f"No OpenRouter API key: set ${_ENV_KEY} or pass api_key=..."
            )
        self._lm = dspy.LM(
            self.model,
            api_key=self._api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **self._lm_kwargs,
        )
        return self._lm

    @staticmethod
    def _first_text(out: Any) -> str:
        """Normalize dspy.LM output (a list of completions) to a string."""
        if isinstance(out, str):
            return out
        if isinstance(out, (list, tuple)) and out:
            first = out[0]
            return first if isinstance(first, str) else str(first)
        return str(out)

    # --- the atomic op: prompt in, completion out -------------------------

    def forward(self, prompt: str, **options: Any) -> str:
        lm = self._get_lm()
        return self._first_text(lm(prompt, **options))

    async def aforward(self, prompt: str, **options: Any) -> str:
        lm = self._get_lm()
        acall = getattr(lm, "acall", None)
        if acall is not None:
            return self._first_text(await acall(prompt, **options))
        # Fall back to the sync path if the installed dspy lacks acall.
        return self.forward(prompt, **options)

    def __repr__(self) -> str:
        # Never include the key; show only whether one is configured.
        return (
            f"OpenRouterProvider(model={self.model!r}, "
            f"has_key={bool(self._api_key)})"
        )

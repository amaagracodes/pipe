"""Prompt-driven, provider-backed expert (Layer 2).

Implements ``Expert.apply`` once (render prompt -> call provider -> parse), so a
concrete expert is one line::

    class Summarize(AIBasedExpert[Article, Summary]):
        specification = "Summarize the article into three bullet points."

``specification`` lives here, not on Pipe. Every step below is overridable.
"""

from __future__ import annotations

import json
import re
from typing import Any, Generic, TypeVar

from pipe.lib.experts.base import Expert
from pipe.lib.providers.interface import ProviderPipe

__all__ = ["AIBasedExpert"]

I = TypeVar("I")
O = TypeVar("O")


def _is_pydantic_model(tp: Any) -> bool:
    try:
        from pydantic import BaseModel
    except ModuleNotFoundError:  # pragma: no cover
        return False
    return isinstance(tp, type) and issubclass(tp, BaseModel)


class AIBasedExpert(Expert[I, O], Generic[I, O]):
    """Subclass with a ``specification`` (and I/O types) to get a working expert."""

    specification: str = ""
    request_json: bool | None = None  # None = auto (True iff O is a pydantic model)

    def __init__(
        self,
        *,
        provider: ProviderPipe | None = None,
        specification: str | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        if specification is not None:
            self.specification = specification
        self._provider = provider
        self._default_provider: ProviderPipe | None = None

    @property
    def provider(self) -> ProviderPipe:
        if self._provider is not None:
            return self._provider
        if self._default_provider is None:
            from pipe.lib.providers.openrouter import OpenRouterProvider

            self._default_provider = OpenRouterProvider()
        return self._default_provider

    def call_provider(self, prompt: str) -> str:
        return self.provider(prompt)

    async def acall_provider(self, prompt: str) -> str:
        return await self.provider.acall(prompt)

    def _wants_json(self) -> bool:
        if self.request_json is not None:
            return self.request_json
        return _is_pydantic_model(self.__output_type__)

    def render_specification(self, data: I) -> str:
        spec = self.specification
        if "{" not in spec:
            return spec
        try:
            return spec.format(**self._input_as_mapping(data))
        except (KeyError, IndexError, ValueError):
            return spec

    def output_schema_hint(self) -> str:
        if not self._wants_json():
            return ""
        schema = self.__output_type__
        if _is_pydantic_model(schema):
            js = json.dumps(schema.model_json_schema(), indent=2)
            return (
                "Respond with a single JSON object matching this JSON Schema. "
                f"Output only JSON:\n{js}"
            )
        return "Respond with a single JSON object. Output only JSON."

    def render_input(self, data: I) -> str:
        if _is_pydantic_model(self.__input_type__) and hasattr(data, "model_dump"):
            return json.dumps(data.model_dump(), default=str, indent=2)
        if isinstance(data, str):
            return data
        try:
            return json.dumps(data, default=str, indent=2)
        except TypeError:
            return str(data)

    def render_prompt(self, data: I) -> str:
        parts = [self.render_specification(data).strip()]
        rendered_input = self.render_input(data).strip()
        if rendered_input:
            parts.append(f"Input:\n{rendered_input}")
        hint = self.output_schema_hint().strip()
        if hint:
            parts.append(hint)
        return "\n\n".join(p for p in parts if p)

    def parse_output(self, text: str) -> Any:
        return self._extract_json(text) if self._wants_json() else text

    def apply(self, data: I) -> O:
        return self.parse_output(self.call_provider(self.render_prompt(data)))  # type: ignore[return-value]

    async def aapply(self, data: I) -> O:
        prompt = self.render_prompt(data)
        return self.parse_output(await self.acall_provider(prompt))  # type: ignore[return-value]

    def _input_as_mapping(self, data: Any) -> dict[str, Any]:
        if hasattr(data, "model_dump"):
            return data.model_dump()
        if isinstance(data, dict):
            return data
        if hasattr(data, "__dict__"):
            return vars(data)
        return {}

    @staticmethod
    def _extract_json(text: str) -> Any:
        stripped = text.strip()
        fence = re.search(r"```(?:json)?\s*(.+?)```", stripped, re.DOTALL)
        if fence:
            stripped = fence.group(1).strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
        for opener, closer in (("{", "}"), ("[", "]")):
            start, end = stripped.find(opener), stripped.rfind(closer)
            if 0 <= start < end:
                try:
                    return json.loads(stripped[start : end + 1])
                except json.JSONDecodeError:
                    continue
        raise ValueError("could not extract JSON; override parse_output for other formats")

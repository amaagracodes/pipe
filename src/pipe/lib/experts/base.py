"""Generic functional-interface layer for experts (java.util.function style).

``Expert[I, O]`` is the ``Function<I, O>`` root; ``Supplier``/``Consumer``/
``BiExpert`` are the sibling shapes. Type args are reified from ``__orig_bases__``
so a subclass knows its own I/O schemas. Everything is an overridable ABC hook.
"""

from __future__ import annotations

import abc
from typing import Any, Generic, TypeVar, get_args, get_origin

from pipe.lib.core.base import PipeMeta
from pipe.lib.experts.interface import ExpertPipe

__all__ = ["Expert", "Supplier", "Consumer", "BiExpert", "SENTINEL_UNSET"]

I = TypeVar("I")
O = TypeVar("O")
I2 = TypeVar("I2")


class _Unset:
    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover
        return "UNSET"


SENTINEL_UNSET = _Unset()


def _is_pydantic_model(tp: Any) -> bool:
    try:
        from pydantic import BaseModel
    except ModuleNotFoundError:  # pragma: no cover
        return False
    return isinstance(tp, type) and issubclass(tp, BaseModel)


def _coerce(schema: Any, value: Any) -> Any:
    """Validate through pydantic when schema is a model; else pass through."""
    if value is SENTINEL_UNSET or schema is None:
        return value
    if _is_pydantic_model(schema):
        return value if isinstance(value, schema) else schema.model_validate(value)
    return value


class _ExpertMeta(PipeMeta, abc.ABCMeta):
    def __init__(cls, name: str, bases: tuple[type, ...], ns: dict[str, Any]) -> None:
        super().__init__(name, bases, ns)
        cls._bind_type_params()


class _TypedFunctional(Generic[I, O], metaclass=_ExpertMeta):
    __input_type__: Any = None
    __output_type__: Any = None

    @classmethod
    def _bind_type_params(cls) -> None:
        root = globals().get("_TypedFunctional")
        if root is None:
            return
        in_slot, out_slot = cls._type_param_slots()
        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if not (isinstance(origin, type) and issubclass(origin, root)):
                continue
            args = get_args(base)
            if not args:
                continue
            if in_slot is not None and in_slot < len(args):
                if not isinstance(args[in_slot], TypeVar):
                    cls.__input_type__ = args[in_slot]
            if out_slot is not None and out_slot < len(args):
                if not isinstance(args[out_slot], TypeVar):
                    cls.__output_type__ = args[out_slot]
            return

    @classmethod
    def _type_param_slots(cls) -> tuple[int | None, int | None]:
        return (0, 1)


class Expert(_TypedFunctional[I, O], ExpertPipe, abc.ABC):
    """Function<I, O>: implement ``apply``; called as a Pipe, chains with ``>>``.

    ``forward`` runs validate_input -> apply -> validate_output; each is overridable.
    """

    @classmethod
    def _type_param_slots(cls) -> tuple[int | None, int | None]:
        return (0, 1)

    def validate_input(self, data: Any) -> Any:
        return _coerce(self.__input_type__, data)

    def validate_output(self, value: Any) -> Any:
        return _coerce(self.__output_type__, value)

    @abc.abstractmethod
    def apply(self, data: I) -> O:
        raise NotImplementedError

    async def aapply(self, data: I) -> O:
        return self.apply(data)

    def forward(self, data: Any) -> Any:
        return self.validate_output(self.apply(self.validate_input(data)))

    async def aforward(self, data: Any) -> Any:
        return self.validate_output(await self.aapply(self.validate_input(data)))


class Supplier(_TypedFunctional[Any, O], ExpertPipe, abc.ABC):
    """Supplier<O>: no input, produces an O. Called with no argument."""

    @classmethod
    def _type_param_slots(cls) -> tuple[int | None, int | None]:
        return (None, 0)

    def validate_output(self, value: Any) -> Any:
        return _coerce(self.__output_type__, value)

    @abc.abstractmethod
    def supply(self) -> O:
        raise NotImplementedError

    async def asupply(self) -> O:
        return self.supply()

    def forward(self, *args: Any, **kwargs: Any) -> Any:
        return self.validate_output(self.supply())

    async def aforward(self, *args: Any, **kwargs: Any) -> Any:
        return self.validate_output(await self.asupply())


class Consumer(_TypedFunctional[I, Any], ExpertPipe, abc.ABC):
    """Consumer<I>: side-effecting sink; returns input unchanged so it can tee."""

    @classmethod
    def _type_param_slots(cls) -> tuple[int | None, int | None]:
        return (0, None)

    def validate_input(self, data: Any) -> Any:
        return _coerce(self.__input_type__, data)

    @abc.abstractmethod
    def consume(self, data: I) -> None:
        raise NotImplementedError

    async def aconsume(self, data: I) -> None:
        self.consume(data)

    def forward(self, data: Any) -> Any:
        checked = self.validate_input(data)
        self.consume(checked)
        return checked

    async def aforward(self, data: Any) -> Any:
        checked = self.validate_input(data)
        await self.aconsume(checked)
        return checked


class BiExpert(_TypedFunctional[I, O], ExpertPipe, abc.ABC, Generic[I, I2, O]):
    """BiFunction<I, I2, O>: two inputs. Invoked with two positional args."""

    __input2_type__: Any = None

    @classmethod
    def _type_param_slots(cls) -> tuple[int | None, int | None]:
        return (0, 2)

    @classmethod
    def _bind_type_params(cls) -> None:
        super()._bind_type_params()
        root = globals().get("BiExpert")
        if root is None:
            return
        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if not (isinstance(origin, type) and issubclass(origin, root)):
                continue
            args = get_args(base)
            if len(args) >= 2 and not isinstance(args[1], TypeVar):
                cls.__input2_type__ = args[1]
            return

    def validate_inputs(self, a: Any, b: Any) -> tuple[Any, Any]:
        return _coerce(self.__input_type__, a), _coerce(self.__input2_type__, b)

    def validate_output(self, value: Any) -> Any:
        return _coerce(self.__output_type__, value)

    @abc.abstractmethod
    def apply2(self, a: I, b: I2) -> O:
        raise NotImplementedError

    async def aapply2(self, a: I, b: I2) -> O:
        return self.apply2(a, b)

    def forward(self, a: Any, b: Any) -> Any:
        ca, cb = self.validate_inputs(a, b)
        return self.validate_output(self.apply2(ca, cb))

    async def aforward(self, a: Any, b: Any) -> Any:
        ca, cb = self.validate_inputs(a, b)
        return self.validate_output(await self.aapply2(ca, cb))

"""pipe.lib.core.base — the structural layer + metaclass.

DSPy splits its abstraction in two:

  * ``BaseModule`` — the *structural* layer. It knows nothing about calling;
    it only walks an instance's attributes to discover nested sub-modules,
    enabling introspection, composition and copying.
  * ``Module`` — the *behavioural* layer (see :mod:`pipe.lib.core.pipe`).

``BasePipe`` here is that structural layer for pipe, and ``PipeMeta`` is the
metaclass that guarantees base attributes exist on every ``Pipe`` — analogous
to DSPy's ``ProgramMeta``.

No third-party imports: safe under Cloudflare's Pyodide runtime.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pipe.lib.core.pipe import Pipe

__all__ = ["BasePipe", "PipeMeta"]


class BasePipe:
    """Structural layer: attribute-walking, discovery, and copying.

    Analogous to ``dspy.primitives.BaseModule``. Holds no calling logic — it
    only understands how ``Pipe``s nest inside one another so that a composite
    ``Pipe`` can be introspected and copied as a unit.
    """

    def named_pipes(self) -> list[tuple[str, "Pipe"]]:
        """Return ``(name, pipe)`` for every ``Pipe`` reachable from ``self``.

        Walks ``__dict__`` one level deep, descending into nested ``Pipe``s and
        into lists/tuples/dicts of ``Pipe``s. Names use dotted / indexed paths
        (``"encoder"``, ``"stages[0]"``, ``"routes['en']"``) so each sub-pipe
        has a stable address. Mirrors ``BaseModule.named_parameters``.
        """
        from pipe.lib.core.pipe import Pipe

        visited: set[int] = set()
        found: list[tuple[str, "Pipe"]] = []

        def add(name: str, value: Any) -> None:
            if isinstance(value, Pipe):
                if id(value) in visited:
                    return
                visited.add(id(value))
                found.append((name, value))
                # Descend so composites of composites are fully discovered.
                for sub_name, sub in value.named_pipes():
                    child = f"{name}.{sub_name}"
                    if id(sub) not in visited:
                        visited.add(id(sub))
                        found.append((child, sub))
            elif isinstance(value, (list, tuple)):
                for i, item in enumerate(value):
                    add(f"{name}[{i}]", item)
            elif isinstance(value, dict):
                for key, item in value.items():
                    add(f"{name}[{key!r}]", item)

        for name, value in self.__dict__.items():
            add(name, value)
        return found

    def pipes(self) -> list["Pipe"]:
        """All nested ``Pipe`` instances (names dropped)."""
        return [p for _, p in self.named_pipes()]

    def deepcopy(self) -> "BasePipe":
        """Deep copy, falling back to a shallow attribute copy if needed.

        Mirrors ``BaseModule.deepcopy``: a plain ``copy.deepcopy`` when the
        instance allows it, otherwise a best-effort attribute-by-attribute copy.
        """
        try:
            return copy.deepcopy(self)
        except Exception:
            new = self.__class__.__new__(self.__class__)
            for attr, value in self.__dict__.items():
                try:
                    setattr(new, attr, copy.deepcopy(value))
                except Exception:
                    setattr(new, attr, copy.copy(value))
            return new


class PipeMeta(type):
    """Metaclass guaranteeing base attributes exist on every ``Pipe``.

    Analogous to DSPy's ``ProgramMeta``: it runs ``Pipe._base_init`` before the
    subclass ``__init__`` so a subclass that forgets ``super().__init__()``
    still has the attributes the framework relies on (here: ``name``).
    """

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        from pipe.lib.core.pipe import Pipe

        obj = cls.__new__(cls, *args, **kwargs)
        if isinstance(obj, cls):
            Pipe._base_init(obj)
            cls.__init__(obj, *args, **kwargs)
            if not hasattr(obj, "name"):
                obj.name = cls.__name__
        return obj

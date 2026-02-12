from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator
from uuid import uuid7

from greenlet import greenlet

from runa import Entity


@dataclass(kw_only=True, frozen=True)
class InitializeReceived:
    id: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


@dataclass(kw_only=True, frozen=True)
class InitializeHandled:
    id: str
    request_id: str


@dataclass(kw_only=True, frozen=True)
class StateChanged:
    id: str
    state: Any


@dataclass(kw_only=True, frozen=True)
class RequestReceived:
    id: str
    method_name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


@dataclass(kw_only=True, frozen=True)
class RequestHandled:
    id: str
    request_id: str
    response: Any


@dataclass(kw_only=True, frozen=True)
class CreateEntityPublished:
    id: str
    entity_type: type[Entity[Any]]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


ExecutionContext = list[
    InitializeReceived
    | InitializeHandled
    | StateChanged
    | RequestReceived
    | RequestHandled
    | CreateEntityPublished
]


class ExecutionResult:
    def __init__(
        self,
        entity: Entity[Any],
        context: ExecutionContext,
    ) -> None:
        self.entity = entity
        self.context = context


class Runa:
    def __init__(self, entity_type: type[Entity[Any]]) -> None:
        self.entity_type = entity_type

    def execute(
        self,
        context: ExecutionContext,
    ) -> ExecutionResult:
        main_greenlet = greenlet.getcurrent()
        entity = Entity.__new__(self.entity_type)
        result = ExecutionResult(entity, [])

        for event in context:
            if isinstance(event, InitializeReceived):
                execution = greenlet(getattr(self.entity_type, "__init__"))
                execution.switch(entity, *event.args, **event.kwargs)

                if not execution.dead:
                    raise NotImplementedError

                result.context.append(event)

                result.context.append(
                    InitializeHandled(
                        id=_generate_event_id(),
                        request_id=event.id,
                    )
                )
                result.context.append(
                    StateChanged(
                        id=_generate_event_id(),
                        state=entity.__getstate__(),
                    )
                )
            elif isinstance(event, StateChanged):
                result.context.append(event)
                entity.__setstate__(event.state)
            elif isinstance(event, RequestReceived):
                execution = greenlet(getattr(self.entity_type, event.method_name))

                with _intercept_instantiate_entity(main_greenlet):
                    interception = execution.switch(entity, *event.args, **event.kwargs)

                result.context.append(event)

                if not execution.dead:
                    result.context.append(interception)
                else:
                    result.context.append(
                        RequestHandled(
                            id=_generate_event_id(),
                            request_id=event.id,
                            response=interception,
                        )
                    )
                    result.context.append(
                        StateChanged(
                            id=_generate_event_id(),
                            state=entity.__getstate__(),
                        )
                    )

        return result


@contextmanager
def _intercept_instantiate_entity(main_greenlet: greenlet) -> Generator[None, None]:
    def new(cls: type[Entity[Any]], *args: Any, **kwargs: Any) -> Entity[Any]:
        entity: Entity[Any] = main_greenlet.switch(
            CreateEntityPublished(
                id=_generate_event_id(),
                entity_type=cls,
                args=args,
                kwargs=kwargs,
            )
        )

        # Temporary patch __init__ to avoid double initialization
        def init(*_: Any, **__: Any) -> None:
            setattr(cls, "__init__", original_init)

        original_init = getattr(cls, "__init__")
        setattr(cls, "__init__", init)
        return entity

    original_new = Entity.__new__
    setattr(Entity, "__new__", new)
    try:
        yield
    finally:
        setattr(Entity, "__new__", original_new)


def _generate_event_id() -> str:
    return uuid7().hex

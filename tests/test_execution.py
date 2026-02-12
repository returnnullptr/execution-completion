from dataclasses import dataclass

from runa import Entity, Runa
from runa.execution import (
    InitializeReceived,
    InitializeHandled,
    StateChanged,
    RequestReceived,
    RequestHandled,
    CreateEntityPublished,
)


@dataclass
class UserState:
    name: str
    pets: list[Pet]


class User(Entity[UserState]):
    def __init__(self, name: str) -> None:
        self.name = name
        self.pets: list[Pet] = []

    def __getstate__(self) -> UserState:
        return UserState(self.name, self.pets)

    def __setstate__(self, state: UserState) -> None:
        self.name = state.name
        self.pets = state.pets

    def change_name(self, name: str) -> str:
        self.name = name
        return "Sure!"

    def add_pet(self, name: str) -> None:
        self.pets.append(Pet(name, owner=self))


@dataclass
class PetState:
    name: str


class Pet(Entity[PetState]):
    def __init__(self, name: str, owner: User) -> None:
        self.name = name
        self.owner = owner

    def __getstate__(self) -> PetState:
        return PetState(self.name)

    def __setstate__(self, state: PetState) -> None:
        self.name = state.name


def test_execute_initialize_received() -> None:
    result = Runa(User).execute(
        context=[
            InitializeReceived(
                id="request-1",
                args=("Yura",),
                kwargs={},
            ),
        ],
    )
    assert isinstance(result.entity, User)
    assert result.entity.name == "Yura"
    assert result.context == [
        InitializeReceived(
            id="request-1",
            args=("Yura",),
            kwargs={},
        ),
        InitializeHandled(
            id=result.context[1].id,
            request_id="request-1",
        ),
        StateChanged(
            id=result.context[2].id,
            state=UserState("Yura", []),
        ),
    ]


def test_execute_state_changed() -> None:
    result = Runa(User).execute(
        context=[
            StateChanged(
                id="state-changed-1",
                state=UserState("Yura", []),
            ),
        ],
    )
    assert isinstance(result.entity, User)
    assert result.entity.name == "Yura"
    assert result.context == [
        StateChanged(
            id="state-changed-1",
            state=UserState("Yura", []),
        ),
    ]


def test_execute_request_received() -> None:
    result = Runa(User).execute(
        context=[
            StateChanged(
                id="state-changed-1",
                state=UserState("Yura", []),
            ),
            RequestReceived(
                id="request-1",
                method_name="change_name",
                args=("Yuriy",),
                kwargs={},
            ),
        ],
    )
    assert isinstance(result.entity, User)
    assert result.entity.name == "Yuriy"
    assert result.context == [
        StateChanged(
            id="state-changed-1",
            state=UserState("Yura", []),
        ),
        RequestReceived(
            id="request-1",
            method_name="change_name",
            args=("Yuriy",),
            kwargs={},
        ),
        RequestHandled(
            id=result.context[2].id,
            request_id="request-1",
            response="Sure!",
        ),
        StateChanged(
            id=result.context[3].id,
            state=UserState("Yuriy", []),
        ),
    ]


def test_execute_create_entity_published() -> None:
    result = Runa(User).execute(
        context=[
            StateChanged(
                id="state-changed-1",
                state=UserState("Yuriy", []),
            ),
            RequestReceived(
                id="request-1",
                method_name="add_pet",
                args=(),
                kwargs={"name": "Stitch"},
            ),
        ],
    )
    assert isinstance(result.entity, User)
    assert not result.entity.pets
    assert result.context == [
        StateChanged(
            id="state-changed-1",
            state=UserState("Yuriy", []),
        ),
        RequestReceived(
            id="request-1",
            method_name="add_pet",
            args=(),
            kwargs={"name": "Stitch"},
        ),
        CreateEntityPublished(
            id=result.context[2].id,
            entity_type=Pet,
            args=("Stitch",),
            kwargs={"owner": result.entity},
        ),
    ]

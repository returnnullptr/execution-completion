from dataclasses import dataclass

from runa import Entity, Runa
from runa.execution import (
    InitializeReceived,
    InitializeHandled,
    StateChanged,
    RequestReceived,
    RequestHandled,
    CreateEntityRequested,
    EntityCreatedReceived,
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
        return UserState(self.name, self.pets.copy())

    def __setstate__(self, state: UserState) -> None:
        self.name = state.name
        self.pets = state.pets.copy()

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
    user = Runa(User)
    result = user.execute(
        context=[
            InitializeReceived(
                id="request-1",
                args=("Yura",),
                kwargs={},
            ),
        ],
    )
    assert isinstance(user.entity, User)
    assert user.entity.name == "Yura"
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
    user = Runa(User)
    result = user.execute(
        context=[
            StateChanged(
                id="state-changed-1",
                state=UserState("Yura", []),
            ),
        ],
    )
    assert isinstance(user.entity, User)
    assert user.entity.name == "Yura"
    assert result.context == [
        StateChanged(
            id="state-changed-1",
            state=UserState("Yura", []),
        ),
    ]


def test_execute_request_received() -> None:
    user = Runa(User)
    result = user.execute(
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
    assert isinstance(user.entity, User)
    assert user.entity.name == "Yuriy"
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


def test_execute_create_entity_requested() -> None:
    user = Runa(User)
    result = user.execute(
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
    assert isinstance(user.entity, User)
    assert not user.entity.pets
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
        CreateEntityRequested(
            id=result.context[2].id,
            entity_type=Pet,
            args=("Stitch",),
            kwargs={"owner": user.entity},
        ),
    ]


def test_execute_entity_created_received() -> None:
    user = Runa(User)
    pet = Pet("Stitch", owner=user.entity)
    result = user.execute(
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
            CreateEntityRequested(
                id="create-entity-1",
                entity_type=Pet,
                args=("Stitch",),
                kwargs={"owner": user.entity},
            ),
            EntityCreatedReceived(
                id="entity-created-1",
                request_id="create-entity-1",
                entity=pet,
            ),
        ],
    )
    assert isinstance(user.entity, User)
    assert user.entity.pets == [pet]
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
        CreateEntityRequested(
            id="create-entity-1",
            entity_type=Pet,
            args=("Stitch",),
            kwargs={"owner": user.entity},
        ),
        EntityCreatedReceived(
            id="entity-created-1",
            request_id="create-entity-1",
            entity=pet,
        ),
        RequestHandled(
            id=result.context[4].id,
            request_id="request-1",
            response=None,
        ),
        StateChanged(
            id=result.context[5].id,
            state=UserState("Yuriy", [pet]),
        ),
    ]

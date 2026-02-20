# Execution completion

Execution completion is a way of executing domain model logic, inspired by chat completion.

During inference, an LLM cannot cause side effects, but it can stop with the intention of calling a tool.

The same can be done for the domain model. Let's imagine, that the domain model cannot cause side effects, but it can pause execution with the intention of requesting another entity or external service.

For example, the domain model consists of regular classes and synchronous methods:
```python
@dataclass
class SenderState:
    receiver: Receiver


class Sender(Entity):
    def __init__(self, receiver: Receiver) -> None:
        self.receiver = receiver

    def __getstate__(self) -> SenderState:
        return SenderState(self.receiver)

    def __setstate__(self, state: SenderState) -> None:
        self.receiver = state.receiver

    def send(self, message: str) -> str:
        return self.receiver.receive(message)


@dataclass
class ReceiverState:
    messages: list[str]


class Receiver(Entity):
    def __init__(self) -> None:
        self.messages: list[str] = []

    def __getstate__(self) -> ReceiverState:
        return ReceiverState(self.messages)

    def __setstate__(self, state: ReceiverState) -> None:
        self.messages = state.messages

    def receive(self, message: str) -> str:
        self.messages.append(message)
        return f"Received: {message!r}"
```

The `Execution` accepts input messages and produces output messages, even if the execution is suspended.

```python
execution = Execution(Sender)
receiver = Receiver()

input_messages: list[ContextMessage] = [
    EntityStateChanged(
        offset=2,
        state=SenderState(receiver),
    ),
    EntityMethodRequestReceived(
        offset=3,
        method=Sender.send,
        args=("Hello!",),
        kwargs={},
    ),
]

output_messages = execution.complete(input_messages)

assert output_messages == [
    EntityMethodRequestSent(
        offset=4,
        trace_offset=3,
        receiver=receiver,
        method=Receiver.receive,
        args=("Hello!",),
        kwargs={},
    ),
]
```

The execution can be resumed when the result is available:

```python
input_messages: list[ContextMessage] = [
    EntityStateChanged(
        offset=2,
        state=SenderState(receiver),
    ),
    EntityMethodRequestReceived(
        offset=3,
        method=Sender.send,
        args=("Hello!",),
        kwargs={},
    ),
    EntityMethodRequestSent(
        offset=4,
        trace_offset=3,
        receiver=receiver,
        method=Receiver.receive,
        args=("Hello!",),
        kwargs={},
    ),
    EntityMethodResponseReceived(
        offset=5,
        request_offset=4,
        response=receiver.receive("Hello!"),
    ),
]

output_messages = execution.complete(input_messages)

assert output_messages == [
    EntityMethodResponseSent(
        offset=6,
        request_offset=3,
        response="Received: 'Hello!'",
    ),
    EntityStateChanged(
        offset=7,
        state=SenderState(receiver),
    ),
]
```

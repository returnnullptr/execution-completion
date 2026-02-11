# Runa

Domain logic isolation research

## Glossary

- **Entity** is a domain object defined primarily by its unique identity.
- **Entity state** is mutable data that can change without affecting the entity's identity.
- **Service** is an external system or infrastructure that entities can interact with.
- **Request** is a message sent to an entity or service, expecting a response.
- **Response** is a message sent by an entity or service in reply to a request.
- **Event** is a message that reflects an occurrence within the domain and is published without specifying its recipients.
- **Error** is a message that indicates a failure or problem occurred while processing another message.
- **Execution context** is the current state of an entity along with the set of messages it is currently processing, including any messages sent or received during that processing.

## Rules

- An entity can access and modify its own state.
- An entity cannot access or modify another entity's state.
- An entity interacts with other entities or services only through messages.
- An entity receives messages in the same order they were produced.
- An entity or service processes every message it receives.
- An entity or service replies to every request it receives.
- An entity can send requests to other entities or services.
- An entity can create other entities.
- An entity receives a response for every request it sends.
- An entity can publish events.
- Processing can be suspended until a response is received.
- An execution context can be saved and restored during processing.

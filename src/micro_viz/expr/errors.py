"""The one error the expression engine raises, and the message provider it renders with."""

from __future__ import annotations

from collections.abc import Callable, Mapping

MessageProvider = Callable[[str, str | None, Mapping[str, object]], str]
"""``provider(message_id, language, fields)`` returns the text of an error message.

The engine owns message ids and their fields, never their words: the caller registers a
provider (micro-viz reads its locale tables) and the engine falls back to the bare id.
"""


def default_messages(message_id: str, language: str | None, fields: Mapping[str, object]) -> str:
    """Render an id with its fields when no provider is registered."""
    shown = ", ".join(f"{key}={value!r}" for key, value in fields.items())
    return f"{message_id}({shown})" if shown else message_id


class ExprError(ValueError):
    """A formula that cannot be read or evaluated, with the place where it went wrong.

    ``message_id`` and ``fields`` identify the problem independent of language, ``source`` is the
    formula text and ``position`` the index of the offending character (or ``None``). ``str()``
    gives the message, the formula and a caret line under the position.
    """

    def __init__(
        self,
        message_id: str,
        *,
        source: str = "",
        position: int | None = None,
        provider: MessageProvider = default_messages,
        language: str | None = None,
        **fields: object,
    ) -> None:
        self.message_id = message_id
        self.fields = dict(fields)
        self.source = source
        self.position = position
        self._provider = provider
        self._language = language
        super().__init__(message_id)

    def with_context(self, *, source: str, provider: MessageProvider) -> ExprError:
        """The same error attached to a formula text and a message provider."""
        error = ExprError(self.message_id, source=source, position=self.position, provider=provider)
        error.fields = dict(self.fields)
        error._language = self._language
        return error

    def message(self, language: str | None = None) -> str:
        """The message alone, in ``language`` (default: the language the error was raised in)."""
        return self._provider(self.message_id, language or self._language, self.fields)

    def render(self, language: str | None = None) -> str:
        """The message, the formula and a caret under the position."""
        text = self.message(language)
        if not self.source or self.position is None:
            return text
        caret = " " * min(self.position, len(self.source)) + "^"
        return f"{text}\n  {self.source}\n  {caret}"

    def __str__(self) -> str:
        return self.render()

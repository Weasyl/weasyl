from __future__ import annotations

import enum
from collections import deque
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Mapping
from typing import Generic
from typing import NamedTuple
from typing import Protocol
from typing import TypeVar

import pytest

from weasyl import frienduser
from weasyl import message
from weasyl import profile
from weasyl.test import db_utils


class _some(NamedTuple):

    t: type

    def __eq__(self, other) -> bool:
        return isinstance(other, self.t)


class _Relation(NamedTuple):
    friend: bool
    friendreq: bool


_NON_FRIENDS = _Relation(friend=False, friendreq=False)
_FRIEND_REQUESTED = _Relation(friend=False, friendreq=True)
_FRIENDS = _Relation(friend=True, friendreq=False)


def _select_relation(userid: int, otherid: int) -> _Relation:
    relation = profile.select_relation(userid, otherid)

    return _Relation(
        friend=relation["friend"],
        friendreq=relation["friendreq"],
    )


class Mirrorable(Protocol):

    def __neg__(self) -> Mirrorable:  # -> Self
        ...


@enum.unique
class Action(enum.Enum):

    ADD_BY_A = 1
    """*A* requests or confirms a friendship with *B*."""

    ADD_BY_B = -1

    REMOVE_BY_A = 2
    """*A* rejects a friend request from *B*, or ends a friendship with *B*."""

    REMOVE_BY_B = -2

    WITHDRAW_BY_A = 3
    """*A* withdraws a friend request sent to *B*."""

    WITHDRAW_BY_B = -3

    def __neg__(self) -> Action:
        return Action(-self.value)


@enum.unique
class State(enum.Enum):

    INITIAL = (0, 0)
    REQUEST_FROM_A = (1, 1)
    REQUEST_FROM_B = (1, -1)

    FRIENDS_FROM_A = (2, 1)
    """*A* and *B* are friends as the result of a friend request from *A*."""

    FRIENDS_FROM_B = (2, -1)

    def __neg__(self) -> State:
        t, d = self.value
        return State((t, -d))


P = TypeVar("P", bound=Mirrorable)
T = TypeVar("T", bound=Mirrorable)


class _mirrorable(Mirrorable, Generic[P, T]):
    """
    Add the negation operator to a partial function, where (-f)(x) = -f(-x).
    """

    f: Callable[[P], T | None]
    _is_neg: bool
    _neg: _mirrorable[P, T]

    def __init__(
        self,
        f: Callable[[P], T | None],
        is_neg: bool = False,
        neg: _mirrorable[P, T] | None = None,  # neg: Self | None
    ):
        self.f = f
        self._is_neg = is_neg
        self._neg = neg or _mirrorable(f, not is_neg, self)

    def __call__(self, x: P) -> T | None:
        if self._is_neg:
            r = self.f(-x)
            return r and -r
        else:
            return self.f(x)

    def __neg__(self) -> _mirrorable[P, T]:
        return self._neg


class _symmetric(Mirrorable, Generic[P, T]):
    """
    Extend a partial function's domain using the symmetry f(x) = -f(-x).
    """

    f: Callable[[P], T | None]

    def __init__(self, f: Callable[[P], T | None]):
        self.f = f

    def __call__(self, x: P) -> T | None:
        return self.f(x) or ((y := self.f(-x)) and -y)

    def __neg__(self) -> _symmetric[P, T]:  # -> Self
        return self


_TRANSITIONS = _symmetric[State, _symmetric[Action, State] | _mirrorable[Action, State]]({
    State.INITIAL: _symmetric[Action, State]({
        Action.ADD_BY_A: State.REQUEST_FROM_A,
    }.get),
    State.REQUEST_FROM_A: _mirrorable[Action, State]({
        Action.ADD_BY_B: State.FRIENDS_FROM_A,
        Action.REMOVE_BY_A: State.INITIAL,
        Action.REMOVE_BY_B: State.INITIAL,
        Action.WITHDRAW_BY_A: State.INITIAL,
    }.get),
    State.FRIENDS_FROM_A: _symmetric[Action, State]({
        Action.REMOVE_BY_A: State.INITIAL,
    }.get),
}.get)


def _apply_expected(state: State, action: Action) -> State:
    """
    Get the expected state with respect to two users' friendship given a previous state and an action.
    """
    tt = _TRANSITIONS(state)
    assert tt is not None
    return tt(action) or state


def _apply_app(action: Action, user1: int, user2: int) -> None:
    """
    Apply an action to the app.
    """
    match action:
        case Action.ADD_BY_A:
            frienduser.request(user1, user2)
        case Action.REMOVE_BY_A:
            frienduser.remove(user1, user2)
        case Action.WITHDRAW_BY_A:
            frienduser.remove_request(user1, user2)
        case _:
            _apply_app(-action, user2, user1)


def _assert_app(state: State, user1: int, user2: int) -> None:
    """
    Assert that the app is in a specific state with respect to two users' friendship.
    """
    def forward_relation() -> _Relation:
        return _select_relation(user1, user2)

    def reverse_relation() -> _Relation:
        return _select_relation(user2, user1)

    match state:
        case State.INITIAL:
            assert forward_relation() == _NON_FRIENDS
            assert reverse_relation() == _NON_FRIENDS

            assert frienduser.check(user1, user2) is False
            assert frienduser.check(user2, user1) is False

            assert frienduser.has_friends(user1) is False
            assert frienduser.has_friends(user2) is False

            assert frienduser.select_friends(0, user1) == []
            assert frienduser.select_friends(0, user2) == []

            assert frienduser.select_requests(user1) == []
            assert frienduser.select_requests(user2) == []

            assert message.select_notifications(user1) == []
            assert message.select_notifications(user2) == []

        case State.REQUEST_FROM_A:
            assert forward_relation() == _FRIEND_REQUESTED
            assert reverse_relation() == _NON_FRIENDS

            assert frienduser.check(user1, user2) is False
            assert frienduser.check(user2, user1) is False

            assert frienduser.has_friends(user1) is False
            assert frienduser.has_friends(user2) is False

            assert frienduser.select_friends(0, user1) == []
            assert frienduser.select_friends(0, user2) == []

            assert frienduser.select_requests(user1) == []
            assert frienduser.select_requests(user2) == [{
                "userid": user1,
                "username": _some(str),
                "user_media": _some(dict),
            }]

            assert message.select_notifications(user1) == []
            assert message.select_notifications(user2) == [{
                "id": _some(int),
                "type": 3080,
                "unixtime": _some(int),
                "userid": user1,
                "username": _some(str),
            }]

        case State.FRIENDS_FROM_A:
            assert forward_relation() == _FRIENDS
            assert reverse_relation() == _FRIENDS

            assert frienduser.check(user1, user2) is True
            assert frienduser.check(user2, user1) is True

            assert frienduser.has_friends(user1) is True
            assert frienduser.has_friends(user2) is True

            assert frienduser.select_friends(0, user1) == [{
                "userid": user2,
                "username": _some(str),
                "user_media": _some(dict),
            }]
            assert frienduser.select_friends(0, user2) == [{
                "userid": user1,
                "username": _some(str),
                "user_media": _some(dict),
            }]

            assert frienduser.select_requests(user1) == []
            assert frienduser.select_requests(user2) == []

            assert message.select_notifications(user1) == [{
                "id": _some(int),
                "type": 3085,
                "unixtime": _some(int),
                "userid": user2,
                "username": _some(str),
            }]
            assert message.select_notifications(user2) == []

        case _:
            _assert_app(-state, user2, user1)


def _all_transitions() -> Iterable[list[Action]]:
    """
    Get the shortest sequences of actions to exercise each transition, skipping any sequence that is a prefix of another sequence.
    """
    queue: deque[tuple[list[Action], State]] = deque([([], State.INITIAL)])
    seen: set[tuple[State, Action]] = set()

    while queue:
        sequence, state = queue.popleft()
        has_continuations = False

        for action in Action:
            if (state, action) not in seen:
                has_continuations = True
                seen.add((state, action))
                queue.append((sequence + [action], _apply_expected(state, action)))

        if not has_continuations:
            yield sequence


_ACTION_DESCS: Mapping[Action, str] = {
    Action.ADD_BY_A: "A adds B",
    Action.ADD_BY_B: "B adds A",
    Action.REMOVE_BY_A: "A removes B",
    Action.REMOVE_BY_B: "B removes A",
    Action.WITHDRAW_BY_A: "A withdraws",
    Action.WITHDRAW_BY_B: "B withdraws",
}


def _repr_sequence(sequence: Iterable[Action]) -> str:
    return ", ".join(_ACTION_DESCS[action] for action in sequence)


# HACK: Avoid creating redundant subtests.
_SUBTESTED: set[tuple[State, Action] | None] = set()


@pytest.mark.parametrize("sequence", [
    pytest.param(sequence, id=_repr_sequence(sequence))
    for sequence in _all_transitions()
])
def test_sequence(
    subtests: pytest.Subtests,
    db,
    sequence: Iterable[Action],
) -> None:
    user1 = db_utils.create_user()
    user2 = db_utils.create_user()

    state = State.INITIAL
    prefix = []

    if None not in _SUBTESTED:
        _SUBTESTED.add(None)

        with subtests.test("initial state"):
            _assert_app(state, user1, user2)

    for action in sequence:
        prefix.append(action)
        is_new = (state, action) not in _SUBTESTED
        _SUBTESTED.add((state, action))
        state = _apply_expected(state, action)

        if is_new:
            with subtests.test(f"{_repr_sequence(prefix)} -> {state}"):
                _apply_app(action, user1, user2)
                _assert_app(state, user1, user2)
        else:
            _apply_app(action, user1, user2)


@pytest.mark.skip("not written")
def test_sequences_with_blocking() -> None:
    # TODO: ignoreuser
    raise NotImplementedError()

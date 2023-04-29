from typing import (
    Any,
    TypeVar,
    Optional,
    Callable,
    Iterable,
)
from discord import Member
from copy import copy
import re

T = TypeVar('T')
_NON_NEGATIVE_INT_RE = re.compile(r'[0-9]+')


def get_name(member: Member) -> str:
    """Returns the name of the member.

    Parameters
    ----------
    member : Member
        The member to get the name from.

    Returns
    -------
    str
        The name of the member.
    """

    return member.name.replace(" ", "_")


def find(predicate: Callable[[T], bool], iterable: Iterable[T]) -> Optional[T]:
    """A helper to return the first element found in the sequence
    that meets the predicate.

    Parameters
    ----------
    predicate : Callable[[T], bool]
        The predicate to check against.
    iterable : Iterable[T]
        The iterable to search through.

    Returns
    -------
    Optional[T]
        The first element found in the sequence that meets the predicate.
    """

    for i in iterable:
        if predicate(i):
            return i
    return None


def find_all(predicate: Callable[[T], bool], iterable: Iterable[T]) -> list[T]:
    """A helper to return all elements found in the sequence
    that meets the predicate.

    Parameters
    ----------
    predicate : Callable[[T], bool]
        The predicate to check against.
    iterable : Iterable[T]
        The iterable to search through.

    Returns
    -------
    Iterable[T]
        The elements found in the sequence that meets the predicate.
    """

    return [i for i in iterable if predicate(i)]


def get(iterable: Iterable[T], conditions: dict[str, Any]) -> Optional[T]:
    """A helper to return the first element found in the iterable

    Parameters
    ----------
    iterable : Iterable[T]
        The iterable to search through.
    conditions : dict[str, Any]
        The conditions to check against.

    Returns
    -------
    Optional[T]
        The first element found in the iterable that meets the conditions.
    To have a nested attribute search (i.e. search by ``x.y``) then
    pass in ``x.y`` as the conditions' dict key.

    Sample
    ------
    >>> class A:
    >>>     def __init__(self, a, b):
    >>>         self.a = a
    >>>         self.b = b
    >>>
    >>> class B:
    >>>
    >>>     def __init__(self, c, d):
    >>>         self.c = c
    >>>         self.d = d
    >>>
    >>> var = get([A(B(1, 2), 3), A(B(4, 5), 6)], {'a.c': 1, 'b': 3})    # returns A(B(1, 2), 3)
    >>> var_2 = get([A(B(1, 2), 3), A(B(4, 5), 6)], {'a.c': 4, 'b': 6})  # returns A(B(4, 5), 6)
    """

    for item in iterable:
        flags: list[bool] = []

        for k, v in conditions.items():
            var = copy(item)

            for attr in k.split('.'):
                var = getattr(var, attr)

            flags.append(var==v)

        if all(flags):
            return item

    return None


def get_integers(text: str) -> list[int]:
    """A helper to return all non-negative-integers found in the text.

    Parameters
    ----------
    text : str
        The text to search through.

    Returns
    -------
    list[int]
        The non-negative-integers found in the text.
    """

    return list(map(int, _NON_NEGATIVE_INT_RE.findall(text)))
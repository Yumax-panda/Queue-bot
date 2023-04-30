from __future__ import annotations
from typing import TypeVar, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from discord import Member


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
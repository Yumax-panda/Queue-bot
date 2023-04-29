from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Type, TypeVar
from enum import Enum

T = TypeVar('T')

class Player:
    """A player in a game.

    Attributes
    ----------
    name : str
        The name of the player.
    tag : Optional[str]
        The tag of the player.
    points : list[int]
        The points of the player.
    """

    __slots__ = (
        "name",
        "tag",
        "points"
    )

    if TYPE_CHECKING:
        name: str
        id: int
        tag: Optional[str]
        points: list[int]

    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.tag = kwargs.get("tag")
        self.points = kwargs.get("points", [])

    @property
    def left_race_num(self) -> int:
        return 12-len(self.points)

    @property
    def is_finished(self) -> bool:
        return len(self.points) == 12


    @property
    def total_point(self) -> int:
        return sum(self.points)


class Team:

    __slots__ = (
        "tag",
        "_players"
    )

    if TYPE_CHECKING:
        tag: Optional[str]
        _players: list[Player]


    def __init__(
        self,
        players: list[Player],
        tag: Optional[str] = None
    ) -> None:
        self.tag = tag
        self._players = players


    @property
    def total_point(self) -> int:
        return sum(player.total_point for player in self._players)


    @property
    def players(self) -> list[Player]:
        return sorted(self._players, key = lambda p: p.total_point, reverse = True)

    @property
    def is_finished(self) -> bool:
        return all(player.is_finished for player in self._players)


    @classmethod
    def make_teams(cls: Type[T], players: list[Player]) -> list[T]:
        """Make teams from players.

        Parameters
        ----------
        players : list[Player]
            The players to make teams from.

        Returns
        -------
        list[T]
            The teams made from players.
        """

        tags = set().union(*[p.tag for p in players])
        teams: dict[str, list[Player]] = {tag: [] for tag in tags}
        for player in players:
            teams[player.tag].append(player)
        return [cls(players = players, tag = tag) for tag, players in teams.items()]


class State(Enum):
    ONGOING = True
    DONE = False

    def __bool__(self) -> bool:
        return self._value_



class Game:

    __slots__ = (
        "_teams",
    )

    if TYPE_CHECKING:
        _teams: list[Team]

    def __init__(self, teams: list[Team]) -> None:
        self._teams = teams

    @property
    def teams(self) -> list[Team]:
        return sorted(self._teams, key = lambda t: t.total_point, reverse = True)

    @property
    def format(self) -> int:
        return len(self._teams[0].players)

    @property
    def is_ffa(self) -> bool:
        return self.format == 1

    @property
    def state(self) -> State:
        return State.DONE if all(t.is_finished for t in self._teams) else State.ONGOING

    @property
    def ranking(self) -> list[Player]:
        """Return the ranking of the game.

        Returns
        -------
        list[Player]
            The ranking of the game.
        """

        players = []
        for t in self._teams:
            players.extend(t.players)
        return sorted(players, key = lambda p: p.total_point, reverse = True)
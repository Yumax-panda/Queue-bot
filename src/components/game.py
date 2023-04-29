from __future__ import annotations
from typing import TYPE_CHECKING, Optional, TypeVar, Type, Union
from enum import Enum
from urllib.parse import quote

from errors import *

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

    def add_rank(self, rank: Union[str, int]) -> None:
        """Add a rank to the player.

        Parameters
        ----------
        rank : Union[str, int]
            The rank to add.
        """

        points = {1:15, 2:12, 3:10, 4:9, 5:8, 6:7, 7:6, 8:5, 9:4, 10:3, 11:2, 12:1}

        if str(rank) not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]:
            raise InvalidRank

        if len(self.points) == 12:
            raise AlreadyFinished

        self.points.append(points[int(rank)])


    def remove_rank(self, _index: int=-1) -> None:
        """Remove a rank from the player.

        Parameters
        ----------
        _index : int
            The index of the rank to remove.
        """

        try:
            self.points.pop(_index)
        except IndexError:
            raise InvalidRank


    def edit_rank(self, rank: Union[str, int], _index: int=-1) -> None:
        """Edit a rank of the player.

        Parameters
        ----------
        rank : Union[str, int]
            The rank to edit.
        _index : int
            The index of the rank to edit.
        """

        points = {1:15, 2:12, 3:10, 4:9, 5:8, 6:7, 7:6, 8:5, 9:4, 10:3, 11:2, 12:1}

        if str(rank) not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]:
            raise InvalidRank

        try:
            self.points[_index] = points[int(rank)]
        except IndexError:
            raise InvalidRank




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

        tags = set().union([p.tag for p in players])
        teams: dict[str, list[Player]] = {tag: [] for tag in tags}
        for player in players:
            teams[player.tag].append(player)
        return [cls(players = ps, tag = tag) for tag, ps in teams.items()]


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


    def get_player(self, name: str) -> Player:
        """Get player by name.

        Parameters
        ----------
        name : str
            The name of the player to get.

        Returns
        -------
        Player
            The player with the given name.
        """

        for t in self._teams:
            for p in t.players:
                if p.name == name:
                    return p
        raise NotParticipant(name)


    def result_url(self, title: str = "Result") -> str:
        size = self.format
        base = "https://gb.hlorenzi.com/table.png?data="
        table_text = f"#title {title} "

        if size == 1:
            table_text += "FFA\nFFA - Free for All #4A82D0\n"
            for player in self.ranking:
                table_text += f"{player.name} [] {player.total_point}\n"
        else:
            table_text += f"{size}v{size}\n"
            for index, team in enumerate(sorted(self._teams, key = lambda t: t.total_point, reverse = True)):
                color = "#1D6ADE" if index % 2 == 0 else "#4A82D0"
                table_text += f"{index+1} {color}\n"
                for p in team.players:
                    table_text += f"{p.name} [] {p.total_point}\n"
        return base + quote(table_text)

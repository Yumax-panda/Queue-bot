from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Type, Final
from discord import Embed, Colour
from discord.embeds import _EmptyEmbed
from datetime import datetime, timedelta
import random

from errors import *
from .utils import get_integers, get_name
from .game import Game, Team, Player, State

if TYPE_CHECKING:
    from discord import Message, Member
    from discord.abc import Messageable

T = TypeVar("T", bound="TableMixin")

ON_GOING_COLOR: Final[Colour] = Colour.blurple()
DONE_COLOR: Final[Colour] = Colour.green()


class TableMixin:
    """A mixin for tables."""

    @property
    def embed(self) -> Embed:
        """Returns an embed of the table.

        Returns
        -------
        Embed
            The embed of the table.
        """

        raise NotImplementedError

    @classmethod
    def from_message(cls: Type[T], message: Message) -> T:
        """Returns a table from a message.

        Parameters
        ----------
        message : Message
            The message to get the table from.

        Returns
        -------
        Table
            The table from the message.
        """

        raise NotImplementedError

    @classmethod
    async def fetch(
        cls: Type[T],
        channel: Messageable,
        limit: Optional[int] = 100,
        allow_archived: bool = False
    ) -> T:
        """Fetches a table from a channel.

        Parameters
        ----------
        channel : Messageable
            The channel to fetch the table from.
        limit : Optional[int], optional
            The limit of messages to fetch, by default 100
        allow_archived : bool, optional
            Whether to allow archived tables, by default False

        Returns
        -------
        T
            The table fetched from the channel.

        Raises
        ------
        TableNotFound
            If the table is not found.
        ArchivedTable
            If the table is archived.
        """

        async for message in channel.history(
            after=datetime.utcnow() - timedelta(minutes=60),
            limit=limit,
            oldest_first=False
        ):
            if cls._is_valid(message):
                table = cls.from_message(message)

                if table.state == State.DONE and not allow_archived:
                    raise ArchivedTable

                return table

        raise TableNotFound


    @classmethod
    def _is_valid(cls, message: Message) -> bool:
        return (
            len(message.embeds) != 0
            and cls.is_valid(message)
        )


    @staticmethod
    def is_valid(message: Message) -> bool:
        """Returns whether the message is a valid table.

        Parameters
        ----------
        message : Message
            The message to check.

        Returns
        -------
        bool
            Whether the message is a valid table.
        """

        raise NotImplementedError



class GatherTable(TableMixin):

    __slots__ = ("names", "message", "state")

    if TYPE_CHECKING:
        names: set[str]
        message: Optional[Message]
        state: State


    def __init__(
        self,
        names: set[str] = {},
        message: Optional[Message] = None,
        state: State = State.ONGOING
    ) -> None:
        self.names = names
        self.message = message
        self.state = state


    def __len__(self) -> int:
        return len(self.names)


    def add_name(self, member: Member) -> None:
        """Adds a name to the table.

        Parameters
        ----------
        member : Member
            The member to add to the table.
        """

        self.names.add(get_name(member))

        if len(self.names) == 12:
            self.state = State.DONE


    def remove_name(self, member: Member) -> None:
        """Removes a name from the table.

        Parameters
        ----------
        member : Member
            The member to remove from the table.
        """
        self.names.discard(get_name(member))


    @property
    def embed(self):
        return Embed(
            title=f"Members @{12-len(self.names)}",
            color=ON_GOING_COLOR if self.state == State.ONGOING else DONE_COLOR,
            description="\n".join(f"{i+1}. {name}" for i, name in enumerate(self.names))
        )


    @classmethod
    def from_message(cls, message):
        e = message.embeds[0].copy()
        names: set[str] = set()

        if type(e.description) is not _EmptyEmbed:
            for line in e.description.split("\n"):
                names.add(line.split(". ")[1])

        state = State.ONGOING if e.color == ON_GOING_COLOR else State.DONE

        return cls(names, message, state)

    @staticmethod
    def is_valid(message):
        e = message.embeds[0].copy()

        return (
            message.author.bot
            and e.title.startswith("Members @")
            and e.color in (ON_GOING_COLOR, DONE_COLOR)
        )


class FormatTable(TableMixin):

    __slots__ = ("data", "message", "state")

    if TYPE_CHECKING:
        data: dict[int, set[str]]
        message: Optional[Message]
        state: State


    def __init__(
        self,
        _data: dict[int, set[str]],
        message: Optional[Message] = None,
        state: State = State.ONGOING
    ) -> None:
        data = _data.copy()

        if len(set().union(*_data.values())) != 12:
            raise InvalidPlayerNum(12)

        for key in {1, 2, 3, 4, 6, -1}:
            if key not in _data.keys():
                data[key] = set()

        self.data = data
        self.message = message
        self.state = state

    @property
    def embed(self) -> Embed:
        e = Embed(title="Preferred format")
        e.color = ON_GOING_COLOR if self.state == State.ONGOING else DONE_COLOR
        e.description = "Click the buttons to vote for the format you prefer"

        name = {1: "FFA", 2: "2v2", 3: "3v3", 4: "4v4", 6: "6v6", -1: "Unvoted"}

        for k in (1, 2, 3, 4, 6, -1):
            v = self.data[k].copy()

            if not v and k != -1:
                e.add_field(name=name[k], value="> No votes", inline=False)
            elif v:
                e.add_field(name=name[k], value="> "+",".join(n for n in v), inline=False)

        return e

    @classmethod
    def from_message(cls, message):
        e = message.embeds[0].copy()
        state = State.ONGOING if e.color == ON_GOING_COLOR else State.DONE
        name = {"FFA": 1, "2v2": 2, "3v3": 3, "4v4": 4, "6v6": 6, "Unvoted":-1}
        data: dict[int, set[str]] = {}

        for field in e.fields:
            if field.value == "> No votes":
                continue
            data[name[field.name]] = set(field.value[2:].split(","))

        return cls(data, message, state)

    @staticmethod
    def is_valid(message):
        e = message.embeds[0].copy()

        return (
            message.author.bot
            and e.title == "Preferred format"
            and e.description == "Click the buttons to vote for the format you prefer"
            and e.color in (ON_GOING_COLOR, DONE_COLOR)
        )


class GameTable(TableMixin):

    __slots__ = ("_game", "message", "state")

    if TYPE_CHECKING:
        _game: Game
        message: Optional[Message]
        state: State

    def __init__(
        self,
        _game: Game,
        message: Optional[Message] = None,
        state: State = State.ONGOING
    ) -> None:
        self._game = _game
        self.message = message
        self.state = state

    @property
    def embed(self) -> Embed:
        format = {1: "FFA", 2: "2v2", 3: "3v3", 4: "4v4", 6: "6v6"}[self._game.format]
        e = Embed(title=f"Format: **{format}**")
        e.color = ON_GOING_COLOR if self.state == State.ONGOING else DONE_COLOR

        if self._game.format == 1:
            for i, p in enumerate(self._game.ranking):
                e.add_field(
                    name=f"{i+1}. {p.name} @{p.left_race_num}",
                    value=f"> {p.total_point}pt ({'-'.join(str(point) for point in p.points)})",
                    inline=False
                )
        else:
            e.description = "**Ranking\n\n**"
            for i, team in enumerate(self._game.teams):
                e.description += f"`{i+1}.` **{team.tag}**  ({team.total_point}pt)\n"
            for i, p in enumerate(self._game.ranking):
                e.add_field(
                    name=f"{i+1}. {p.name} ({p.tag}) @{p.left_race_num}",
                    value=f"> {p.total_point}pt ({'-'.join(str(point) for point in p.points)})",
                    inline=False
                )

        return e

    @classmethod
    def from_message(cls, message):
        e = message.embeds[0].copy()
        state = State.ONGOING if e.color == ON_GOING_COLOR else State.DONE
        is_ffa: bool = "FFA" in e.title
        players: list[Player] = []

        for field in e.fields:
            data = field.name.split(" ")
            payload = {
                "points": get_integers(field.value[2:].split(" ")[-1]),
                "name": field.name.split(" ")[1]
            }
            if not is_ffa:
                payload["tag"] = data[2][1]
            players.append(Player(**payload))
        if is_ffa:
            return cls(Game([Team(players=[p], tag=None) for p in players]), message, state)
        else:
            return cls(Game(Team.make_teams(players)), message, state)

    @staticmethod
    def is_valid(message):
        e = message.embeds[0].copy()

        return (
            message.author.bot
            and e.title.startswith("Format")
            and e.color in (ON_GOING_COLOR, DONE_COLOR)
        )


    @classmethod
    def initialize(cls: Type[T], format: int, names: list[str]) -> T:
        _names = names.copy()
        _tags = ["A", "B", "C", "D", "E", "F"]

        random.shuffle(_names)
        tag = _tags[:len(_names)]*format

        if format == 1:
            teams = [Team([Player(name=name,tag=None)], None) for name in _names]
            return cls(Game(teams))
        else:
            teams = Team.make_teams([Player(name=name, tag=tag) for name, tag in zip(_names, tag)])
            return cls(Game(teams))
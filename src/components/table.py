from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Type
from discord.ui import View, string_select
from discord import Embed, Colour, SelectOption
import random

from errors import *
from .utils import get_integers
from .game import Game, Team, Player

if TYPE_CHECKING:
    from discord import Message, Interaction, Member
    from discord.ui import Select, Item

T = TypeVar("T")


def get_name(member: Member) -> str:
    return member.name.replace(" ", "_")


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

    def is_valid_message(self, message: Message) -> bool:
        """Checks if a message is a valid table.

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

    __slots__ = ("names",)

    if TYPE_CHECKING:
        names: set[str]


    def __init__(self, names: set[str],) -> None:
        self.names = names


    def __len__(self) -> int:
        return len(self.names)


    @property
    def embed(self):
        return Embed(
            title="Members",
            color=Colour.blurple(),
            description="\n".join(f"{i+1}. {name}" for i, name in enumerate(self.names))
        )


    @classmethod
    def from_message(cls, message):
        e = message.embeds[0].copy()
        names: set[str] = set()

        for line in e.description.split("\n"):
            names.union(line.split(". ")[1])

        return cls(names)


class FormatTable(TableMixin):

    __slots__ = ("data",)

    if TYPE_CHECKING:
        data: dict[int, set[str]]


    def __init__(self, _data: dict[int, set[str]]) -> None:
        data = _data.copy()

        if len(set().union(*_data.values())) != 12:
            raise InvalidPlayerNum(12)

        for key in {1, 2, 3, 4, 6, -1}:
            if key not in _data.keys():
                data[key] = set()

        self.data = data

    @property
    def embed(self) -> Embed:
        e = Embed(title="Preferred format", color=Colour.blurple())
        e.description = "Click the buttons to vote for the format you prefer"

        name = {1: "FFA", 2: "2v2", 3: "3v3", 4: "4v4", 6: "6v6", -1: "Unvoted"}

        for k, v in self.data.items():
            if not v and k != -1:
                e.add_field(name=name[k], value="No votes", inline=False)
            elif v:
                e.add_field(name=name[k], value=",".join(n for n in v), inline=False)

        return e

    @classmethod
    def from_message(cls, message):
        e = message.embeds[0].copy()
        name = {"FFA": 1, "2v2": 2, "3v3": 3, "4v4": 4, "6v6": 6, "Unvoted":-1}
        data: dict[int, set[str]] = {}

        for field in e.fields:
            data[name[field.name]] = set(field.value.split(","))

        return cls(data)


class GameTable(TableMixin):

    __slots__ = ("_game",)

    if TYPE_CHECKING:
        _game: Game

    def __init__(
        self,
        _game: Game
    ) -> None:
        self._game = _game

    @property
    def embed(self) -> Embed:
        format = {1: "FFA", 2: "2v2", 3: "3v3", 4: "4v4", 6: "6v6"}[self._game.format]
        e = Embed(title=f"Format: **{format}**", color=Colour.blurple())

        if self._game.format == 1:
            for i, p in enumerate(self._game.ranking):
                e.add_field(
                    name=f"{i+1}. {p.name} @{p.left_race_num}",
                    value=f"{p.total_point}pt ({'-'.join(str(point) for point in p.points)})",
                    inline=False
                )
        else:
            e.description = "**Ranking\n\n**"
            for i, team in enumerate(self._game.teams):
                e.description += f"{i+1}. {team.tag} {team.total_point}pt\n"
            for i, p in enumerate(self._game.ranking):
                e.add_field(
                    name=f"{i+1}. {p.name} ({p.tag}) @{p.left_race_num}",
                    value=f"{p.total_point}pt ({'-'.join(str(point) for point in p.points)})",
                    inline=False
                )

        return e

    @classmethod
    def from_message(cls, message):
        e = message.embeds[0].copy()
        is_ffa: bool = "FFA" in e.title
        players: list[Player] = []

        for field in e.fields:
            data = field.value.split(" ")
            payload = {"points": get_integers(field.value.split(" ")[-1]), "name": data[1]}
            if not is_ffa:
                payload["tag"] = data[2][2]
            players.append(Player(**payload))
        if is_ffa:
            return cls(Game([Team(players=[p], tag=None) for p in players]))
        else:
            return cls(Game(Team.make_teams(players)))


    @classmethod
    def initialize(cls: Type[T], format: int, names: list[str]) -> T:
        _names = names.copy()
        _tags = ["A", "B", "C", "D", "E", "F"]

        random.shuffle(_names)
        tag = _tags[:len(_names)]*format

        if format == 1:
            return cls(Game(Team.make_teams([Player(name=name, tag=None) for name in _names])))
        else:
            teams = Team.make_teams([Player(name=name, tag=tag) for name, tag in zip(_names, tag)])
            return cls(Game(teams))


class FormatView(View):

    def __init__(self) -> None:
        super().__init__(
            timeout=None,
            disable_on_timeout=True
        )


    @string_select(
        custom_id="format",
        placeholder="Select your preferred format",
        options=[
            SelectOption(label="FFA", value=1),
            SelectOption(label="2v2", value=2),
            SelectOption(label="3v3", value=3),
            SelectOption(label="4v4", value=4),
            SelectOption(label="6v6", value=6)
        ]
    )
    async def select_format(
        self,
        select: Select,
        interaction: Interaction
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        table = FormatTable.from_message(interaction.message)

        for k in {1, 2, 3, 4, 6, -1}:
            table.data[k].difference_update(get_name(interaction.user.name))

        table.data[select.values[0]].update(get_name(interaction.user.name))
        await interaction.message.edit(embed=table.embed, view=FormatView())
        await interaction.followup.send(
            "Your vote has been recorded" if interaction.locale != 'ja' else '投票が記録されました',
            ephemeral=True
        )

        if not table.data[-1]:
            format = max(table.data, key=lambda x: len(table.data[x]))
            await interaction.followup.send(embed=GameTable.initialize(format, set().union(*table.data.values())).embed, ephemeral=False)
            await self.message.edit(view=None)


    async def interaction_check(self, interaction: Interaction):
        table = FormatTable.from_message(interaction.message)
        return get_name(interaction.user.name)  not in set().union(*table.data.values())


    async def on_check_failure(self, interaction: Interaction):
        await interaction.response.send_message(
            "You cannot vote." if interaction.locale != 'ja' else '投票する権限がありません。',
            ephemeral=True
        )

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)


    async def on_error(self, error: Exception, item: Item, interaction: Interaction):
        if isinstance(error, MyError):
            if interaction.response.is_done():
                await interaction.followup.send(
                    error.localize(interaction.locale),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    error.localize(interaction.locale),
                    ephemeral=True
                )
            return

        raise error
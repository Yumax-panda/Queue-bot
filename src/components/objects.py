from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Type
from discord.ui import View, string_select
from discord import Embed, Colour, SelectOption
from discord.utils import raw_mentions
import random

from errors import *

if TYPE_CHECKING:
    from discord import Message, Interaction
    from discord.ui import Select

T = TypeVar("T")


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

    __slots__ = ("ids",)

    if TYPE_CHECKING:
        ids: set[int]


    def __init__(self, ids: set[int],) -> None:
        self.ids = ids


    def __len__(self) -> int:
        return len(self.ids)


    @property
    def embed(self):
        return Embed(
            title="Members",
            color=Colour.blurple(),
            description="\n".join(f"{i+1}. <@{id}>" for i, id in enumerate(self.ids))
        )


    @classmethod
    def from_message(cls, message):
        return cls(set(raw_mentions(message.embeds[0].description)))


class FormatTable(TableMixin):

    __slots__ = ("data",)

    if TYPE_CHECKING:
        data: dict[int, set[int]]


    def __init__(self, _data: dict[int, set[int]]) -> None:
        data = _data.copy()

        if len(set().union(*data.values())) != 12:
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
            else:
                e.add_field(name=name[k], value=",".join(f"<@{id}>" for id in v), inline=False)

        return e

    @classmethod
    def from_message(cls, message):
        e = message.embeds[0].copy()
        name = {"FFA": 1, "2v2": 2, "3v3": 3, "4v4": 4, "6v6": 6, "Unvoted":-1}
        return cls(
            {name[e.fields[i].name]: set(raw_mentions(e.fields[i].value)) for i in range(len(e.fields))}
        )


def make_teams(format: int, ids: set[int]) -> Embed:

    if len(ids) != 12:
        raise InvalidPlayerNum(12)

    tags = ("A", "B", "C", "D", "E", "F")
    _ids = list(ids)

    indexes = list(range(12))
    random.shuffle(indexes)
    teams = [[_ids[index] for index in indexes[i:i+format]]for i in range(0, 12, format)]
    f = {1: "FFA", 2: "2v2", 3: "3v3", 4: "4v4", 6: "6v6"}
    e = Embed(title=f"Format: **{f[format]}**", color=Colour.blurple())

    for i, team in enumerate(teams):
        e.add_field(name=f"Team {tags[i]}", value="\n".join(f"<@{id}>" for id in team), inline=False)

    return e



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
            table.data[k].difference_update(interaction.user.id)

        table.data[select.values[0]].update(interaction.user.id)
        await interaction.message.edit(embed=table.embed, view=FormatView())
        await interaction.followup.send(
            "Your vote has been recorded" if interaction.locale != 'ja' else '投票が記録されました',
            ephemeral=True
        )

        if not table.data[-1]:
            format = max(table.data, key=lambda x: len(table.data[x]))
            await interaction.followup.send(embed=make_teams(format, set().union(*table.data.values())), ephemeral=False)
            self.stop()
            await self.message.edit(view=None)
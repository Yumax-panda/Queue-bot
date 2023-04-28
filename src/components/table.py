from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Type
from discord.ui import View
from discord import Embed, Colour
from discord.utils import raw_mentions

if TYPE_CHECKING:
    from discord import Message

G = TypeVar("G", bound="GatherTable")


class GatherTable:

    __slots__ = ("ids",)

    if TYPE_CHECKING:
        ids: set[int]


    def __init__(self, ids: set[int],) -> None:
        self.ids = ids


    def __len__(self) -> int:
        return len(self.ids)


    @property
    def embed(self) -> Embed:
        """Returns an embed of the table.

        Returns
        -------
        Embed
            The embed of the table.
        """
        return Embed(
            title="Members",
            color=Colour.blurple(),
            description="\n".join(f"{i+1}. <@{id}>" for i, id in enumerate(self.ids))
        )


    @classmethod
    def from_message(cls: Type[G], message: Message) -> G:
        """Returns a GatherTable from a message.

        Parameters
        ----------
        message : Message
            The message to get the table from.

        Returns
        -------
        GatherTable
            The table from the message.
        """

        return cls(set(raw_mentions(message.embeds[0].description)))


class GatherView(View):

    def __init__(self) -> None:
        super().__init__(timeout=None)
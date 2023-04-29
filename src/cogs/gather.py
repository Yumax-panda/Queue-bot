from __future__ import annotations
from typing import TYPE_CHECKING
from discord.utils import raw_mentions
from discord.ext import commands
from discord import Member

from errors import *
from components.view import GatherView, FormatView
from components.table import GatherTable, FormatTable, GameTable
from components.utils import get_name, get_integers


if TYPE_CHECKING:
    from discord import Message
    from bot import QueueBot


class Gather(commands.Cog, name="Gather"):

    def __init__(self, bot: QueueBot) -> None:
        self.bot: QueueBot = bot


    @commands.command()
    @commands.guild_only()
    async def start(self, ctx: commands.Context) -> None:
        await ctx.send(
            embed=GatherTable({get_name(ctx.author)}).embed,
            view=GatherView()
        )


    @commands.command(aliases=['c'])
    @commands.guild_only()
    async def can(self, ctx: commands.Context, members: commands.Greedy[Member] = []) -> None:
        table = await GatherTable.fetch(ctx.channel)
        _members = members or [ctx.author]

        if len(_members) + len(table.names) > 12:
            raise InvalidPlayerNum

        for m in _members:
            table.add_name(m)

        await ctx.send(f"{', '.join(m.mention for m in _members)} has joined the game. (@{12-len(table.names)})")

        if not table.state:
            await table.message.edit(embed=table.embed, view=None)
            await ctx.send(embed=FormatTable({-1:table.names}).embed, view=FormatView())
        else:
            await table.message.edit(embed=table.embed)


    @commands.command(aliases=['a', "add"])
    @commands.guild_only()
    async def add_rank(
        self,
        ctx: commands.Context,
        rank: int,
        target: Optional[Member] = None,
    ) -> None:
        table = await GameTable.fetch(ctx.channel)
        table._game.get_player(get_name(target or ctx.author)).add_rank(rank)
        await table.message.edit(embed=table.embed)
        await ctx.send("順位を追加しました。")


    @commands.command(aliases=['r', "remove", "b"])
    @commands.guild_only()
    async def back(self, ctx: commands.Context) -> None:
        table = await GameTable.fetch(ctx.channel)
        table._game.get_player(get_name(ctx.author)).remove_rank()
        await table.message.edit(embed=table.embed)
        await ctx.send("順位を削除しました。")


def setup(bot: QueueBot):
    bot.add_cog(Gather(bot))
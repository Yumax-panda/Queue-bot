from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from discord.ext import commands
from discord import Member

from components.view import GatherView, FormatView
from components.table import GatherTable, FormatTable, GameTable


if TYPE_CHECKING:
    from bot import QueueBot


class Gather(commands.Cog, name="Gather"):

    def __init__(self, bot: QueueBot) -> None:
        self.bot: QueueBot = bot


    @commands.command()
    @commands.guild_only()
    async def start(self, ctx: commands.Context) -> None:
        await ctx.send(
            "Starting a gather...",
            embed=GatherTable({ctx.author.name.replace(" ", "_")}).embed,
            view=GatherView()
        )


    @commands.command()
    @commands.guild_only()
    async def can(self, ctx: commands.Context, member: Optional[Member] = None) -> None:
        table = await GatherTable.fetch(ctx.channel)
        table.add_name(member if member is not None else ctx.author)

        if not table.state:
            await table.message.edit(embed=table.embed, view=None)
            await ctx.send(embed=FormatTable({-1:table.names}).embed, view=FormatView())
        else:
            await table.message.edit(embed=table.embed)


def setup(bot: QueueBot):
    bot.add_cog(Gather(bot))
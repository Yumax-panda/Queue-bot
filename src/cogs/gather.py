from __future__ import annotations
from typing import TYPE_CHECKING
from discord.ext import commands
from discord import Member, DMChannel

from errors import *
from components.view import GatherView, FormatView, GameView, ResumeView
from components.table import GatherTable, FormatTable, GameTable
from components.utils import get_name


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

        if table.is_done:
            await ctx.send(embed=FormatTable({-1:table.names}).embed, view=FormatView())
            await table.message.edit(embed=table.embed, view=None)
        else:
            await table.message.edit(embed=table.embed)

        await ctx.send(f"{', '.join(m.mention for m in _members)} has joined the game. (@{12-len(table.names)})")


    @commands.command(aliases=['d'])
    @commands.guild_only()
    async def drop(self, ctx: commands.Context, members: commands.Greedy[Member] = []) -> None:
        table = await GatherTable.fetch(ctx.channel)
        _members = members or [ctx.author]

        for m in _members:
            table.remove_name(m)

        await table.message.edit(embed=table.embed)
        await ctx.send(f"{', '.join(m.mention for m in _members)} has dropped the game. (@{12-len(table.names)})")


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
        await ctx.send(embed=table.embed, view=GameView())
        await table.message.delete()


    @commands.command(aliases=['r', "remove", "b"])
    @commands.guild_only()
    async def back(self, ctx: commands.Context) -> None:
        table = await GameTable.fetch(ctx.channel)
        table._game.get_player(get_name(ctx.author)).remove_rank()
        await ctx.send(embed=table.embed, view=GameView())
        await table.message.delete()


    @commands.command()
    @commands.guild_only()
    async def edit(
        self,
        ctx: commands.Context,
        _index: int,
        rank: int,
    ) -> None:
        table = await GameTable.fetch(ctx.channel)
        table._game.get_player(get_name(ctx.author)).edit_rank(rank, _index-1)
        await table.message.edit(embed=table.embed)
        await ctx.send("Edit complete.")


    @commands.command()
    @commands.guild_only()
    async def end(self, ctx: commands.Context) -> None:
        table = await GameTable.fetch(ctx.channel)
        table.is_done = True
        await table.message.edit(embed=table.embed, view=ResumeView())
        await ctx.send("Finished the game.")


    @commands.command()
    @commands.guild_only()
    async def resume(self, ctx: commands.Context) -> None:
        table = await GameTable.fetch(ctx.channel)
        table.is_done = False
        await table.message.edit(embed=table.embed, view=GameView())
        await ctx.send("Resumed the game.")


    @commands.Cog.listener("on_message")
    async def _shorthand_command(self, message: Message) -> None:
        """This is a shorthand command for adding (removing) ranks to the game.

        Parameters
        ----------
        message : Message
            The message to be processed.
        """

        if (
            message.author.bot
            or isinstance(message.channel, DMChannel)
        ):
            return
        if not (
            message.content in map(str, range(1, 13))
            or message.content in ("back", "b")
        ):
            return

        try:
            table = await GameTable.fetch(message.channel)

            if message.content in ("back", "b"):
                table._game.get_player(get_name(message.author)).remove_rank()
            else:
                table._game.get_player(get_name(message.author)).add_rank(int(message.content))

            await message.channel.send(embed=table.embed, view=GameView())
            await table.message.delete()

        except MyError:
            return


def setup(bot: QueueBot):
    bot.add_cog(Gather(bot))
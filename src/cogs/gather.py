from typing import TYPE_CHECKING
from discord.ext import commands
from discord import (
    Member,
    Option,
    DMChannel,
    SlashCommandGroup,
    ApplicationContext
)

from errors import *
from components.view import GatherView, FormatView, GameView, ResumeView
from components.table import GatherTable, FormatTable, GameTable
from components.utils import get_name


if TYPE_CHECKING:
    from discord import Message
    from bot import QueueBot


class Gather(commands.Cog, name="Gather"):

    def __init__(self, bot: "QueueBot") -> None:
        self.bot: QueueBot = bot

    game = SlashCommandGroup(name="game", description="Game related commands")
    race = game.create_subgroup(name="race")


    @commands.command()
    @commands.guild_only()
    async def start(self, ctx: commands.Context) -> None:
        await ctx.send(
            embed=GatherTable({get_name(ctx.author)}).embed,
            view=GatherView()
        )


    @game.command(
        name="start",
        description="Call for participants in the game",
        description_localizations={"ja": "ゲームの参加者を募集"}
    )
    @commands.guild_only()
    async def game_start(self, ctx: ApplicationContext) -> None:
        await ctx.response.defer()
        await ctx.respond(
            content = "参加者の募集を開始します。" if ctx.locale=="ja" else "Starting to gather participants.",
            embed=GatherTable({get_name(ctx.user)}).embed,
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

        if table.is_done:
            await ctx.send(embed=FormatTable({-1:table.names}).embed, view=FormatView())
            await table.message.edit(embed=table.embed, view=None)
        else:
            await table.message.edit(embed=table.embed)


    @game.command(
        name="can",
        description="Join the game",
        description_localizations={"ja": "ゲームに参加する"}
    )
    @commands.guild_only()
    async def game_can(
        self,
        ctx: ApplicationContext,
        member: Option(
            Member,
            name="member",
            name_localizations={"ja": "メンバー"},
            description="The member to join the game",
            description_localizations={"ja": "ゲームに参加するメンバー"},
            default=None,
            required=False
        )
    ) -> None:
        await ctx.response.defer()
        _member: Member = member or ctx.user
        table = await GatherTable.fetch(ctx.channel)
        table.add_name(_member)

        await ctx.respond(
            f"{_member.name}さんがゲームに参加しました。" if ctx.locale=="ja" else f"{_member.name} has joined the game.",
        )

        if table.is_done:
            await ctx.respond(embed=FormatTable({-1:table.names}).embed, view=FormatView())
            await table.message.edit(embed=table.embed, view=None)
        else:
            await table.message.edit(embed=table.embed)


    @commands.command(aliases=['d'])
    @commands.guild_only()
    async def drop(self, ctx: commands.Context, members: commands.Greedy[Member] = []) -> None:
        table = await GatherTable.fetch(ctx.channel)
        _members = members or [ctx.author]

        for m in _members:
            table.remove_name(m)

        await table.message.edit(embed=table.embed)
        await ctx.send(f"{', '.join(m.mention for m in _members)} has dropped the game. (@{12-len(table.names)})")


    @game.command(
        name="drop",
        description="Drop the game",
        description_localizations={"ja": "ゲームの参加を取り消す"}
    )
    @commands.guild_only()
    async def game_drop(
        self,
        ctx: ApplicationContext,
        member: Option(
            Member,
            name="member",
            name_localizations={"ja": "メンバー"},
            description="The member to drop the game",
            description_localizations={"ja": "ゲームから抜けるメンバー"},
            default=None,
            required=False
        )
    ) -> None:
        await ctx.response.defer()
        _member: Member = member or ctx.user
        table = await GatherTable.fetch(ctx.channel)
        table.remove_name(_member)
        await table.message.edit(embed=table.embed)
        await ctx.respond(
            f"{_member.name}さんがゲームから抜けました。" if ctx.locale=="ja" else f"{_member.name} has dropped the game.",
        )


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


    @race.command(
        name="add",
        description="Register your race standings",
        description_localizations={"ja": "レースの順位を登録する"}
    )
    @commands.guild_only()
    async def game_race_add(
        self,
        ctx: ApplicationContext,
        rank: Option(
            int,
            name="rank",
            name_localizations={"ja": "順位"},
            description="The rank to register",
            description_localizations={"ja": "登録する順位"},
            required=True,
            min_value=1,
            max_value=12
        ),
        number: Option(
            int,
            name="race_number",
            name_localizations={"ja": "レース番号"},
            description="If no input, then the last race.",
            description_localizations={"ja": "設定しないと最後のレースになります"},
            required=False,
            min_value=1,
            max_value=12,
            default=12
        )
    ) -> None:
        await ctx.response.defer()
        table = await GameTable.fetch(ctx.channel)
        table._game.get_player(get_name(ctx.user)).add_rank(rank, number)
        await ctx.respond(embed=table.embed, view=GameView())
        await table.message.delete()


    @commands.command(aliases=['r', "remove", "b"])
    @commands.guild_only()
    async def back(self, ctx: commands.Context) -> None:
        table = await GameTable.fetch(ctx.channel)
        table._game.get_player(get_name(ctx.author)).remove_rank()
        await ctx.send(embed=table.embed, view=GameView())
        await table.message.delete()


    @race.command(
        name="back",
        description="Back one race",
        description_localizations={"ja": "レースを一つ戻す"}
    )
    @commands.guild_only()
    async def game_race_back(
        self,
        ctx: ApplicationContext,
        number: Option(
            int,
            name="race_number",
            name_localizations={"ja": "レース番号"},
            description="If no input, then the last race.",
            description_localizations={"ja": "設定しないと最後のレースになります"},
            required=False,
            min_value=1,
            max_value=12,
            default=0
        )
    ) -> None:
        await ctx.response.defer()
        table = await GameTable.fetch(ctx.channel)
        table._game.get_player(get_name(ctx.author)).remove_rank(number-1)
        await ctx.respond(embed=table.embed, view=GameView())
        await table.message.delete()


    @commands.command()
    @commands.guild_only()
    async def edit(
        self,
        ctx: commands.Context,
        rank: int,
        _index: int = 0,
    ) -> None:
        table = await GameTable.fetch(ctx.channel)
        table._game.get_player(get_name(ctx.author)).edit_rank(rank, _index-1)
        await table.message.edit(embed=table.embed)
        await ctx.send("Edit complete.")


    @race.command(
        name="edit",
        description="Edit the race",
        description_localizations={"ja": "レースを編集する"}
    )
    @commands.guild_only()
    async def game_race_edit(
        self,
        ctx: ApplicationContext,
        rank: Option(
            int,
            name="rank",
            name_localizations={"ja": "順位"},
            description="The rank to register",
            description_localizations={"ja": "登録する順位"},
            required=True,
            min_value=1,
            max_value=12
        ),
        number: Option(
            int,
            name="race_number",
            name_localizations={"ja": "レース番号"},
            description="If no input, then the last race.",
            description_localizations={"ja": "設定しないと最後のレースになります"},
            required=False,
            min_value=1,
            max_value=12,
            default=0
        )
    ) -> None:
        await ctx.response.defer()
        table = await GameTable.fetch(ctx.channel)
        table._game.get_player(get_name(ctx.author)).edit_rank(rank, number-1)
        await table.message.edit(embed=table.embed)
        await ctx.respond("レースを編集しました。" if ctx.locale == "ja" else "Edit complete.")


    @commands.command()
    @commands.guild_only()
    async def end(self, ctx: commands.Context) -> None:
        table = await GameTable.fetch(ctx.channel)
        table.is_done = True
        await table.message.edit(embed=table.embed, view=ResumeView())
        await ctx.send("Finished the game.")


    @game.command(
        name="end",
        description="End the game",
        description_localizations={"ja": "ゲームを終了する"}
    )
    @commands.guild_only()
    async def game_end(self, ctx: ApplicationContext) -> None:
        await ctx.response.defer()
        table = await GameTable.fetch(ctx.channel)
        table.is_done = True
        await table.message.edit(embed=table.embed, view=ResumeView())
        await ctx.respond("ゲームを終了しました。" if ctx.locale == "ja" else "Finished the game.")


    @commands.command()
    @commands.guild_only()
    async def resume(self, ctx: commands.Context) -> None:
        table = await GameTable.fetch(ctx.channel, allow_archived=True)
        table.is_done = False
        await table.message.edit(embed=table.embed, view=GameView())
        await ctx.send("Resumed the game.")


    @game.command(
        name="resume",
        description="Resume the game",
        description_localizations={"ja": "ゲームを再開する"}
    )
    @commands.guild_only()
    async def game_resume(self, ctx: ApplicationContext) -> None:
        await ctx.response.defer()
        table = await GameTable.fetch(ctx.channel, allow_archived=True)
        table.is_done = False
        await table.message.edit(embed=table.embed, view=GameView())
        await ctx.respond("ゲームを再開しました。" if ctx.locale == "ja" else "Resumed the game.")


    @commands.Cog.listener("on_message")
    async def _shorthand_command(self, message: "Message") -> None:
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


def setup(bot: "QueueBot"):
    bot.add_cog(Gather(bot))
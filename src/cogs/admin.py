from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from traceback import print_exception
from io import StringIO
import sys

from discord.ext import commands
from discord.utils import get
from discord import (
    File,
    Embed,
    EmbedField,
    CheckFailure,
    ApplicationContext,
    ApplicationCommandError
)

from errors import *

DEBUG: bool = True # If you want to debug, set this to True

if TYPE_CHECKING:
    from bot import QueueBot


class Admin(commands.Cog, name="Admin", command_attrs=dict(hidden=True)):

    def __init__(self, bot: QueueBot) -> None:
        self.bot: QueueBot = bot
        self.is_public: bool = False
        self.description: str = "Admin commands"
        self.description_localizations: dict[str, str] = {
            "ja": "管理者用コマンド",
            "en-US": "Admin commands"
        }


    async def send_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        e = Embed(
            title = error.__class__.__name__,
            description = f'```{error}```',
            fields=[
                EmbedField(
                    name='Command name',
                    value=ctx.command.name,
                    inline=False,
                ),
                EmbedField(
                    name='content',
                    value=f'```{ctx.message.content}```',
                    inline=False
                ),
                EmbedField(
                    name='Channel',
                    value=f'{ctx.channel.name} (`{ctx.channel.id}`)',
                    inline=False
                )
            ]
        )
        e.set_author(name=str(ctx.author), icon_url=ctx.author.display_avatar.url)
        buffer = StringIO()
        t, _, tb = sys.exc_info()
        print_exception(t, error, tb, file=buffer)
        buffer.seek(0)
        await self.bot.LOG_CHANNEL.send(embed=e, file=File(fp=buffer, filename='traceback.txt'))
        buffer.close()


    async def send_app_error(self, ctx: ApplicationContext, error: ApplicationCommandError) -> None:
        e = Embed(
            title = error.__class__.__name__,
            description = f'```{error}```',
            fields=[
                EmbedField(
                    name='Command name',
                    value=ctx.command.qualified_name,
                    inline=False,
                ),
                EmbedField(
                    name='Inputs',
                    value=f'```{ctx.selected_options}```',
                    inline=False
                ),
                EmbedField(
                    name='Channel',
                    value=f'{ctx.channel.name} (`{ctx.channel.id}`)',
                    inline=False
                )
            ]
        )
        e.set_author(name=str(ctx.user), icon_url=ctx.user.display_avatar.url)
        buffer = StringIO()
        t, _, tb = sys.exc_info()
        print_exception(t, error, tb, file=buffer)
        buffer.seek(0)
        await self.bot.LOG_CHANNEL.send(embed=e, file=File(fp=buffer, filename='traceback.txt'))
        buffer.close()


    @commands.command(
        name='user',
        aliases=['u'],
        description='Show user info',
        brief = 'ユーザー情報を表示',
        usage = '!user <ID or name>',
        hidden = True
    )
    @commands.is_owner()
    async def user(self, ctx: commands.Context, user_id: Optional[int] = 0, name: Optional[str] = '') -> None:

        if (user := get(self.bot.users, name=name) or get(self.bot.users, id=user_id)) is None:
            raise NotFoundError

        e = Embed(title=str(user), description='参加サーバー\n')
        e.set_author(name=str(user.id), icon_url=user.display_avatar.url)

        for g in user.mutual_guilds:
            e.description += f'{g.name} (`{g.id}`)\n'

        await self.bot.LOG_CHANNEL.send(embed=e)


    @commands.Cog.listener("on_command_error")
    async def command_error_handler(self, ctx: commands.Context, error: commands.CommandError) -> None:
        content: Optional[str] = None

        if isinstance(error, MyError):
            content = error.localize()
        elif isinstance(error, commands.NoPrivateMessage):
            content = 'DMでこのコマンドは使えません。\nThis command is not available in DM channels.'
        elif isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.NotOwner):
            content = 'これは管理者専用コマンドです。\nThis command is only for owner.'
        elif isinstance(error, commands.UserInputError):
            content = f'コマンドの入力が不正です。\n{ctx.command.usage}'
        elif isinstance(error, commands.BotMissingPermissions):
            content = f'このコマンドを使うにはBotへ以下の権限のください。\n\
                In order to invoke this command, please give me the following permissions\n\
                **{", ".join(error.missing_permissions)}**'
        elif isinstance(error, commands.CheckFailure):
            return

        if content is not None:
            await ctx.send(content)
            return

        if DEBUG:
            raise error
        else:
            await self.send_command_error(ctx, error)
            await ctx.send('予期しないエラーが発生しました。\nUnexpected error raised.')


    @commands.Cog.listener('on_application_command_error')
    async def app_error_handler(self, ctx: ApplicationContext, error: ApplicationCommandError) -> None:
        content: Optional[str] = None

        if isinstance(error, MyError):
            content = error.localize(ctx.locale)
        elif isinstance(error, commands.NoPrivateMessage):
            content = {'ja': 'DMでこのコマンドは使えません。'}.get(ctx.locale, 'This command is not available in DM channels.')
        elif isinstance(error, CheckFailure):
            content = {'ja': 'このコマンドは無効です。'}.get(ctx.locale, 'This command is not available.')

        if content is not None:
            await ctx.respond(content, ephemeral=True)
            return

        if DEBUG:
            raise error
        else:
            await self.send_app_error(ctx, error)
            await ctx.respond({'ja': '予期しないエラーが発生しました。'}.get(ctx.locale, 'Unexpected error raised.'))
            await ctx.interaction.delete_original_response()


def setup(bot: QueueBot) -> None:
    bot.add_cog(Admin(bot))
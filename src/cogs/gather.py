from __future__ import annotations
from typing import TYPE_CHECKING
from discord.ext import commands


if TYPE_CHECKING:
    from bot import QueueBot


class Gather(commands.Cog, name="Gather"):

    def __init__(self, bot: QueueBot) -> None:
        self.bot: QueueBot = bot


def setup(bot: QueueBot):
    bot.add_cog(Gather(bot))
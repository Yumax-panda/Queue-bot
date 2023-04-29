from discord.ext import commands
import discord
import os

from components.view import GatherView, FormatView, GameView

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

extensions = [
    "cogs.admin",
    "cogs.gather",
]

class QueueBot(commands.Bot):

    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or('$'),
            case_insensitive=True,
            intents = intents
        )
        self.LOG_CHANNEL: discord.TextChannel = None

    async def on_ready(self):

        for view in (
            GatherView,
            FormatView,
            GameView
        ):
            self.add_view(view())

        self.LOG_CHANNEL = self.get_channel(int(os.environ["LOG_CHANNEL_ID"]))
        print("Bot is ready!")

bot = QueueBot()
bot.load_extensions(*extensions)
bot.run(os.environ["BOT_TOKEN"])


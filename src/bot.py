from discord.ext import commands
import discord
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

extensions = [
    "cogs.gather",
]

class QueueBot(commands.Bot):

    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or('$'),
            case_insensitive=True,
            intents = intents
        )

    async def on_ready(self):
        print("Bot is ready!")

bot = QueueBot()
bot.load_extensions(*extensions)
bot.run(os.environ["BOT_TOKEN"])


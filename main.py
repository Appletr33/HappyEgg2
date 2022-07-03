from discord.ext import commands
from utils.database import Database
import asyncpg
import traceback
import sys
import discord
import os

initial_extensions = (
    'cogs.hypixelstats',
    'cogs.errorhandler',
    'cogs.help',
    'cogs.musicplayer'
)


class Bot(commands.Bot):

    def __init__(self):
        commands.Bot.__init__(self, command_prefix=["egg ", "egg", " egg", "egg  ", "Egg", "Egg "])
        self.db = Database()

    async def on_ready(self):
        await self.db.pool_connect_to_db()
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="egg help"))
        bot.remove_command('help')

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f"Failed to load extension {extension}.", file=sys.stderr)
                traceback.print_exc()

        print("\n[INFO]: Bot Is Now Online")
        print(f"\n\n[INFO]: Bot is in {len(bot.guilds)} servers:")
        for guild in bot.guilds:
            print(f"\t{guild}\t {guild.id}")


bot = Bot()
bot.run(os.environ["DISCORD_TOKEN"])


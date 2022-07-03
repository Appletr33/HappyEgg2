from discord import FFmpegPCMAudio
from discord.ext import commands
from itertools import cycle
from os import walk
import asyncio

import utils.errors as errors


class MusicPlayer(commands.Cog):
    """Music Commands"""

    def __init__(self, bot):
        self.bot = bot
        self.voices = self.get_voices()
        self.songs = cycle(self.get_songs())

    def get_voices(self):
        voices = {}
        for guild in self.bot.guilds:
            voices[guild] = {'voice': guild.voice_client, 'playing': False, 'plays': 0}

        return voices

    @staticmethod
    def get_songs():
        songs_names = next(walk('Music/Christmas/'))

        songs = []
        for song_name in songs_names[2]:
            songs.append(songs_names[0] + song_name)

        return songs

    @commands.command(help="Use <join> to get happy egg to join the channel your in")
    async def join(self, ctx):
        try:
            channel = ctx.message.author.voice.channel
        except AttributeError:
            raise errors.NotInVoiceChannel()

        if channel is None:
            raise errors.NotInVoiceChannel()

        self.voices[ctx.guild]['voice'] = ctx.guild.voice_client
        if self.voices[ctx.guild]['voice'] is not None and self.voices[ctx.guild]['voice'].is_connected():
            await self.voices[ctx.message.guild]['voice'].move_to(channel)
        else:
            await channel.connect()

        self.voices[ctx.message.guild]['voice'] = ctx.message.guild.voice_client

        if not self.voices[ctx.message.guild]['playing']:
            self.voices[ctx.message.guild]['playing'] = True
            player = FFmpegPCMAudio(next(self.songs))
            self.voices[ctx.message.guild]['voice'].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.after_play(ctx.message.guild), self.bot.loop))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel:
            if len(before.channel.members) < 2 and self.voices[member.guild]['playing'] and self.voices[member.guild]['voice'] and member.id != 812506337644511253:
                self.voices[member.guild]['playing'] = False
                self.voices[member.guild]['voice'] = member.guild.voice_client
                self.voices[member.guild]['voice'].stop()
                await self.voices[member.guild]['voice'].disconnect()

        if before.channel is None and after.channel is not None and self.voices[member.guild]['playing'] is False and member.id != 812506337644511253:
            self.voices[member.guild]['playing'] = True
            await after.channel.connect()
            self.voices[member.guild]['voice'] = member.guild.voice_client
            player = FFmpegPCMAudio(next(self.songs))
            self.voices[member.guild]['voice'].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.after_play(member.guild), self.bot.loop))

    async def after_play(self, guild):
        self.voices[guild]['voice'] = guild.voice_client
        player = FFmpegPCMAudio(next(self.songs))
        self.voices[guild]['voice'].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.after_play(guild=guild), self.bot.loop))


def setup(bot):
    bot.add_cog(MusicPlayer(bot))

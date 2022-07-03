from discord.ext import commands, tasks
from discord import embeds, Color
from discord import client
import discord
import traceback
import sys
import utils.errors as errors


class CommandErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
             Parameters
             ------------
             ctx: commands.Context
                 The context used for command invocation.
             error: commands.CommandError
                 The Exception raised.
             """
        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound,)
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':
                await ctx.send()
            embed = embeds.Embed(title="**Something Went Wrong**",
                                 description=f'Please pass in correct arguments!', color=Color.red())
            await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = embeds.Embed(title="**Something Went Wrong**", description=f'Please pass in all required arguments!', color=Color.red())
            await ctx.send(embed=embed)

        elif isinstance(error, commands.CommandOnCooldown):
            embed = embeds.Embed(title="**Something Went Wrong**", description=f'This command is on cooldown ~{error.retry_after:.2f}s.', color=Color.red())
            await ctx.send(embed=embed)

        elif isinstance(error, errors.InvalidUUID):
            embed = embeds.Embed(title="**Something Went Wrong**", description=f"Sorry, this account does not exist or is not being monitored {error.param!r}. Try using the `add <minecraft account name>` command if you're sure {error.param!r} exists.", color=Color.red())
            await ctx.send(embed=embed)

        elif isinstance(error, errors.AlreadyMonitored):
            embed = embeds.Embed(title="**Something Went Wrong**", description=f'Sorry, this account is already being monitored {error.param!r}.', color=Color.red())
            await ctx.send(embed=embed)

        elif isinstance(error, errors.NotMonitoring):
            embed = embeds.Embed(title="**Something Went Wrong**", description=f"Sorry, but you are not currently monitoring any accounts. Use the 'Add <account name>' command to monitor an account", color=Color.red())
            await ctx.send(embed=embed)

        elif isinstance(error, errors.TooManyAccounts):
            embed = embeds.Embed(title="**Something Went Wrong**", description=f"Sorry, but you cannot monitor an account. There can only be up to 18 accounts at a time being monitored due to API restrictions. Simply, ask someone for their spot.", color=Color.red())
            await ctx.send(embed=embed)

        elif isinstance(error, errors.AccountAlreadyMonitoring):
            embed = embeds.Embed(title="**Something Went Wrong**", description=f"Sorry, you're already monitoring {error.param!r}! Use"
                                                                f" the 'Remove' command to have the ability to monitor a"
                                                                f" different account.", color=Color.red())
            await ctx.send(embed=embed)

        elif isinstance(error, errors.InvalidTime):
            embed = embeds.Embed(title="**Something Went Wrong**", description=f"Sorry, but you can only request `data 1 <minecraft account name> or data 7 <minecraft account name>` not {error.param!r}!", color=Color.red())
            await ctx.send(embed=embed)

        elif isinstance(error, errors.NotInVoiceChannel):
            embed = embeds.Embed(title="**Something Went Wrong**", description=f"Sorry, but you must be in a voice channel`", color=Color.red())
            await ctx.send(embed=embed)

        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))

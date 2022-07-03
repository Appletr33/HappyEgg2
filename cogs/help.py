import discord
from discord.ext import commands
from discord.errors import Forbidden


async def send_embed(ctx, embed):
    try:
        await ctx.send(embed=embed)
    except Forbidden:
        try:
            await ctx.send("My permissions seem to not allow me to send embeds. :(")
        except Forbidden:
            await ctx.author.send(
                f"Hey, My permissions don't allow me to send messages on {ctx.channel.name} on {ctx.guild.name}\n"
                f"Please inform the server admin about this issue. Thanks!", embed=embed)


class Help(commands.Cog):
    """Sends this help message"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, *input):
        """Shows all modules of that bot"""
        prefix = "egg"
        owner = 389148125681418247
        owner_name = "Xander#5341"

        # checks if cog parameter was given
        # if not: sending all modules and commands not associated with a cog
        if not input:
            # checks if owner is on this server - used to 'tag' owner
            try:
                owner = ctx.guild.get_member(owner).mention

            except AttributeError as e:
                owner = owner

            # starting to build embed
            emb = discord.Embed(title='Commands and modules', color=discord.Color.blue(),
                                description=f'Use `{prefix} help <module>` to gain more information about that module '
                                            f'\n')

            # iterating trough cogs, gathering descriptions
            cogs_desc = ''
            for cog in self.bot.cogs:
                if cog != "CommandErrorHandler":
                    cogs_desc += f'`{cog}` {self.bot.cogs[cog].__doc__}\n'

            # adding 'list' of cogs to embed
            emb.add_field(name='Modules', value=cogs_desc, inline=False)

            # integrating trough uncategorized commands
            commands_desc = ''
            for command in self.bot.walk_commands():
                # if cog not in a cog
                # listing command if cog name is None and command isn't hidden
                if not command.cog_name and not command.hidden:
                    commands_desc += f'{command.name} - {command.help}\n'

            # adding those commands to embed
            if commands_desc:
                emb.add_field(name='Not belonging to a module', value=commands_desc, inline=False)

            # setting information about author
            emb.add_field(name="About", value=f"The Bots is developed by {owner_name}.\n")

        # block called when one cog-name is given
        # trying to find matching cog and it's commands
        elif len(input) == 1:

            # iterating trough cogs
            for cog in self.bot.cogs:
                if cog != "CommandErrorHandler":
                    # check if cog is the matching one
                    if cog.lower() == input[0].lower():

                        # making title - getting description from doc-string below class
                        emb = discord.Embed(title=f'{cog} - Commands', description=self.bot.cogs[cog].__doc__,
                                            color=discord.Color.dark_gold())

                        # getting commands from cog
                        for command in self.bot.get_cog(cog).get_commands():
                            # if cog is not hidden
                            if not command.hidden:
                                emb.add_field(name=f"***{prefix} {command.name}***", value=command.help, inline=True)
                        # found cog - breaking loop
                        break

            # if input not found
            # yes, for-loops have an else statement, it's called when no 'break' was issued
            else:
                emb = discord.Embed(title="Oh No!",
                                    description=f"Module could not be found `{input[0]}` :cry:",
                                    color=discord.Color.orange())

        # too many cogs requested - only one at a time allowed
        elif len(input) > 1:
            emb = discord.Embed(title="Oops!",
                                description="Please request only one module at a time",
                                color=discord.Color.orange())

        else:
            emb = discord.Embed(title="RIP", description="My Pants Are Wet", color=discord.Color.red())

        # sending reply embed using our own function defined above
        await send_embed(ctx, emb)


def setup(bot):
    bot.add_cog(Help(bot))

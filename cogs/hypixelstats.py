from os import getenv
from discord.ext import commands, tasks
from discord import embeds, Color, File
import requests
import json
import sys
from utils.minecraft import get_uuid, get_name
from utils.graph_config import qc_config_pie
from zoneinfo import ZoneInfo
import utils.errors as errors
from quickchart import QuickChart
import datetime
from collections import defaultdict
from random import randint


class HypixelStats(commands.Cog, description="A Collection of Commands for Hypixel Monitoring"):
    """A collection of commands regarding Hypixel"""

    def __init__(self, bot):
        self.bot = bot
        self.players = []  # Player: {'uuid': uuid, 'discord_id': discord_id, 'name': name, 'date': date, 'ended': ended, 'prev_activity': pre_activity, 'current_activity': current_activity}, Activity: {'gametype': gametype, 'mode': mode, 'map': map}
        self.update_players = True
        self.loops = 0
        self.track_activity.start()

    async def graph(self, rows, name):
        # Setup QuickChart
        qc = QuickChart()
        qc.width = 1000
        qc.height = 600
        qc.device_pixel_ratio = 2.0
        qc.config = qc_config_pie

        # Prepare Data
        data = defaultdict(float)
        for row in rows:
            if row['time_played'] is not None:
                if row['gametype'] == "main":  # or row['gametype'] == "arcade" or row['gametype'] == "legacy" or row['gametype'] == "prototype"
                    row['gametype'] = row['gametype'] + " Lobby"

                data[row['gametype'].capitalize()] += (row['time_played'])

        # Add data to QuickChart config and clear old data
        qc.config['data']['datasets'][0]['data'].clear()
        qc.config['data']['datasets'][0]['backgroundColor'].clear()
        qc.config['data']['labels'].clear()
        for k in data:
            time_played = round(float(data[k]), 2)

            qc.config['data']['datasets'][0]['data'].append(time_played)
            qc.config['data']['datasets'][0]['backgroundColor'].append(f"rgb({randint(70, 230)}, {randint(70, 230)}, {randint(70, 230)})")
            qc.config['data']['labels'].append(str(k) + f"({time_played} hours)")

        qc.config['data']['datasets'][0]['label'] = str(name)
        qc.config = str(qc.config)

        return qc.get_short_url()

    async def get_name_uuid_from_input(self, player_name_uuid):
        try:
            if len(player_name_uuid) > 16:
                name = await get_name(player_name_uuid)
                uuid = await get_uuid(name)
            else:  # If name
                uuid = await get_uuid(player_name_uuid)
                name = await get_name(uuid)
        except:
            raise errors.InvalidUUID(param=player_name_uuid)

        name.replace(" ", "")
        return {'uuid': uuid, 'name': name}

    @commands.cooldown(1, 2, commands.BucketType.default)
    @commands.command(help="Use `data <minecraft account name or uuid>` to get detailed data graphs")
    async def data(self, ctx, player_to_add):

        # Get Player to add info
        player_to_add = await self.get_name_uuid_from_input(player_to_add)
        uuid = player_to_add['uuid']
        name = player_to_add['name']

        for item in self.players:
            if item['uuid'] == uuid:

                rows = await self.bot.db.select_hypixel_data_all_days(uuid)

                # Graph Data
                graph = await self.graph(rows, item['name'])

                # Send added message
                embed = embeds.Embed(title=f"Showing Data For {name}",
                                     description=f"Total Time Played!",
                                     url=graph,
                                     color=Color.green())
                embed.set_image(url=graph)
                embed.set_author(name="Happy Egg",
                                 icon_url="https://cdn.discordapp.com/avatars/812506337644511253"
                                          "/aca7819ddd7b3e2f50fc1115f41cc3e2.png?size=256")
                await ctx.send(embed=embed)
                return

        raise errors.InvalidUUID(name)

    @commands.cooldown(1, 3, commands.BucketType.default)
    @commands.command(help="Use `remove` to remove the account your monitoring")
    async def remove(self, ctx):
        removed = None
        for player in self.players:
            if str(ctx.author.id) == player['discord_id']:
                await self.bot.db.remove_uuid_data(player['uuid'], str(ctx.author.id))
                self.players.remove(player)
                removed = player["name"]
                break

        if removed is None:
            raise errors.NotMonitoring()
        else:
            # Send Removed message
            embed = embeds.Embed(title="Success",
                                 description=f"{removed} Removed!",
                                 color=Color.green())
            embed.set_author(name="Happy Egg",
                             icon_url="https://cdn.discordapp.com/avatars/812506337644511253"
                                      "/aca7819ddd7b3e2f50fc1115f41cc3e2.png?size=256")
            await ctx.send(embed=embed)

    @commands.cooldown(1, 5, commands.BucketType.default)
    @commands.command(help="Use `add <name or uuid> <minecraft account name or uuid>` to add an account to monitor")
    async def add(self, ctx, player_to_add):
        if len(self.players) < 18:

            # Get Player to add info
            player_to_add = await self.get_name_uuid_from_input(player_to_add)
            uuid = player_to_add['uuid']
            name = player_to_add['name']

            if uuid is not None:
                uuid.replace('_', '')

                for player in self.players:
                    if str(ctx.author.id) == player['discord_id']:
                        raise errors.AccountAlreadyMonitoring(param=player['name'])
                    if uuid == player['uuid']:
                        raise errors.AlreadyMonitored(param=name)

                # Add UUID locally and to Database
                await self.bot.db.insert_uuid_data(str(uuid), str(ctx.author.id))
                formatted_name = await get_name(uuid)
                self.players.append({'uuid': uuid, 'discord_id': str(ctx.author.id), 'name': formatted_name, 'prev_activity': None, 'current_activity': None})
                # Send added message
                embed = embeds.Embed(title="Success",
                                     description=f"{formatted_name} Added!",
                                     color=Color.green())

                embed.set_author(name="Happy Egg",
                                 icon_url="https://cdn.discordapp.com/avatars/812506337644511253"
                                          "/aca7819ddd7b3e2f50fc1115f41cc3e2.png?size=256")
                await ctx.send(embed=embed)
            else:
                raise errors.InvalidUUID(param=name)
        else:
            raise errors.TooManyAccounts()

    @commands.command(hidden=True)
    async def ping(self, ctx, *, message: commands.clean_content):
        pass

    @staticmethod
    def retrieve_activity(player):
        # Request Hypixel API status
        request_status = requests.get(
            f"https://api.hypixel.net/status?key={getenv('HYPIXEL_KEY')}&uuid={player['uuid']}")

        if int(request_status.headers['RateLimit-Remaining']) > 5:

            # Check if the request was successful
            if int(str(request_status.status_code)[0]) == 2:
                if request_status.json()["success"] is True:
                    request_status = json.loads(request_status.text)

                    # Determine the result
                    if request_status["session"]["online"] is False:
                        player['current_activity'] = {'gametype': "offline", 'mode': 'none', 'map': 'none'}

                    elif 'map' in request_status["session"]:
                        player['current_activity'] = {'gametype': request_status["session"]["gameType"].lower(),
                                                      'mode': request_status["session"]["mode"].lower(),
                                                      'map': request_status["session"]["map"].lower()}

                    elif 'mode' in request_status["session"]:
                        player['current_activity'] = {'gametype': request_status["session"]["gameType"].lower(),
                                                      'mode': request_status["session"]["mode"].lower(),
                                                      'map': 'none'}
                    else:
                        player['current_activity'] = {'gametype': request_status["session"]["gameType"].lower(),
                                                      'mode': 'none',
                                                      'map': 'none'}

                    return player
            else:
                print("[INFO]: Error Fetching Hypixel Data" + "\n\n")
                print(request_status.status_code)
                print(request_status.content)
                sys.exit()
        else:
            print("[INFO]: Less than 5 request remain ERROR")
            sys.exit()

    async def send_status(self):
        # Send Discord Message
        channel = self.bot.get_channel(739333758058233857)
        fields = []

        # Get Time
        now_pacific = datetime.datetime.now(ZoneInfo('US/Pacific'))

        # Setup Embed
        embed = embeds.Embed(title="Hypixel Status",
                             description=f"{now_pacific.strftime('%Y-%m-%d, %I:%M %p')} PST",
                             color=Color.blurple())
        embed.set_author(name="Happy Egg", url="https://api.hypixel.net/",
                         icon_url="https://cdn.discordapp.com/avatars/812506337644511253"
                                  "/aca7819ddd7b3e2f50fc1115f41cc3e2.png?size=256")
        embed.set_thumbnail(
            url="https://fsa.zobj.net/crop.php?r=by0jGANgnc4W22sOr9z4e9V"
                "-f5s5J9Ud5UMMEyggbnr0Mr3JYYoK16DCVlQulNDLSO6xrestaTY37IUXFdx5A-h1LOgW6zaWU03pvnFnVw"
                "-6C37MyBorvI6Fc-qdaFTVsjNzrGm-ZcZDSmu4")

        # Parse Data
        for player in self.players:
            message = "Currently playing"

            if player['current_activity']['gametype'] != "offline":
                message += " " + player['current_activity']['gametype'].replace('_', ' ').capitalize()

            else:
                message = "Currently offline"

            if player['current_activity']['mode'] != 'none' and player['current_activity']['mode'].lower() != player['current_activity']['gametype'].lower():
                message += " " + player['current_activity']['mode'].replace('_', ' ').replace(player['current_activity']['gametype'], '').capitalize()

            if player['current_activity']['map'] != 'none' and player['current_activity']['map'].lower() != player['current_activity']['mode'].lower():
                message += " on the map \"" + player['current_activity']['map'].replace('_', ' ').capitalize() + "\""

            fields.append([f'**{player["name"]}**', message])

        # Add Fields
        for field in fields:
            embed.add_field(name=field[0], value=field[1], inline=False)

        await channel.send(embed=embed)

    async def update_players_initially(self):
        self.players.clear()
        players = await self.bot.db.select_all_hypixel_uuids()
        for player in players:
            # Set Last Activity
            prev_activity = None
            current_activity = None

            discord_id = player['discord_id']
            name = await get_name(player['uuid'])
            uuid = player['uuid']
            self.players.append(
                {'uuid': uuid, 'discord_id': discord_id, 'name': name, 'prev_activity': prev_activity,
                 'current_activity': current_activity})

    async def update_gametime_with_database(self, player):
        # Query if there is a row already for the game
        row = await self.bot.db.select_row_game_uuid(uuid=player['uuid'], gametype=player['prev_activity']['gametype'], mode='none', game_map='none')  # mode=player['prev_activity']['mode'], map=player['prev_activity']['map']) # Makes too many rows

        time_played = round(float(((player['ended'] - player['date']).total_seconds() / 60 / 60)), 5)

        if not row:
            # Create New Row With Data
            await self.bot.db.insert_hypixel_data(game_type=player['prev_activity']['gametype'], mode='none', game_map='none', uuid=player['uuid'], time=time_played)  #player['prev_activity']['mode'], player['prev_activity']['map'])
        else:
            # Update Existing Row's time
            await self.bot.db.update_row_game_uuid(time_played=time_played, uuid=player['uuid'], gametype=player['prev_activity']['gametype'], mode='none', game_map='none')  # player['prev_activity']['mode'], player['prev_activity']['map'])

    @tasks.loop(seconds=10)
    async def track_activity(self):

        if self.update_players:
            self.update_players = False
            await self.update_players_initially()

        # Retrieve current activity
        for i in range(0, len(self.players)):
            self.players[i] = self.retrieve_activity(self.players[i])

        # Check if the current activity is equal to the previous activity for each player
        for i in range(0, len(self.players)):
            # Set the ended date for the previous activity to be now
            self.players[i]['ended'] = datetime.datetime.now(tz=datetime.timezone.utc)

            if self.players[i]['prev_activity'] is not None:
                if self.players[i]['current_activity'] != self.players[i]['prev_activity']:
                    # Update Time Played For the Previous activity with the database
                    await self.update_gametime_with_database(self.players[i])

                    # Set the date of the new activity to be now
                    self.players[i]['date'] = datetime.datetime.now(tz=datetime.timezone.utc)

                else:
                    # If they are still the same after 5 minutes, update the database anyway
                    if self.loops % 30 == 0:
                        await self.update_gametime_with_database(self.players[i])

                        # Set the date of the new activity to be now
                        self.players[i]['date'] = datetime.datetime.now(tz=datetime.timezone.utc)
            else:
                # First Time Around set date
                self.players[i]['date'] = datetime.datetime.now(tz=datetime.timezone.utc)

        for i in range(0, len(self.players)):
            # Set the previous activity as the current activity
            self.players[i]['prev_activity'] = self.players[i]['current_activity']

        # Send status message to channel
        if self.loops % 6 == 0:
            if len(self.players) != 0:
                await self.send_status()

        self.loops += 1


def setup(bot):
    bot.add_cog(HypixelStats(bot))

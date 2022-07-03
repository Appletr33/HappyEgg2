import asyncpg
import asyncio
import ssl
import os


class Database:
    def __init__(self):
        self.pool = None

    async def pool_connect_to_db(self):
        #ctx = ssl.create_default_context(cafile='root certificate.pem')
        #ctx.check_hostname = False
        #ctx.verify_mode = ssl.CERT_NONE
        self.pool = await asyncpg.create_pool(user=os.environ["USER_TOKEN"], password=os.environ["PASS_TOKEN"], host=os.environ["HOST_TOKEN"], database=os.environ["DB_TOKEN"], ssl=None) #ctx
        print("[INFO]: Connected To Database")

    async def insert_hypixel_data(self, game_type, mode, game_map, uuid, time):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                        INSERT INTO hypixel_stats (gametype, mode, map, uuid, time_played) VALUES($1, $2, $3, $4, $5);
                    ''', game_type, mode, game_map, uuid, time)

    async def insert_uuid_data(self, uuid, discord_id):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                               INSERT INTO uuids (uuid, discord_id) VALUES($1, $2);
                           ''', uuid, discord_id)

    async def remove_uuid_data(self, uuid, discord_id):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                               DELETE FROM uuids WHERE discord_id=$1 AND uuid=$2;
                           ''', discord_id, uuid)

    async def select_all_hypixel_uuids(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''SELECT * FROM uuids;''')
            return [dict(row) for row in rows]

    async def select_discord_id_from_uuid(self, uuid):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f'''SELECT * FROM uuids WHERE uuid = $1;''',
                                    str(uuid))
            return [dict(row) for row in rows]

    async def select_row_game_uuid(self, uuid, gametype, mode, game_map):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f'''SELECT id FROM hypixel_stats WHERE gametype = $1 AND mode = $2 AND map = $3 AND uuid = $4;''',
                gametype, mode, game_map, str(uuid))
            return [dict(row) for row in rows]

    async def select_hypixel_data_all_days(self, uuid):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                f'''SELECT * FROM hypixel_stats WHERE uuid = $1;''', str(uuid))
            return [dict(row) for row in rows]

    async def update_row_game_uuid(self, time_played, uuid, gametype, mode, game_map):
        async with self.pool.acquire() as conn:
            await conn.execute(
                f'''UPDATE hypixel_stats SET time_played = time_played + $1 WHERE id IN (SELECT id FROM hypixel_stats WHERE uuid = $2 AND gametype = $3 AND mode = $4 AND map = $5);''',
                time_played, str(uuid), gametype, mode, game_map)

    # Deprecated
    async def delete_last_hypixel_row(self, uuid):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('''DELETE FROM hypixel_stats WHERE id IN (SELECT id FROM hypixel_stats WHERE (uuid = $1) ORDER BY id DESC LIMIT 1);''', uuid)

    # Deprecated
    async def select_last_hypixel_row(self, uuid):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('''SELECT * FROM hypixel_stats WHERE uuid = $1 ORDER BY id DESC LIMIT 1;''', uuid)

    # Deprecated
    async def update_ended_last_hypixel_row(self, uuid):
        async with self.pool.acquire() as conn:
            await conn.execute('''UPDATE hypixel_stats SET ended = NOW() WHERE id IN (SELECT id FROM hypixel_stats WHERE uuid = $1 ORDER BY id DESC LIMIT 1);''', uuid)

    # Deprecated
    async def update_ended_done_last_hypixel_row(self, uuid):
        async with self.pool.acquire() as conn:
            await conn.execute('''UPDATE hypixel_stats SET ended = NOW(), done = TRUE WHERE id IN (SELECT id FROM hypixel_stats WHERE uuid = $1 ORDER BY id DESC LIMIT 1);''', uuid)

    # Deprecated
    async def select_hypixel_data_one_day(self, uuid):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f'''SELECT * FROM hypixel_stats WHERE date > NOW() - interval '1' DAY AND uuid = $1;''',
                                    str(uuid))
            return [dict(row) for row in rows]

    # Deprecated
    async def select_hypixel_data_seven_days(self, uuid):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f'''SELECT * FROM hypixel_stats WHERE date > NOW() - interval '7' DAY AND uuid = $1;''',
                                    str(uuid))
            return [dict(row) for row in rows]


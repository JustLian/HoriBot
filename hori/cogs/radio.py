import traceback
from hori import GUILDS, db, CColour
from pytube import Playlist
from random import shuffle
from nextcord import Interaction, SlashOption, Colour, Embed
import nextcord
from nextcord.ext import commands
import asyncio
import json
import nextcord
from nextcord.ext import commands
import nextwave


skips = {}


async def start_radio(bot: commands.Bot, guild: int) -> None:
    data = db.get_server(guild)
    guild: nextcord.Guild = bot.get_guild(guild)
    if guild is None:
        return

    channel: nextcord.VoiceChannel = guild.get_channel(data['music_channel'])
    if channel is None:
        return

    if not guild.voice_client:
        vc: nextwave.Player = await channel.connect(cls=nextwave.Player)
    else:
        vc: nextwave.Player = guild.voice_client

    queue = []
    ready = []
    for pl in enumerate(data['playlist_urls']):
        urls = list(Playlist(pl[1]).video_urls)
        pool = [0 for _ in range(len(urls))]
        for url in enumerate(urls):
            asyncio.create_task(
                add_track(url[1], pool, url[0], ready))
        while len(ready) != len(urls):
            await guild.me.edit(nick=f"{bot.user.name} | Task {pl[0] + 1}/{len(data['playlist_urls'])}: {len(ready) + 1}/{len(urls)}")
            await asyncio.sleep(2)
        while 0 in pool:
            pool.remove(0)
        queue.extend(pool)
    if bool(data['shuffle']):
        shuffle(queue)
    vc.queue.extend(queue)

    skips[guild.id] = []
    await vc.play(vc.queue.get())


async def add_track(url, pool, index, ready):
    node = nextwave.NodePool.get_node()
    if 'music.youtube' in url:
        try:
            t = (await node.get_tracks(nextwave.YouTubeMusicTrack, url))[0]
            pool[index] = t
        except:
            pass
    else:
        try:
            t = (await node.get_tracks(nextwave.YouTubeTrack, url))[0]
            pool[index] = t
        except:
            pass
    ready.append(0)


class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @nextcord.slash_command('skip', 'Skip current song', GUILDS)
    async def cmd_skip(self, inter: Interaction):
        await inter.response.defer()
        data = db.get_server(inter.guild.id)

        if inter.guild.id not in skips:
            skips[inter.guild.id] = []

        if data['radio_enabled'] == 0:
            em = Embed(title="Radio is disabled",
                       description="Use /radio on (admins only) to enable radio", colour=CColour.dark_brown)
            em.set_thumbnail(url='attachment://sad.gif')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad.gif'))
            return

        if inter.user.voice is None or inter.user.voice.channel.id != data['music_channel']:
            em = Embed(title="Join radio channel",
                       description="Join same channel as me to use that command!", colour=CColour.dark_brown)
            em.set_thumbnail(url='attachment://surprised-1.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/surprised-1.png'))
            return

        if inter.user.id in skips[inter.guild.id]:
            em = Embed(title="You've already voted for skip",
                       description="75% of listeners must vote to skip current song", colour=CColour.dark_brown)
            em.set_thumbnail(url='attachment://happy-4.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/happy-4.png'))
            return

        skips[inter.guild.id].append(inter.user.id)

        if len(skips[inter.guild.id]) < (len(inter.user.voice.channel.members) - 1) * 3 / 4:
            em = Embed(title="Vote counted!",
                       description="75% of listeners must vote to skip current song", colour=CColour.orange)
            em.set_thumbnail(url='attachment://happy-3.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/happy-3.png'))
            return

        em = Embed(title="Vote counted!",
                   description="Skipping current song!", colour=CColour.light_orange)
        em.set_thumbnail(url='attachment://happy-5.gif')
        await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/happy-5.gif'))
        await inter.guild.voice_client.stop()


class Radio(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.bot.wait_until_ready()

        with open('./secrets/lava_nodes.json', 'r') as f:
            nodes = json.load(f)

        for node in nodes:
            await nextwave.NodePool.create_node(bot=self.bot,
                                                host=node['host'],
                                                port=node['port'],
                                                password=node['password'])

    @commands.Cog.listener()
    async def on_ready(self):
        for guild_id in db.get_servers():
            if db.get_server(guild_id)['radio_enabled'] == 0:
                continue
            try:
                await asyncio.create_task(start_radio(self.bot, guild_id))
            except Exception as e:
                print(
                    f'Error occurred in start_radio({self.bot}, {guild_id}): {e}')
                traceback.print_exception(e)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: nextwave.Node):
        print(f'Node <{node.identifier}> is ready')

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player: nextwave.Player, track: nextwave.Track):
        name = f"{self.bot.user.name} | {track.title}"
        if len(name) > 32:
            name = name[:30] + '..'
        await player.guild.me.edit(nick=name)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: nextwave.Player, track: nextwave.Track, reason):
        skips[player.guild.id] = []
        try:
            await player.play(player.queue.get())
        except:
            if db.get_server(player.guild.id)['radio_enabled'] == 1:
                await start_radio(self.bot, player.guild.id)

    @nextcord.slash_command('radio_settings', 'Setup 24/7 radio on your server', GUILDS)
    async def cmd_setup_radio(self, inter: Interaction, add_url: str = SlashOption('add_url', 'Add Youtube/YouTube Music playlist url to guild library', False), remove_url: str = SlashOption('remove_url', 'Remove YouTube/YouTube Music playlist from guild library', False), update_channel: bool = SlashOption('update_channel', "Set your current voicechannel to Hori's radio channel", False), shuffle: bool = SlashOption('shuffle', "Set if songs from all playlist should get shuffled every time radio starts", False)):
        await inter.response.defer()

        if not inter.user.guild_permissions.administrator:
            em = Embed(title="No permissions",
                       description="You don't have enough permissions to execute that command!", colour=Colour.brand_red())
            em.set_thumbnail(url='attachment://sad-3.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad-3.gif'))
            return

        data = db.get_server(inter.guild.id)

        updates = []

        if add_url:
            if add_url in data['playlist_urls']:
                em = Embed(title="Playlist is already in library",
                           description="If you know that playlist is not in library report that on our github with your server id (https://github.com/JustLian/HoriBot", colour=CColour.dark_brown())
                em.set_thumbnail(url='attachment://sad-3.png')
                await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad-3.png'))
                return

            data['playlist_urls'].append(add_url)
            db.update_server(
                inter.guild.id, ('playlist_urls', data['playlist_urls']))
            updates.append('added new playlist')

        if remove_url:
            if add_url not in data['playlist_urls']:
                em = Embed(title="Playlist is not in library",
                           description="If you know that playlist is in library report that on our github with your server id (https://github.com/JustLian/HoriBot", colour=CColour.dark_brown())
                em.set_thumbnail(url='attachment://sad-3.png')
                await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad-3.png'))
                return

            data['playlist_urls'].remove(add_url)
            db.update_server(
                inter.guild.id, ('playlist_urls', data['playlist_urls']))
            updates.append('removed playlist')

        if update_channel:
            if not inter.user.voice:
                em = Embed(title='You are not in VC!',
                           description='You need to join some VC to do that!', colour=Colour.brand_red())
                em.set_thumbnail(url='attachment://sad-3.png')
                await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad-3.png'))
                return

            db.update_server(inter.guild.id, ('music_channel',
                             inter.user.voice.channel.id))
            updates.append('updated radio channel')

        if shuffle is not None:
            db.update_server(inter.guild.id, ('shuffle', int(shuffle)))
            updates.append(
                f'{"enabled" if shuffle else "disabled"} shuffle feature')

        if len(updates) > 0:

            em = Embed(title='Updated settings',
                       description=', '.join(updates).title(), colour=CColour.orange)
            em.set_thumbnail(url='attachment://happy-4.png')

            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/happy-4.png'))
            return

        em = Embed(title='Current radio settings', colour=CColour.orange)
        em.set_thumbnail(url='attachment://happy-2.png')
        em.add_field(name='Radio channel id',
                     value=data['music_channel'], inline=True)
        em.add_field(name='Radio enabled',
                     value='yes' if data['radio_enabled'] else 'no', inline=True)
        em.add_field(name='Shuffle enabled',
                     value='yes' if data['shuffle'] else 'no', inline=True)
        em.add_field(name='Playlist urls', value=', '.join(
            data['playlist_urls']), inline=True)

        await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/happy-2.png'))

    @nextcord.slash_command('radio', 'Enable/disable radio', GUILDS)
    async def cmd_radio(self, inter: Interaction, toggle: str = SlashOption('toggle', 'Enable/disable radio', True, ['on', 'off'])):
        await inter.response.defer()

        if not inter.user.guild_permissions.administrator:
            em = Embed(title="No permissions",
                       description="You don't have enough permissions to execute that command!", colour=Colour.brand_red())
            em.set_thumbnail(url='attachment://sad-3.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad-3.gif'))
            return

        toggle = toggle == 'on'
        data = db.get_server(inter.guild.id)

        if data['music_channel'] == 0 or data['playlist_urls'] == []:
            em = Embed(title='Setup radio first!',
                       description='Use command /setup_radio to setup radio on your server. (You must have Administrator permissions)', colour=Colour.brand_red())
            em.set_thumbnail(url='attachment://shouting-1.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/shouting-1.png'))
            return

        if toggle:
            em = Embed(title='Trying to find voicechannel...',
                       description='Please wait.', colour=Colour.blurple())
            await inter.edit_original_message(embed=em)
            try:
                channel: nextcord.VoiceChannel = await self.bot.fetch_channel(data['music_channel'])
            except:
                em.title = 'Voicechannel not found!'
                em.description = 'Setup radio again.'
                em.colour = Colour.red()
                await inter.edit_original_message(embed=em)
                return

            em.title = 'Channel found! Setting everything up...'
            await inter.edit_original_message(embed=em)

            if inter.guild.voice_client is not None:
                await inter.guild.voice_client.disconnect(force=True)

            await start_radio(self.bot, inter.guild.id)

            em.title = 'Setting everything up! Currently trying to get your playlist.'
            await inter.edit_original_message(embed=em)

            db.update_server(inter.guild.id, ('radio_enabled', 1))
            em.title = 'Everything is done!'
            em.description = f'Radio will work 24/7!'
            em.colour = CColour.orange
            em.set_thumbnail(url='attachment://happy-5.gif')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/happy-5.gif'))
            return

        db.update_server(inter.guild.id, ('radio_enabled', 0))
        skips[inter.guild.id] = []
        if inter.guild.voice_client is not None:
            inter.guild.voice_client.queue.clear()
            inter.guild.voice_client.stop()
            await inter.guild.voice_client.disconnect(force=True)

        em = Embed(title='Radio was disabled!',
                   description='Use command /radio on to enable it!', colour=CColour.brown)
        em.set_thumbnail(url='attachment://thinking.png')
        await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/thinking.png'))


def setup(bot):
    bot.add_cog(Radio(bot))
    bot.add_cog(Utilities(bot))

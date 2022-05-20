import traceback
from hori import GUILDS, db, CColour
from nextcord import Interaction, SlashOption, Colour, Embed
import nextcord
from math import floor
from nextcord.ext import commands
import asyncio
import youtube_dl


youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}
ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

skips = {}


class YTDLSource(nextcord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        entrs = []
        if 'entries' in data:
            for entry in data['entries']:
                filename = entry['url'] if stream else ytdl.prepare_filename(
                    entry)
                entrs.append((cls(nextcord.FFmpegPCMAudio(
                    filename, **ffmpeg_options), data=entry), entry['duration'], entry['title']))
        return entrs


async def start_radio(bot: commands.Bot, guild_id: int, after=None) -> None:
    data = db.get_server(guild_id)
    guild = bot.get_guild(guild_id)
    if guild is None:
        return

    channel: nextcord.VoiceChannel = guild.get_channel(data['music_channel'])
    if channel is None:
        return

    if guild.voice_client is not None:
        await guild.voice_client.disconnect(force=True)
    await channel.connect()

    while True:
        if guild.voice_client is None:
            if db.get_server(guild_id)['radio_enabled'] == 1:
                await channel.connect()
            else:
                break

        entries = await YTDLSource.from_url(data['playlist_url'], loop=bot.loop, stream=True)
        if after is not None:
            after()
        for player in entries:
            skips[guild_id] = []
            guild.voice_client.play(player[0], after=lambda e: print(
                f'Player error: {e}') if e else None)
            print('playing')
            while False if guild.voice_client is None else guild.voice_client.is_playing():
                if len(skips[guild_id]) >= (len(channel.members) - 1) * 3 / 4:
                    guild.voice_client.stop()
                    print('skipping')
                    break
                await asyncio.sleep(2)


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


class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

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

    @nextcord.slash_command('setup_radio', 'Setup 24/7 radio on your server', GUILDS)
    async def cmd_setup_radio(self, inter: Interaction, url: str = SlashOption('playlist_link', 'Playlist link', True)):
        await inter.response.defer()

        if not inter.user.guild_permissions.administrator:
            em = Embed(title="No permissions",
                       description="You don't have enough permissions to execute that command!", colour=Colour.brand_red())
            em.set_thumbnail(url='attachment://sad-3.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad-3.gif'))
            return

        if inter.user.voice is None:
            em = Embed(title='You are not in VC!',
                       description='You need to join some VC to do that!', colour=Colour.brand_red())
            em.set_thumbnail(url='attachment://sad-3.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad-3.png'))
            return

        channel = inter.user.voice.channel.id

        db.update_server(inter.guild.id, ('music_channel', channel),
                         ('playlist_url', url), ('radio_enabled', 0))

        em = Embed(title='Everything is ready!',
                   description='Use command /radio on to start your 24/7 radio!', colour=CColour.orange)
        em.set_thumbnail(url='attachment://happy-4.png')

        await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/happy-4.png'))

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

        if bool(data['radio_enabled']) == toggle:
            em = Embed(title='Action already done',
                       description='Radio is already turned on/off', colour=Colour.brand_red())
            em.set_thumbnail(url='attachment://happy-2.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/happy-2.png'))
            return

        if data['music_channel'] == 0 or data['playlist_url'] == 'NONE':
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

            flag = asyncio.Event()
            asyncio.get_event_loop().create_task(
                start_radio(self.bot, inter.guild.id, flag.set))

            em.title = 'Setting everything up! Currently trying to get your playlist.'
            await inter.edit_original_message(embed=em)

            await flag.wait()

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
            await inter.guild.voice_client.disconnect(force=True)

        em = Embed(title='Radio was disabled!',
                   description='Use command /radio on to enable it!', colour=CColour.brown)
        em.set_thumbnail(url='attachment://shouting-1.png')
        await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/shouting-1.png'))


def setup(bot):
    bot.add_cog(Radio(bot))
    bot.add_cog(Utilities(bot))

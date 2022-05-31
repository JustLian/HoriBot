import traceback
from nextcord import Interaction, Embed, SlashOption
import lyricsgenius
import nextcord
from nextcord.ext import commands
from hori import GUILDS, CColour
import asyncio


with open('./secrets/genius_token', 'r') as f:
    _genius_token = f.read().strip()
genius = lyricsgenius.Genius(_genius_token, verbose=False)


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @nextcord.slash_command('help', 'List all commands', GUILDS)
    async def cmd_help(self, inter: Interaction):
        await inter.response.defer()
        em = nextcord.Embed(title="Hori's commands",
                            description="List of all Hori's commands with description", colour=CColour.light_orange)
        em.set_thumbnail(url='attachment://happy-2.png')
        fields = {}
        for command in self.bot.get_all_application_commands():
            name = '/' + command.name
            for opt in command.options.keys():
                name += f' <{command.options[opt].name}>'
            fields[name] = command.description

        for field in fields.keys():
            em.add_field(name=field, value=fields[field], inline=False)

        await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/happy-2.png'))

    @nextcord.slash_command('lyrics', 'Find song lyrics', GUILDS)
    async def cmd_lyrics(self, inter: Interaction, title: str = SlashOption('name', 'Song title', True)):
        await inter.response.defer()

        song = await asyncio.get_event_loop().run_in_executor(None, genius.search_song, title)

        if song is None:
            em = Embed(title='Nothing found',
                       description="I couldn't find song with that title", colour=CColour.brown)
            em.set_thumbnail(url='attachment://sad-3.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad-3.png'))
            return

        lyrics = "Lyrics:\n" + 'Lyrics'.join(song.lyrics.split('Lyrics')[1:])

        em = Embed(title=song.title, description=lyrics[:4096] if len(lyrics) > 4096 else lyrics,
                   colour=CColour.light_orange, url=song.url)
        em.set_footer(text=song.artist)
        em.set_thumbnail(url=song.song_art_image_thumbnail_url)
        await inter.edit_original_message(embed=em)
        if len(lyrics) > 4096:
            last = 0
            for n in range(6096, len(lyrics), 2000):
                await inter.send(lyrics[n - 2000:n])
                last = n
            await inter.send(lyrics[last:])

    @ nextcord.slash_command('artist', "Search artist's songs on Genius", GUILDS)
    async def cmd_artist(self, inter: Interaction, name: str = SlashOption('name', "Artist's name", True)):
        await inter.response.defer()

        artist = await asyncio.get_event_loop().run_in_executor(
            None, genius.search_artist, name, 15)

        if artist is None:
            em = Embed(title='Nothing found',
                       description="I couldn't find artist with that title", colour=CColour.brown)
            em.set_thumbnail(url='attachment://sad-3.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad-3.png'))
            return

        em = Embed(title=f"{artist.name}'s songs",
                   description=f"{len(artist.songs)} most popular")
        for song in artist.songs:
            em.add_field(name=song.title, value=f'[Genius page]({song.url})')

        await inter.edit_original_message(embed=em)

    @commands.Cog.listener()
    async def on_application_command_error(self, inter: Interaction, err):
        em = Embed(title='Error occurred!',
                   description='Please copy text from message below and create bug report on [Github](https://github.com/JustLian/HoriBot) or contact developer on [support server](https://discord.gg/gSvt9TpHkG)')
        em.set_thumbnail(url='attachment://sad.gif')
        await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad.gif'))
        await inter.send(''.join(traceback.format_exception(err)))


def setup(bot):
    bot.add_cog(Main(bot))

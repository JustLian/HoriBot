from nextcord import Interaction, Embed, SlashOption
import lyricsgenius
import nextcord
from nextcord.ext import commands
from hori import GUILDS, CColour


with open('./secrets/genius_token', 'r') as f:
    _genius_token = f.read().strip()
genius = lyricsgenius.Genius(_genius_token)


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
    async def cmd_lyrics(self, inter: Interaction, title: str = SlashOption('')):
        await inter.response.defer()

        song = genius.search_song(title)

        if song is None:
            em = Embed(title='Nothing found',
                       description="I couldn't find a song with that title", colour=CColour.brown)
            em.set_thumbnail(url='attachment://sad-3.png')
            await inter.edit_original_message(embed=em, file=nextcord.File('./assets/emotes/sad-3.png'))
            return

        em = Embed(title=song.title, description="Lyrics:\n" + 'Lyrics'.join(song.lyrics.split('Lyrics')[1:]),
                   colour=CColour.light_orange)
        em.set_footer(text=song.artist)
        em.set_thumbnail(url=song.song_art_image_thumbnail_url)
        await inter.edit_original_message(embed=em)


def setup(bot):
    bot.add_cog(Main(bot))

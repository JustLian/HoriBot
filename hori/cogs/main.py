from nextcord import Interaction, Colour, SlashOption
import nextcord
from nextcord.ext import commands
import youtube_dl
from hori import GUILDS, CColour


def check_youtube_url(url: str) -> bool:
    return url.replace('https://', '').startswith('www.youtube.com') or url.replace('https://', '').startswith('music.youtube.com')


youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


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


def setup(bot):
    bot.add_cog(Main(bot))

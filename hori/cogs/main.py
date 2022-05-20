from nextcord import Interaction, Colour
import nextcord
from nextcord.ext import commands

from hori import GUILDS
reminds = {}


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @nextcord.slash_command('help', 'List all commands', GUILDS)
    async def cmd_help(self, inter: Interaction):
        await inter.response.defer()
        em = nextcord.Embed(title="Hori's commands",
                            description="List of all Hori's commands with description", colour=Colour.from_rgb(186, 82, 235))
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

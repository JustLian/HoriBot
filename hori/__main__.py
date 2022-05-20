import asyncio
import os
import nextcord
from hori import db, CColour
from termcolor import colored
from nextcord import Embed
from nextcord.ext import commands


with open('./secrets/bot_token', 'r') as f:
    _token = f.read().strip()

bot = commands.Bot(intents=nextcord.Intents.all())


@bot.event
async def on_ready():
    print('Loaded ', colored('Hori', 'magenta'), '!', sep='')
    await asyncio.sleep(2)
    await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.playing, name='/help'), status=nextcord.Status.online)


@bot.event
async def on_guild_join(guild: nextcord.Guild):
    em = Embed(title='Thanks for inviting!',
               description="Hi! Thankyou for inviting me :> Setup your free 24/7 radio using /setup_radio commad!", colour=CColour.light_orange)
    em.add_field(name='Developer',
                 value='https://github.com/JustLian', inline=False)
    em.add_field(name='HoriBot on Github',
                 value='https://github.com/JustLian/HoriBot', inline=False)
    em.add_field(name='MarinBot on Github',
                 value='https://github.com/JustLian/MarinBot', inline=False)
    em.set_thumbnail(url='attachment://happy-5.gif')
    if guild.system_channel is None:
        channel = max([c for c in guild.channels if c.permissions_for(
            guild.self_role).send_messages == True], key=lambda x: x.position)
        await channel.send(embed=em, file=nextcord.File('./assets/emotes/happy-5.gif'))
    db.create_server(guild.id)


@bot.event
async def on_guild_remove(guild):
    db.delete_server(guild.id)


if __name__ == '__main__':
    print('Loading ', colored('Hori', 'magenta'), '...', sep='')
    for ext in os.listdir('./hori/cogs/'):
        if ext.endswith('.py'):
            bot.load_extension(f'hori.cogs.{ext[:-3]}')
            print('Loaded extension',
                  colored(ext, 'blue', 'on_yellow'))
    print('Extensions loaded')

    bot.run(_token)

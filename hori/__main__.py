import asyncio
import os
import nextcord
from hori import db
from termcolor import colored
from nextcord import *
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
async def on_guild_join(guild):
    db.create_server(guild.id)


@bot.event
async def on_guild_remove(guild):
    db.delete_server(guild.id)


print('Loading ', colored('Hori', 'magenta'), '...', sep='')
for ext in os.listdir('./hori/cogs/'):
    if ext.endswith('.py'):
        bot.load_extension(f'hori.cogs.{ext[:-3]}')
        print('Loaded extension',
              colored(ext, 'blue', 'on_yellow'))
print('Extensions loaded')


bot.run(_token)

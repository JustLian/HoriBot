import asyncio
import os
import nextcord
from hori import db, CColour, PRESENCE_LOOP_COOLDOWN
from termcolor import colored
from nextcord import Embed
from nextcord.ext import commands, tasks
import topgg


with open('./secrets/bot_token', 'r') as f:
    _token = f.read().strip()
with open('./secrets/topgg_token', 'r') as f:
    _topgg_token = f.read().strip()
restart_in = None

bot = commands.Bot(command_prefix='hori/', intents=nextcord.Intents.all())
topgg_api = topgg.client.DBLClient(token=_topgg_token)


@bot.event
async def on_command_error(ctx, error):
    pass


@bot.command('restart_presence')
async def cmd_restart_presence(ctx: commands.Context, minutes: int):
    global restart_in
    if (await bot.application_info()).owner.id == ctx.author.id:
        restart_in = minutes
        await ctx.reply('done')


@bot.event
async def on_ready():
    print('Loaded ', colored('Hori', 'magenta'), '!', sep='')
    await asyncio.sleep(2)
    await presence_loop.start()


@bot.event
async def on_guild_join(guild: nextcord.Guild):
    em = Embed(title='Thanks for inviting!',
               description="Hi! Thankyou for inviting me :> Setup your free 24/7 radio using /radio_settings commad!", colour=CColour.light_orange)
    em.add_field(name='Developer',
                 value='[GITHUB](https://github.com/JustLian)', inline=False)
    em.add_field(name='HoriBot on Github',
                 value='[GITHUB](https://github.com/JustLian/HoriBot)', inline=False)
    em.add_field(name='Support server',
                 value='[DISCORD](https://discord.gg/gSvt9TpHkG)', inline=False)
    em.set_thumbnail(url='attachment://happy-5.gif')
    if guild.system_channel is None:
        channel = sorted([c for c in guild.text_channels if c.permissions_for(
            guild.self_role).send_messages == True], key=lambda x: x.position, reverse=True)[-1]
    else:
        channel = guild.system_channel
    await channel.send(embed=em, file=nextcord.File('./assets/emotes/happy-5.gif'))
    db.create_server(guild.id)


@bot.event
async def on_guild_remove(guild):
    db.delete_server(guild.id)


@tasks.loop(minutes=1)
async def topgg_loop():
    await topgg_api.post_guild_count(len(bot.guilds))


@tasks.loop(seconds=PRESENCE_LOOP_COOLDOWN * 2)
async def presence_loop():
    global restart_in
    if restart_in is not None:
        restart_in -= PRESENCE_LOOP_COOLDOWN / 60
        if restart_in < 0:
            restart_in = 0
        await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=f'Restart in {round(restart_in)} minutes'), status=nextcord.Status.dnd)
        return

    await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.playing, name='/help'), status=nextcord.Status.online)
    await asyncio.sleep(PRESENCE_LOOP_COOLDOWN)
    await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=f'{len(bot.guilds)} servers'), status=nextcord.Status.online)


if __name__ == '__main__':
    print('Loading ', colored('Hori', 'magenta'), '...', sep='')
    for ext in os.listdir('./hori/cogs/'):
        if ext.endswith('.py'):
            bot.load_extension(f'hori.cogs.{ext[:-3]}')
            print('Loaded extension',
                  colored(ext, 'blue', 'on_yellow'))
    print('Extensions loaded')

    bot.run(_token)

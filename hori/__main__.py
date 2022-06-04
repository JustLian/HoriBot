import asyncio
import logging
import os
import traceback
import nextcord
from hori import db, CColour, PRESENCE_LOOP_COOLDOWN
from hori.cogs import radio
from termcolor import colored
from nextcord import Embed
from nextwave import Player
from nextcord.ext import commands, tasks
import topgg


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

with open('./secrets/bot_token', 'r') as f:
    _token = f.read().strip()
with open('./secrets/topgg_token', 'r') as f:
    _topgg_token = f.read().strip()
restart_in = None
queues = []

bot = commands.Bot(command_prefix='hori/', intents=nextcord.Intents.all())


tgg = topgg.client.DBLClient(bot, _topgg_token, True)


@bot.event
async def on_command_error(ctx, error):
    pass


@bot.command('restart_presence')
async def cmd_restart_presence(ctx: commands.Context, minutes: int):
    global restart_in
    if (await bot.application_info()).owner.id == ctx.author.id:
        restart_in = minutes
        await ctx.reply('done')


@bot.command('restart_bot')
async def cmd_restart_bot(ctx: commands.Context):
    if (await bot.application_info()).owner.id == ctx.author.id:
        global queues, restart_in
        restart_in = 'restarting'
        print('Getting ready to reload bot...')
        queues, waiting, done = [], 0, 0

        async def fetch_guild_before(guild):
            nonlocal done
            vc: Player = guild.voice_client
            await guild.me.edit(nick=f'{bot.user.name} | Reloading!')
            if not vc.queue.is_empty and db.get_server(vc.guild.id)['radio_enabled'] == 0:
                queues.append(vc.channel, list(vc.queue))
            await vc.stop()
            done += 1

        async def fetch_guild_after(d):
            await d[0].connect()
            await d[0].guild.voice_client.queue.extend(d[1])

        for g in bot.guilds:
            if g.voice_client is not None:
                bot.loop.create_task(fetch_guild_before(g))
                waiting += 1

        print('Waiting...')
        while waiting != done:
            await asyncio.sleep(1)
        print('Reloading all extensions!')

        for ext in bot.extensions:
            print(f'Reloading extension\t{ext}')
            bot.reload_extension(ext)
        print(f'Everything is done! Restarting music player')

        restart_in = None
        for d in queues:
            bot.loop.create_task(fetch_guild_after(d))

        print(f'Restarting radio')
        for guild_id in db.get_servers():
            if db.get_server(guild_id)['radio_enabled'] == 0:
                continue
            try:
                await asyncio.create_task(radio.start_radio(bot, guild_id))
            except Exception as e:
                print(
                    f'Error occurred in start_radio({bot}, {guild_id}): {e}')
                traceback.print_exception(e)
        print('Finished reloading!')


@bot.event
async def on_ready():
    print('Loaded ', colored('Hori', 'magenta'), '!', sep='')
    for guild in bot.guilds:
        db.create_server(guild.id)
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


@tasks.loop(seconds=PRESENCE_LOOP_COOLDOWN * 2)
async def presence_loop():
    global restart_in
    if restart_in is 'restarting':
        await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.playing, name='Restarting bot!'), status=nextcord.Status.idle)
    elif restart_in is not None:
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

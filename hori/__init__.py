from nextcord import Colour
from json import load
__version__ = '1.0a'


with open('./secrets/guilds.json', 'r') as f:
    GUILDS = load(f)
PRESENCE_LOOP_COOLDOWN = 15


class CColour:
    dark_brown = Colour(0x340700)
    brown = Colour(0x5a2003)
    orange = Colour(0xbc3b06)
    light_orange = Colour(0xe6934a)

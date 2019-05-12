import discord
from discord.ext import commands
import discord.voice_client


TOKEN = '*'
bot = commands.Bot(command_prefix='!')

bot.run(TOKEN)

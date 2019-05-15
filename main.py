from discord.ext import commands
import discord.voice_client
from scripts import expand


token_file = open("token.txt", "r")
TOKEN = token_file.read()

bot = commands.Bot(command_prefix='!')

@bot.command()
async def add_expandable_channel(ctx, channel_name):
	await expand.add_expandable_channel(ctx, channel_name)


@bot.command()
async def t(ctx, channel_name):
	await expand.add_expandable_channel(ctx, channel_name)


@bot.event
async def on_ready():
	print("Bot is ready.")


@bot.event
async def on_voice_state_update(member, before, after):
	if not(before.channel is None):
		await user_left_channel(member, before, after)
	if not(after.channel is None):
		await user_joined_channel(member, before, after)


async def user_joined_channel(member, before, after):
	print("*User {0} joined {1}".format(member.name, after.channel.name))
	await expand.user_joined_channel(member, before, after)


async def user_left_channel(member, before, after):
	print("*User {0} left {1}".format(member.name, before.channel.name))
	await expand.user_left_channel(member, before, after)


bot.run(TOKEN)

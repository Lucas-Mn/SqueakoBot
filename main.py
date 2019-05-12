import discord
from discord.ext import commands
import discord.voice_client


TOKEN = '*'
bot = commands.Bot(command_prefix='!')


@bot.command()
async def add_expandable_channel(ctx, channel_name):
	xt = Expandable_Channel(find_voice_channel(ctx.guild, channel_name))
	if xt is None:
		await ctx.send("Channel {0} does not exist.".format(channel_name))
	else:
		expandable_channels.append(xt)
		await ctx.send("{0} is now expandable.".format(channel_name))


@bot.event
async def on_ready():
	print("Bot is ready.")


@bot.event
async def on_voice_state_update(member, before, after):
	await expand_voice_channels(member, before, after)


async def expand_voice_channels(member, before, after):
	# if user left channel
	if not(before.channel is None):
		debug_expand("*User left channel %s" % before.channel.name)
		await user_left_channel(member, before, after)
		return

	# if user joined channel
	if not(after.channel is None):
		debug_expand("*User joined channel %s" % after.channel.name)
		await user_joined_channel(member, before, after)


async def user_joined_channel(member, before, after):
	x = find_expandable_channel(after.channel.name)
	if x is None:
		debug_expand("--joined channel is not expandable")
		return
	else:
		debug_expand("--joined channel is expandable")
		await user_joined_expandable_channel(member, before, after, x)


async def user_joined_expandable_channel(member, before, after, expandable):
	new_channel_name = None

	if expandable.nxt is None:
		if expandable.previous is None:
			debug_expand("--channel is origin")
			new_channel_name = '{0} 2'.format(after.channel.name)
		elif expandable.previous_is_not_empty():
			debug_expand("--channel is not origin")
			new_channel_name = '{0} 3'.format(after.channel.name)
			# TODO Placeholder, must make dynamic
		# if all is good, create channel
		if not(new_channel_name is None):
			debug_expand("--new channel created")
			await after.channel.guild.create_voice_channel(new_channel_name, category=after.channel.category)
			expandable.nxt = Expandable_Channel(find_voice_channel(after.channel.guild, new_channel_name), expandable)
			expandable_channels.append(expandable.nxt)
			expandable.print()
			expandable.nxt.print()
	else:
		debug_expand("--there is already an expansion of this channel")


async def user_left_channel(member, before, after):
	x = find_expandable_channel(before.channel.name)
	if x is None:
		debug_expand("--channel is not expandable")
		return
	else:
		debug_expand("--channel is expandable")
		await user_left_expandable_channel(member, before, after, x)


async def user_left_expandable_channel(member, before, after, x):
	if len(before.channel.members) <= 0:  # if the channel is now empty
		debug_expand("--channel is empty")
		if x.nxt is None:  # and if it's the last channel in the chain
			debug_expand("--channel is last in chain")
			if not(x.previous is None):  # and if it's not the first one
				debug_expand("--channel is not origin")
				if len(find_voice_channel(after.channel.guild, x.previous.get_name()).members) <= 0:
					debug_expand("--previous channel is empty, deleting...")
					x.clear_others() # TODO: make it so that the next channel becomes this one
					expandable_channels.remove(x)
					await before.channel.delete()
					return
			else:
				debug_expand("--channel is origin")
		else:
			if x.previous is None: # if it's the origin
				next_channel = find_voice_channel(member.guild, x.nxt.get_name())
				if len(next_channel.members) <= 0: # if the next channel is empty
					await delete_expandable_channel(x.nxt, next_channel)
			else:
				debug_expand("--channel is not last in chain")
				nxt = find_voice_channel(member.guild, x.nxt.current.name)
				if len(nxt.members) <= 0 and not(x.previous is None):
					await before.channel.delete()
					x.previous.nxt = None
					expandable_channels.remove(x)


def find_voice_channel(guild: discord.guild, name):
	for x in guild.voice_channels:
		if x.name == name:
			return x
	return None


def find_expandable_channel(name):
	for x in expandable_channels:
		if x.get_name() == name:
			return x
	return None


expandable_channels = []


class Expandable_Channel:
	def __init__(self, current, previous=None):
		self.previous = previous
		self.current = current
		self.nxt = None

	def get_name(self):
		return self.current.name

	def previous_is_not_empty(self):
		return len(self.previous.get_members()) > 0

	def get_members(self):
		return self.current.members

	def clear_others(self):
		self.previous.nxt = None
		if not(self.nxt is None):
			self.nxt.previous = None

	def print(self):
		print("--*expandable channel '%s'" % self.current.name)
		self.print_previous()
		self.print_nxt()

	def print_previous(self):
		if self.previous is None:
			print("----previous channel is None")
		else:
			print("----previous channel is: '%s'" % self.previous.current.name)

	def print_nxt(self):
		if self.nxt is None:
			print("----next channel is None")
		else:
			print("----next channel is: '%s'" % self.nxt.current.name)

async def delete_expandable_channel(expandable, real_channel):
	expandable_channels.remove(expandable)
	expandable.clear_others()
	await real_channel.delete()

def debug_expand(str):
	print(str)


bot.run(TOKEN)

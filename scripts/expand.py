from discord.ext import commands
import discord.voice_client


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
		print("----index: %s" % self.get_index())

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

	def get_index(self):
		if self.previous is None:
			return 0
		return self.previous.get_index() + 1

async def add_expandable_channel(ctx, channel_name):
	xt = Expandable_Channel(find_voice_channel(ctx.guild, channel_name))
	if xt is None:
		await ctx.send("Channel {0} does not exist.".format(channel_name))
	else:
		expandable_channels.append(xt)
		await ctx.send("{0} is now expandable.".format(channel_name))


async def user_joined_channel(member, before, after):
	x = find_expandable_channel(after.channel.name)
	if x is None:
		debug_expand("--joined channel is not expandable")
		return
	else:
		debug_expand("--joined channel is expandable")
		await user_joined_expandable_channel(member, before, after, x)


async def user_left_channel(member, before, after):
	x = find_expandable_channel(before.channel.name)
	if x is None:
		debug_expand("--channel is not expandable")
		return
	else:
		debug_expand("--channel is expandable")
		await user_left_expandable_channel(member, before, after, x)


async def user_joined_expandable_channel(member, before, after, expandable):
	new_channel_name = None

	if expandable.nxt is None:
		if expandable.previous is None:
			debug_expand("--channel is origin")
			new_channel_name = '{0} 2'.format(after.channel.name)
		elif expandable.previous_is_not_empty():
			debug_expand("--channel is not origin")
			new_channel_name = clean_channel_name(after.channel.name) + (' %s' % (expandable.get_index() + 2))
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


async def user_left_expandable_channel(member, before, after, x):
	if len(before.channel.members) <= 0:  # if the channel is now empty
		debug_expand("--channel is empty")
		if x.nxt is None:  # and if it's the last channel in the chain
			debug_expand("--channel is last in chain")
			if not(x.previous is None):  # and if it's not the first one
				debug_expand("--channel is not origin")
				if after.channel is None or len(find_voice_channel(after.channel.guild, x.previous.get_name()).members) <= 0:
					debug_expand("--previous channel is empty, deleting...")
					x.clear_others()  # TODO: make it so that the next channel becomes this one
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


def clean_channel_name(str):
	string_index = None
	index = len(str)-1
	loop_count = 0  # this will ensure we're not iterating unnecessarily on a bad string
	while index >= 0:
		if str[index] == " ":
			string_index = index
			break
		else:
			index -= 1
			loop_count += 1
			if loop_count > 2:
				print("TRIED TO CLEAN INVALID CHANNEL NAME")
				break
	return str[:string_index]


async def delete_expandable_channel(expandable, real_channel):
	expandable_channels.remove(expandable)
	expandable.clear_others()
	await real_channel.delete()


def debug_expand(str):
	print(str)
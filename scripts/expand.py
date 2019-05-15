from discord.ext import commands
import discord.voice_client


class Expandable_Channel:
	def __init__(self, current, guild_id, previous=None):
		self.previous = previous
		self.current = current
		self.nxt = None
		self.guild_id = guild_id

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
	xt = Expandable_Channel(find_voice_channel(ctx.guild, channel_name), ctx.guild.id)
	if xt is None:
		await ctx.send("Channel {0} does not exist.".format(channel_name))
	else:
		add_expandable_to_dict(xt)
		await ctx.send("{0} is now expandable.".format(channel_name))


async def user_joined_channel(member, before, after):
	x = find_expandable_channel(after.channel.name, after.channel.guild)
	if x is None:
		debug_expand("--joined channel is not expandable")
		return
	else:
		debug_expand("--joined channel is expandable")
		await user_joined_expandable_channel(member, before, after, x)


async def user_left_channel(member, before, after):
	x = find_expandable_channel(before.channel.name, before.channel.guild)
	if x is None:
		debug_expand("--channel is not expandable")
		return
	else:
		debug_expand("--channel is expandable")
		await user_left_expandable_channel(member, before, after, x)


async def user_joined_expandable_channel(member, before, after, expandable):
	new_channel_name = None

	if expandable.nxt is None:  # if channel is not expanded yet
		if expandable.previous is None:  # if channel is origin
			debug_expand("--channel is origin")
			new_channel_name = '{0} 2'.format(after.channel.name)
		elif expandable.previous_is_not_empty():  # TODO: this is probably unnecessary
			debug_expand("--channel is not origin")
			new_channel_name = remake_channel_name(after.channel.name, expandable)
		# if all is good, create channel
		if not(new_channel_name is None):
			await after.channel.guild.create_voice_channel(new_channel_name, category=after.channel.category)
			channel = find_voice_channel(after.channel.guild, new_channel_name)
			await channel.edit(position=after.channel.position+1)
			expandable.nxt = Expandable_Channel(channel, expandable.guild_id, expandable)
			add_expandable_to_dict(expandable.nxt)  # NOTE: could skip duplication check
			debug_expand("--new channel created")
	else:
		debug_expand("--there is already an expansion of this channel")

	print_all_expandables()


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
					guilds[before.channel.guild.id].remove(x)
					await before.channel.delete()
			else:
				debug_expand("--channel is origin")
		else:
			debug_expand("--channel is not last in chain")
			if x.previous is None: # if it's the origin
				debug_expand("--channel is origin")
				next_channel = find_voice_channel(member.guild, x.nxt.get_name())
				if len(next_channel.members) <= 0: # if the next channel is empty
					await delete_expandable_channel(x.nxt, next_channel)
					debug_expand("--next channel was empty, so it was deleted")
			else:
				debug_expand("--channel is not origin")
				nxt = find_voice_channel(member.guild, x.nxt.current.name)
				if len(nxt.members) <= 0:  # if next channel is empty
					await nxt.delete()
					guilds[before.channel.guild.id].remove(x.nxt)
					x.nxt = None
					debug_expand("--next channel was empty, so it was deleted")
				else:  # if next channel has people
					debug_expand("--next channel is not empty")
					# bind surrounding channels together and remove x from list
					x_prev = x.previous
					x_nxt = x.nxt
					x_prev.nxt = x_nxt
					x_nxt.previous = x_prev
					guilds[before.channel.guild.id].remove(x)

					# delete channel and update next
					await before.channel.delete()
					await nxt.edit(name=remake_channel_name(nxt.name, x_nxt))
	print_all_expandables()

def find_voice_channel(guild: discord.guild, name):
	for x in guild.voice_channels:
		if x.name == name:
			return x
	return None


def find_expandable_channel(name, guild):
	for x in guilds[guild.id]:
		if x.get_name() == name:
			return x
	return None


# key: guild ID | value: a list of expandable channels
guilds = dict()


def add_expandable_to_dict(expandable):
	id = expandable.guild_id
	if id in guilds:
		# check that channel doesn't already exist
		for x in guilds[id]:
			if x.get_name() == expandable.get_name():
				debug_expand("tried to add %s to dictionary, but it already exists" % expandable.get_name())
				return
		guilds[id].append(expandable)
	else:
		guilds[id] = [expandable]


def print_all_expandables():
	for g in guilds:
		print("Guild %s expandables: " % g)
		for x in guilds[g]:
			x.print()


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


def remake_channel_name(str, expandable):
	return clean_channel_name(str) + (' %s' % (expandable.get_index() + 2))


async def delete_expandable_channel(expandable, real_channel):
	guilds[expandable.guild_id].remove(expandable)
	expandable.clear_others()
	await real_channel.delete()


def debug_expand(str):
	print(str)
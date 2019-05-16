from discord.ext import commands
import discord.voice_client


guilds = dict()


def load():
    file = open('config.txt')
    mode = 'start'
    guild = 0

    for line in file:

        if mode == 'start' or line.startswith('guild='):
            mode = 'guild'
            guild = clean_string(line[6:])
            guilds[guild] = dict()
        else:
            # split line into key : value
            s = line.split('=')
            s[1] = clean_string(s[1]) # remove /n
            # if there's already a list in that key, add value to it
            if s[0] in guilds[guild]:
                guilds[guild][s[0]].append(s[1])
            # else, create list with value in it
            else:
                guilds[guild][s[0]] = [s[1]]

    print('loaded the following settings: ')
    print_settings()


def save():
    file = open('config.txt', 'w')
    for g_key, g_value in guilds.items():
        file.write('guild=%s\n' % g_key)
        for s_key, s_value in g_value.items():
            for x in s_value:
                file.write('{0}={1}\n'.format(s_key, x))

    print('saved config file')


def add_value(guild, key, value):
    x = guilds[guild][key]
    if x is None:
        guilds[guild][key]=[value]
    else:
        x.append(value)


def print_settings():
    for g_key, g_value in guilds.items():
        print('-Guild: %s' % g_key)
        for s_key, s_value in g_value.items():
            print('--%s:' % s_key)
            for x in s_value:
                print('---%s' % x)


# removes \n from strings
def clean_string(str):
    if str[-1:] == '\n':
        return str[:-1]
    else:
        return str
import discord
import random
import requests as rq
import json

async def send_message(m, s):
    await m.channel.send(s)

class Command_parser:
    def __init__(self, commands=None, init_command_char='!'):
        self.init_command_char = init_command_char
        if commands is None:
            self.__commands__ = {}
        else:
            self.__commands__ = commands

    def add_command(self, name, f):
        if name not in self.__commands__:
            self.__commands__[name] = f
            return True
        return False

    def remove_command(self, name):
        if name in self.__commands__:
            del self.__commands__[name]
            return True
        return False

    async def parse(self, m):
        s = m.content
        if s.startswith(self.init_command_char):
            s = s[1:]
        else: return
        for k in self.__commands__.keys():
            if s.startswith(k):
                await(self.__commands__[k](argv=[m] + s[len(k)+1:].split(' ')))
                break


all_skills = {'Agility', 'Construction',
    'Cooking', 'Crafting', 'Farming',
    'Firemaking', 'Fishing', 'Fletching',
    'Herblore', 'Hunter', 'Mining',
    'Runecraft', 'Smithing', 'Thieving',
    'Woodcutting'}
async def roll_a_random_skill(argv, loc='chosen_skills.txt'):
    # read from files which skills were used previously
    try:
        with open(loc, 'r') as f:
        prev_skills = set(f.readlines().split())
    # if no such file exists, create an empty file
    except:
        open(loc, 'w').close()
        prev_skills = set()

    # possible skills to roll are all skills except previously rolled skills
    skill_rolls = all_skills.difference(prev_skills)
    # roll for random skill
    rolled_skill = random.choice(skill_rolls)
    # if only one left skill to chose from, reset file
    if len(skill_rolls) == 1:
        open(loc, 'w').close()
    # write away chosen skill so we don't pick it again until all skills have been chosen
    with open(loc, 'a') as f:
        f.write(f'{rolled_skill}\n')

    await argv[0].channel.send(rolled_skill)


async def auto_nicknames(argv):
    message = argv[0]
    if not len(json.loads(rq.get('https://api.wiseoldman.net/players/search?username='+ message.content.split(' ', 1)[1]).text)) == 1: return
    if 'Unverified' in map(lambda x:x.name, message.author.roles):
        await message.author.remove_roles([r for r in message.guild.roles if r.name=="Unverified"][0])
        await message.author.add_roles([r for r in message.guild.roles if r.name=="Awaiting Rank"][0])
        await message.author.edit(nick=message.content.split(' ', 1)[1])
        await message.channel.send('%s has successfully been verified, welcome to the server!' % message.author.name)
    else:
        await message.author.edit(nick=message.content.split(' ', 1)[1])

    # currently seems like WOM api doesn't handle track requests based solely username. It'll have to be implemented later
    #elif len(json.loads(rq.get('https://api.wiseoldman.net/players/track', json={'username':message.content.split(' ', 1)[1]}).text)) > 1:
    #    print(json.loads(rq.get('https://api.wiseoldman.net/players/track', json={'username':message.content.split(' ', 1)[1]}).text))
    #    await message.channel.send('Your username wasn\'t tracked on the WiseOldMan. I fixed that for you, please try again!')





ints = discord.Intents.all()
ints.presences = False
client = discord.Client(intents=ints)
c_parser = Command_parser(
    commands={
        'setrsn': auto_nicknames,
        'random skill': roll_a_random_skill
    }
)


@client.event
async def on_ready():
    print('logged in as {0.user}'.format(client))
@client.event
async def on_member_join(member):
    await member.add_roles([r for r in member.guild.roles if r.name=="Unverified"][0])
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await c_parser.parse(message)

if __name__ == '__main__':
    client.run('')

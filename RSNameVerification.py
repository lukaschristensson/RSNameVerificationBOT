import discord
import random
import requests as rq
import json


guild_settings = {}
base_settings = {
    'basinga': None
}



def settings_controller(guild, message):
    if message == '!basinga on' and guild_settings[guild]['basinga'] is None:
        guild_settings[guild]['basinga'] = basinga
        guild_basinga_phrase[guild] = random.choice(basinga_phrase_options)
    elif message == '!basinga off':
        guild_settings[guild]['basinga'] = None



basinga_phrase_options = ['area', 'book', 'business', 'case', 'child', 'company', 'country', 'day', 'eye', 'fact', 'family', 'government', 'group', 'hand', 'home', 'job', 'life', 'man', 'money', 'month', 'mother', 'night', 'number', 'part', 'people', 'place', 'point', 'problem', 'program', 'question', 'room', 'school', 'state', 'story', 'student', 'study', 'system', 'thing', 'time', 'water', 'woman', 'word', 'work', 'world', 'year']
guild_basinga_phrase = {}

async def basinga(guild, message):
    if guild in guild_basinga_phrase:
        if guild_basinga_phrase[guild] in message.content:
            await message.channel.send('Bazinga!!')
            guild_basinga_phrase[guild] = random.choice(basinga_phrase_options)



ints = discord.Intents.all()
ints.presences = False
client = discord.Client(intents=ints)

@client.event
async def on_ready():
    print('logged in as {0.user}'.format(client))

@client.event
async def on_member_join(member):
    await member.add_roles([r for r in member.guild.roles if r.name=="Unverified"][0])
    print('new member joined: %s' % member.name)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    #for (s, f) in guild_settings[message.guild]:
    #    if f: f(message.guild, message.content)
    if message.content.startswith('!setrsn') and 'Unverified' in map(lambda x:x.name, message.author.roles):
        if len(json.loads(rq.get('https://api.wiseoldman.net/players/search?username='+ message.content.split(' ', 1)[1]).text)) == 1:
            await message.author.remove_roles([r for r in message.guild.roles if r.name=="Unverified"][0])
            await message.author.add_roles([r for r in message.guild.roles if r.name=="Awaiting Rank"][0])
            await message.author.edit(nick=message.content.split(' ', 1)[1])
            await message.channel.send('%s has successfully been verified, welcome to the server!' % message.author.name)
    elif message.content.startswith('!setrsn') and len(json.loads(rq.get('https://api.wiseoldman.net/players/search?username='+ message.content.split(' ', 1)[1]).text)) == 1:
            await message.author.edit(nick=message.content.split(' ', 1)[1])

        # currently seems like WOM api doesn't handle track requests based solely username. It'll have to be implemented later
        #elif len(json.loads(rq.get('https://api.wiseoldman.net/players/track', json={'username':message.content.split(' ', 1)[1]}).text)) > 1:
        #    print(json.loads(rq.get('https://api.wiseoldman.net/players/track', json={'username':message.content.split(' ', 1)[1]}).text))
        #    await message.channel.send('Your username wasn\'t tracked on the WiseOldMan. I fixed that for you, please try again!')

if __name__ == '__main__':
    client.run('TokenWhichIForgotToDeleteLikeADumbass')

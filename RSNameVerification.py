import discord
import requests as rq
import psycopg2
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

clapo_help  = """ 
!clapo setname <your_name>
    Sets the corresponding rsn for you on this server to be <your_name>.
!clapo setclan <your_clan>
    Sets the clan for this discord server to <your_clan>, this is needed for most commands.
!clapo set_admin_channel
    Sets the current channel as the admin channel. This means that the channel in which this is written is
    the only channel allowed to call privileged commands.
!clapo remove_admin_channel
    Unsets the current channel as the admin channel. This is needed if you want to change which
    channel is considered the admin channel.
!clapo h
!clapo help
!clapo ?
!clapo
    Brings up this help window.
!clapo add <amount> <rsn>
    Adds <amount> points to the player <rsn> if this player is part of your clan
    If <rsn> is set to ALL then all players in the clan will receive <amount> of points.
!clapo get
    Gets the current points for the clan member who called the account
    Using the keyword ALL after get gets all the members and their corresponding point count.

"""
async def CLAPO(argv):
    if len(argv) == 1 or argv[1] in ['help', 'h', '?' ,'']:
        await argv[0].channel.send(clapo_help)
        return
    authorized_channel = (
            str(argv[0].guild.id) not in clapo_authorized_admin_channel or
            clapo_authorized_admin_channel[str(argv[0].guild.id)] =='' or
            argv[0].channel.name == clapo_authorized_admin_channel[str(argv[0].guild.id)]
    )
    if len(argv) > 2 and argv[1] == 'setclan' and authorized_channel:
        clapo_clan_discord[str(argv[0].guild.id)] = ' '.join(argv[2:])
        save_config('clapo_config',
                    where={
                        'guild_id': argv[0].guild.id
                    },
                    clan_name=' '.join(argv[2:])
                    )
        await argv[0].channel.send('clan set: ' + clapo_clan_discord[str(argv[0].guild.id)])
        return
    elif len(argv) > 1 and argv[1] == 'set_admin_channel' and authorized_channel:
        clapo_authorized_admin_channel[str(argv[0].guild.id)] = argv[0].channel.name
        save_config('clapo_config',
                    where={
                        'guild_id': argv[0].guild.id
                    },
                    admin_channel_name=str(argv[0].channel.name)
                    )
        await argv[0].channel.send('admin channel set: ' + str(clapo_authorized_admin_channel[str(argv[0].guild.id)]))
        return
    elif len(argv) > 1 and argv[1] == 'remove_admin_channel' and authorized_channel:
        del clapo_authorized_admin_channel[str(argv[0].guild.id)]
        save_config('clapo_config',
                    where={
                        'guild_id': argv[0].guild.id
                    },
                    admin_channel_name=''
                    )
        await argv[0].channel.send('admin channel removed' )

    if str(argv[0].guild.id) not in clapo_clan_discord:
        await argv[0].channel.send('You have not yet set your clan. Please set your clan with "!clapo setclan your_clan_name".')
        return

    if len(argv) > 2 and argv[1] == 'setname':
        if rq.post(clapoURL, params={'rsn': ' '.join(argv[2:]), 'a': 0,
                                  'clan_name': clapo_clan_discord[str(argv[0].guild.id)]}).content.decode():
            clapo_user_guild_rsn[(argv[0].guild.id, argv[0].author.id)] = ' '.join(argv[2:])
            save_config('clapo_user_rsn',
                        where={
                            'guild_id': argv[0].guild.id,
                            'discord_user_id': argv[0].author.id
                        },
                        rsn=' '.join(argv[2:])
                        )
            await argv[0].channel.send('Your name has been set to: '+str(' '.join(argv[2:])))
        else:
            await argv[0].channel.send('There is no such user in this clan')

        return

    if len(argv) > 1 and argv[1] == 'get':
        resp = rq.get(clapoURL, params={'clan_name': clapo_clan_discord[str(argv[0].guild.id)]}).content.decode().replace('\'', '"')
        if resp is None or resp == 'None':
            await argv[0].channel.send('There are no members for clan: '+str(clapo_clan_discord[str(argv[0].guild.id)]))
            return
        user_data = json.loads(resp)
        send_args = []
        if len(argv) > 2 and argv[2] == 'ALL':
            for m in user_data:
                send_args.append(str(m['rsn'])+': '+str(m['points']))
        else:
            if (str(argv[0].guild.id), str(argv[0].author.id)) not in clapo_user_guild_rsn:
                send_args.append('You haven\'t set your name, please do so with !clapo setname your_rsn_here')
            else:
                for m in user_data:
                    if m['rsn'] == clapo_user_guild_rsn[(str(argv[0].guild.id), str(argv[0].author.id))]:
                        send_args.append(str(m['rsn'])+': '+str(m['points']))
                        break

        await argv[0].channel.send('\n'.join(send_args))
        return

    if len(argv) > 3 and argv[1] == 'add' and (argv[2].isnumeric() or (argv[2][0] == '-' and argv[2][1:].isnumeric())) and authorized_channel:
        new_balance = rq.post(clapoURL, params={'rsn': ' '.join(argv[3:]), 'a':argv[2], 'clan_name': clapo_clan_discord[str(argv[0].guild.id)]}).content.decode()[1:-1].split(',')
        if new_balance[0] == '':
            await argv[0].channel.send('No such player in the clan: '+(' '.join(argv[3:])))
            return
        if argv[3] != 'ALL':
            await argv[0].channel.send('Transaction complete\n'+new_balance[0]+': '+new_balance[1])
        else:
            await argv[0].channel.send('Transaction complete\nALL: +' + argv[2])

async def auto_nicknames(argv):
    message = argv[0]
    if not len(json.loads(rq.get('https://api.wiseoldman.net/players/search?username='+ message.content.split(' ', 1)[1]).text)) == 1:return
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
        'clapo': CLAPO
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

def load_config(table, **kwargs):
    if 'where' in kwargs and len(kwargs['where']) == 0:
        del kwargs['where']


    where_columns = []
    where_values = []
    if 'where' in kwargs:
        for (k, v) in kwargs['where'].items():
            where_columns += k
            where_values += v     # this way insures that the order of values and columns are always correct
    cur.execute(
                'SELECT ' + (', '.join(kwargs['values']))+' FROM '+table+
                ((' WHERE '+(' AND '.join([k + '=%s' for k in where_columns])) ) if 'where' in kwargs else ''),
                where_values
    )
    return cur.fetchall()

def save_config(table, **kwargs):
    if 'where' in kwargs and len(kwargs['where']) == 0:
        del kwargs['where']

    columns = []
    values = []
    for (k, v) in kwargs.items():
        if k != 'where':    # where is a protected keyword in this context
            columns.append(str(k))
            values.append(str(v))     # this way insures that the order of values and columns are always correct

    where_columns = []
    where_values = []
    if 'where' in kwargs:
        for (k, v) in kwargs['where'].items():
            where_columns.append(str(k))
            where_values.append(str(v))

    try:
        cur.execute('INSERT INTO '+table+
                    '(' + (','.join(columns+where_columns)) + ')'
                    ' VALUES '
                    '('+(', '.join(['%s']*(len(values) + len(where_values)))) + ')',
                    values+where_values
                    )
    except:
        db_conn.rollback()
    if 'where' in kwargs:
        cur.execute('UPDATE '+table+ ' SET ' +
                    (', '.join([str(k + '=%s') for k in columns]))+
                    ' WHERE ' +
                    (' AND '.join([str(k + '=%s') for k in where_columns])),
                    values+where_values)
    db_conn.commit()

if __name__ == '__main__':
    db_conn = psycopg2.connect(
    )
    cur = db_conn.cursor()

    clapo_clan_discord = {}
    clapo_authorized_admin_channel = {}
    clapo_user_guild_rsn = {}

    for (k, v) in load_config('clapo_config', values=['guild_id', 'clan_name']):
        if v != '':
            clapo_clan_discord[str(k)] = str(v)
    for (k, v) in load_config('clapo_config', values=['guild_id', 'admin_channel_name']):
        if v != '':
            clapo_authorized_admin_channel[str(k)] = str(v)
    for (k0, k1, v) in load_config('clapo_user_rsn', values=['guild_id', 'discord_user_id', 'rsn']):
        if v != '':
            clapo_user_guild_rsn[(str(k0), str(k1))] = str(v)

    client.run()

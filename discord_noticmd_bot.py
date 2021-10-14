import os, sys
import asyncio
from io import TextIOWrapper
import json
from datetime import datetime
import discord
from discord import utils
from discord.enums import TeamMembershipState
from My_Logger import *


# setup discord client
intents = discord.Intents(guilds=True, members=True, messages=True)
client = discord.Client(intents=intents)
channel:discord.TextChannel

# setup global variable
DATA:str = ""
MENTION_STR:str = ""

# setup config variable
SAMPLE_CONFIG:str = """
{
    "fifo_path": "",
    "discord_token": "",
    "discord_guild_id": 0,
    "discord_channel_id": 0,
    "admin_discord_name": ""
}
"""
CONFIG:dict

# setup fifo variable
fifo_listener = asyncio.get_event_loop()
fifo:TextIOWrapper



def init_config() -> None:
    try:
        with open("./config.json", 'r') as configfile:
            global CONFIG
            CONFIG = json.load(configfile)
    except FileNotFoundError:
        broadcastErrorMsg("Cannot find \"config.json\" under current directory.")
        broadcastErrorMsg("Creating new \"config.json\"...")
        with open("./config.json", 'w') as configfile:
            json.dump(SAMPLE_CONFIG, configfile)
        broadcastErrorMsg("Please fill in all information in \"config.json\" and then run this script again.")
        # exit
        try:
            sys.exit(-1)
        except SystemExit:
            os._exit(-1)

async def init_fifo() -> None:
    "Open/Create fifo for message piping"
    global fifo
    if os.path.exists(CONFIG["fifo_path"]):
        fd = os.open(CONFIG["fifo_path"], os.O_RDONLY | os.O_NONBLOCK, 0)
        fifo = os.fdopen(fd, 'r', encoding="utf-8")
    else: # create new fifo
        try:
            os.mkfifo(CONFIG["fifo_path"])
            fd = os.open(CONFIG["fifo_path"], os.O_RDONLY | os.O_NONBLOCK, 0)
            fifo = os.fdopen(fd, 'r', encoding="utf-8")
        except Exception as err:
            broadcastErrorMsg(err)
            os._exit(-1)


@client.event
async def on_ready():
    
    # setup global var channel
    guild:discord.Guild = discord.utils.get(client.guilds, id=CONFIG["discord_guild_id"])
    global channel
    channel = discord.utils.get(guild.channels, id=CONFIG["discord_channel_id"])
    
    broadcastInfoMsg(f"Notification in Guild: {guild}")
    broadcastInfoMsg(f"Notification in Channel: {channel}")
    
    # get admin's mention string e.g. <@admin_id>
    global MENTION_STR
    if len(MENTION_STR) == 0:
        for member in guild.members:
            if str(member) == "Gavin1937#8571":
                mention_member:discord.Member = member
                MENTION_STR = member.mention
                break
        
        broadcastInfoMsg(f"Admin is: {mention_member}")
        broadcastInfoMsg(f"Admin MENTION_STR: {MENTION_STR}")
    
        # init fifo & enter fifo_waiting_loop
        await fifo_listener.create_task(init_fifo())
        await fifo_listener.create_task(fifo_waiting_loop())

@client.event
async def on_resumed():
    # go back to fifo_waiting_loop
    await fifo_listener.create_task(fifo_waiting_loop())

@client.event
async def on_message(message:discord.message):
    if message.author != client.user:
        broadcastInfoMsg(f"{message.author} says: {message.content}")
        await asyncio.sleep(0.25)

@client.event
async def on_new_data(has_data):
    await send_msg()

async def send_msg():
    global channel
    
    # split DATA if it is too big
    # discord.Channel.send() max msg length is 2000
    # leave 50 bytes for MENTION_STR
    data_list = []
    bdata = bytes(DATA.encode("utf-8"))
    old_idx = 0
    tmp_list = [0, ""]
    while tmp_list[0] < len(bdata):
        tmp_list = cutUStrByBytes(
            bdata[tmp_list[0]:].decode("utf-8"),
            1950
        )
        tmp_list[0] += old_idx
        old_idx = tmp_list[0]
        data_list.append(tmp_list[1])
    
    # send all msgs in data_list
    for msg in data_list:
        if msg[0] == '@' and msg[1] == ' ':
            loc_msg = msg.replace('@', MENTION_STR)
        else:
            loc_msg = msg
        
        broadcastInfoMsg(f"Sending Message: {loc_msg}")
        await channel.send(loc_msg)
    
    await asyncio.sleep(0)

async def online_msg():
    global channel
    msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] discord-noticmd-bot online!"
    broadcastInfoMsg(msg)
    await channel.send(msg)

def offline_msg():
    msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] discord-noticmd-bot offline!"
    broadcastInfoMsg(msg)

@client.event
async def read_fifo() -> None:
    global DATA
    DATA = fifo.read()
    if len(DATA) > 0: # has new data
        client.dispatch("new_data", True)
    await asyncio.sleep(0.25)

@client.event
async def fifo_waiting_loop() -> None:
    await online_msg()
    while True:
        await read_fifo()


def cutUStrByBytes(data:str, max_byte:int) -> list:
    """
    Cut input \"data\" string to a new string within \"max_byte\".\n
    If \"data\" is a utf-8 string, this function can keep its completion.
    list[0] is byte index of input data
    list[0] is cut unicode string
    """
    
    bdata = bytes(data.encode("utf-8"))
    blength = len(bdata)
    idx = max_byte
    
    # go to last complete unicode character
    if blength > max_byte:
        while ((bdata[idx] & 0xc0) == 0x80):
            # current byte is middle byte of an unicode character
            idx -= 1 # move backward
    
    # after if statement above, idx is at
    # one byte after the last complete unicode character
    # return all characters from 0 to (idx-1)
    return [idx, bdata[:idx].decode("utf-8")]


if __name__ == "__main__":
    try:
        init_config()
        client.run(CONFIG["discord_token"])
        
        # post processing
        offline_msg()
        fifo_listener.stop()
        fifo.close()
        client.loop.stop()
        asyncio.get_event_loop().stop()
        
    except KeyboardInterrupt:
        print()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

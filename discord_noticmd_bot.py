import os, sys
import asyncio
from io import TextIOWrapper
import json
from time import time
import traceback
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
fifo_task:asyncio.Task
fifo:TextIOWrapper



def init_config() -> None:
    try:
        with open("./config.json", 'r') as configfile:
            global CONFIG
            CONFIG = json.load(configfile)
    except FileNotFoundError:
        logger.error("Cannot find \"config.json\" under current directory.")
        logger.error("Creating new \"config.json\"...")
        with open("./config.json", 'w') as configfile:
            json.dump(SAMPLE_CONFIG, configfile)
        logger.error("Please fill in all information in \"config.json\" and then run this script again.")
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
            logger.error(err)
            os._exit(-1)

async def close_fifo() -> None:
    global fifo
    fifo.close()

async def reinit_fifo() -> None:
    "Call close_fifo() and then init_fifo()"
    await close_fifo()
    await init_fifo()


@client.event
async def on_ready():
    
    # setup global var channel
    guild:discord.Guild = discord.utils.get(client.guilds, id=CONFIG["discord_guild_id"])
    global channel
    channel = discord.utils.get(guild.channels, id=CONFIG["discord_channel_id"])
    
    logger.info(f"Notification in Guild: {guild}")
    logger.info(f"Notification in Channel: {channel}")
    
    # get admin's mention string e.g. <@admin_id>
    global MENTION_STR
    if len(MENTION_STR) == 0:
        for member in guild.members:
            if str(member) == CONFIG["admin_discord_name"]:
                mention_member:discord.Member = member
                MENTION_STR = member.mention
                break
        
        logger.info(f"Admin is: {mention_member}")
        logger.info(f"Admin MENTION_STR: {MENTION_STR}")
    
        # init fifo & enter fifo_waiting_loop
        await fifo_listener.create_task(init_fifo())
        await online_msg()
        global fifo_task
        fifo_task = asyncio.ensure_future(fifo_waiting_loop())

@client.event
async def on_resumed():
    # reopen fifo & go back to fifo_waiting_loop
    await fifo_listener.create_task(reinit_fifo())
    msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] discord-noticmd-bot online!"
    logger.info(msg)
    global fifo_task
    fifo_task.cancel()
    fifo_task = asyncio.ensure_future(fifo_waiting_loop())

@client.event
async def on_message(message:discord.message):
    if message.author != client.user:
        logger.info(f"{message.author} says: {message.content}")
        await asyncio.sleep(0.25)

@client.event
async def on_new_data(has_data):
    await send_msg()

async def send_msg():
    global channel
    
    # split DATA if it is too big
    # discord.Channel.send() max msg length is 2000
    # leave 150 bytes for MENTION_STR
    data_list = []
    bdata = bytes(DATA.encode("utf-8"))
    old_idx = 0
    tmp_list = [0, ""]
    while tmp_list[0] < len(bdata):
        tmp_list = cutUStrByBytes(
            bdata[tmp_list[0]:].decode("utf-8"),
            1850
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
        
        logger.info(f"Sending Message: {loc_msg}")
        await channel.send(loc_msg)
    
    await asyncio.sleep(0)

async def online_msg():
    global channel
    msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] discord-noticmd-bot online!"
    logger.info(msg)
    await channel.send(msg)

def offline_msg():
    msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] discord-noticmd-bot offline!"
    logger.info(msg)

@client.event
async def read_fifo() -> None:
    global DATA
    DATA = fifo.read()
    if len(DATA) > 0: # has new data
        # reinit fifo after successfully read data
        await fifo_listener.create_task(reinit_fifo())
        # trigger new_data event to handle data from fifo
        client.dispatch("new_data", True)
    await asyncio.sleep(1)

@client.event
async def fifo_waiting_loop() -> None:
    while True:
        await read_fifo()


def cutUStrByBytes(data:str, max_byte:int) -> list:
    """
    Cut input \"data\" string to a new string within \"max_byte\".\n
    If \"data\" is a utf-8 string, this function can keep its completion.
    list[0] is byte index of input data
    list[1] is cut unicode string
    """
    
    bdata = bytes(data.encode("utf-8"))
    blength = len(bdata)
    idx = max_byte
    
    # go to last complete unicode character
    if blength > max_byte:
        while ((bdata[idx] & 0xc0) == 0x80):
            # current byte is middle byte of an unicode character
            idx -= 1 # move backward
    
    # after the if statement above, idx is at
    # one byte after the last complete unicode character
    # return all characters from 0 to (idx-1)
    return [idx, bdata[:idx].decode("utf-8")]


def incr_sleep(step):
    sleep_time = round( (1.3**step) * 600 )
    logger.info(f"Sleep for {sleep_time/60} minutes")
    sleep(sleep_time)

if __name__ == "__main__":
    stop_loop = False
    max_retry = 10
    retry_count = 0
    while not stop_loop and retry_count < max_retry:
        try:
            init_config()
            client.run(CONFIG["discord_token"])
            
            # post processing
            offline_msg()
            fifo.close()
            fifo_listener.stop()
            fifo_task.cancel()
            client.loop.stop()
            asyncio.get_event_loop().stop()
            
            stop_loop = True
            
        except KeyboardInterrupt:
            print()
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        except Exception as err:
            print(traceback.format_exc())
            stop_loop = False
            retry_count += 1
            incr_sleep(retry_count)

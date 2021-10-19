
# discord-noticmd-bot

<span style="font-size:1.5em;">
A Discord Bot to handle Notification & Command using fifo (named pipe)
</span>
</br>
<span style="font-size:1.5em;">
<strong>This script ONLY WORK FOR Linux</strong>
</span>


## Requirements

| Package    | Version                                |
|------------|----------------------------------------|
| discord.py | latest (older version should work too) |

### run following script to install required package
```sh
pip install discord.py
```

### Setup Discord Bot
Checkout [This Tutorial](https://www.freecodecamp.org/news/create-a-discord-bot-with-python/)

### Make sure you have token for your discord bot 

### Make sure you create a new Discord guild/server


## Configuration

You need to provide a **config.json** for the script.
Here is a sample config template
```
{
    "fifo_path": "",          // Path to fifo, if fifo does not exist, script will create one
    "discord_token": "",      // Discord bot token
                              // 
    "discord_guild_id": 0,    // Discord guild (server) id
    "discord_channel_id": 0,  // Discord channel id
                              // A guild to find these ids:
                              // https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-
                              // I suggest login to discord on a browser and
                              // searching for guild id & channel id in url
                              // 
    "admin_discord_name": ""  // User you want the bot to notify.
                              // You Must Enter the actual username (not nickname in server) + user discriminator.
                              // e.g. DiscordUserName#12345
}
```


## Running

To start the bot, simply run following command after you setup your **config.json**
```sh
python discord_noticmd_bot.py
```
After the script outputting an online message, You can start sending message to fifo


## Testing

To test the bot, you can run following command to let it send a greeting message.

```sh
bash greeting.sh your_fifo_filename
```


## How It Works?

**discord_noticmd_bot.py** will create a fifo pipe (if not exist) and constantly trying to read from it.

Then, when you write to that fifo from another program, **discord_noticmd_bot.py** will catch the data and send it to Discord channel. 

[More About fifo](https://linux.die.net/man/7/fifo)


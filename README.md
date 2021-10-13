
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

## Configuration

You need to provide a **config.json** for the script.
Here is a sample config file
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

To run the script, simply run following command after you setup the **config.json**
```sh
python discord_noticmd_bot.py
```
After script outputting an online message, You can start sending message to fifo


## Testing

After you setup the script & successfully run it.

You can run following command to test it.

```sh
bash greeting.sh your_fifo_filename
```


## How It Works?

**discord_noticmd_bot.py** will create a fifo (if not exist) and constantly trying to read from it.

Then, when you write to that fifo from another program, **discord_noticmd_bot.py** will catch that data and send it to Discord channel. 

[More About fifo](https://linux.die.net/man/7/fifo)


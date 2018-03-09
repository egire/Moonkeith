# Moonkeith Discord Bot V0.2.5
> Discord bot with Beagle Bone Black commands

Discord bot with the abilities to fetch memes and display memes to a Beagle Bone Black. The bot can test pins on the BBB.

## Current features:
* Command character configuration
* Administrators configuration
* Catch phrases configuration
* Post fortunes to channel
* Post memes to channel
* Test pins on a BBB (blink pin, set voltage high/low)
* Compare steam game account and choose a common random multiplayer
* Say random phrases
* Display memes on BBB LCD screen
* Update itself from github

## Commands:
* !free: List of free game keys to channel
* !game [acc1] [acc2]: Posts random multiplayer game from both steam libraries
* !g2a [game name: Posts the first result from G2A.com (game title, price, url)
* !steam [game name]: Posts the first result from steampowered.com (game title, price, url)
* !pin [pin name] [high/low/blink ([# blinks] [delay in secs])]: Tests a pin on the BBB
* !meme: Posts random meme to channel
* !fortune: Read off random fortune cookie
* !spew: Spew random phrase
* !purge: Remove all bot messages from channel
* !restart: Updates and restarts the bot
* !quit: Kills the bot

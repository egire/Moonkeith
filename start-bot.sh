#!/bin/bash

echo "Updating bot..."
/home/debian/update-bot.sh

echo "Running bot..."
cd /home/debian/discord-bot/Moonkeith/
python3 bot.py > /dev/null &

import sys, os, time, random
import discord, urllib, json, asyncio
#from PIL import Image
from bs4 import BeautifulSoup
from steam import SteamGameGrabber
from pinout import PIN

if sys.platform == "linux" or sys.platform == "linux2":
    import Adafruit_BBIO.GPIO as GPIO
elif sys.platform == "win32":
    GPIO = False

client = discord.Client()
phrases = []
admins = []
ctrl = '!'
maxblink = 0
commands = {'free': 'Posts list of free game keys to channel', 'meme': 'Posts random meme to channel', 'fortune':'Read off random fortune cookie', 'steam [acc1] [acc2]': 'Posts random multiplayer game from both steam libraries', 'purge':'Remove all posts from channel', 'spew':'Spew random phrase', 'quit': 'Kills the bot', 'pin [pin name] [high/low/blink ([# blinks] [delay in secs])] ': 'tests a pin on the BBB', 'restart':'Updates and restarts the bot'}

def fetch_html(url):
    headers = {}
    headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0'
    req = urllib.request.Request(url, headers = headers)
    html = urllib.request.urlopen(req).read()
    return html
    
def is_me(m):
    return m.author == client.user

def load_admins():
    global admins
    admins_file = open("./admins.txt", "r")
    admins = admins_file.read().splitlines()
    admins_file.close()

def is_admin(user):
    global admins
    return (str(user) in admins)
    
def load_phrases():
    global phrases
    phrases_file = open("./phrases.txt", "r")
    phrases = phrases_file.read().splitlines()
    phrases_file.close()
    
def rand_phrase():
    global phrases
    random.seed()
    phrase_num = random.randrange(0, len(phrases))
    phrase = phrases[phrase_num]
    return phrase

def gpio_init():
    if(GPIO == False):
        return
    GPIO.setup(PIN['BUZZER'], GPIO.OUT)
    GPIO.output(PIN['BUZZER'], GPIO.HIGH)

@client.event
async def on_ready():
    gpio_init()
    load_phrases()
    load_admins()
    print('Admins file loaded: ' + str(admins))
    print('Phrase file loaded, ' + rand_phrase() +'.')
    random.seed()
    print('Logged in as ' + client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if is_me(message):
        return
        
    elif message.content.startswith(ctrl+'test1'):
        counter = 0
        tmp = await client.send_message(message.channel, 'Calculating messages...')
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1
        await client.edit_message(tmp, 'You have {} messages.'.format(counter))

    elif message.content.startswith(ctrl+'help'):
        for command, desc in commands.items():
            await client.send_message(message.author, ctrl+command+": "+desc)
   
    elif message.content.startswith(ctrl+'sleep'):
        await asyncio.sleep(5)
        await client.send_message(message.channel, 'Done sleeping')
    
    elif message.content.startswith(ctrl+'free'):
        page = fetch_html('https://www.reddit.com/r/FreeGameFindings/')
        soup = BeautifulSoup(page, 'html.parser')
        for a in soup.find_all('a', attrs={'class': 'title'}):
            game = a.text + ' - ' + a['href']
            await client.send_message(message.channel, game)
    
    elif message.content.startswith(ctrl+'meme'):
        page = fetch_html('https://www.memecenter.com/')
        soup = BeautifulSoup(page, 'html.parser')
        url = soup.find('a', attrs={'class': 'random'})
        meme = fetch_html(url['href'])
        soup = BeautifulSoup(meme, 'html.parser')
        img = soup.find('img', attrs={'class': 'rrcont'})
        await client.send_message(message.channel, img['src'])
    
    elif message.content.startswith(ctrl+'fortune'):
        id = random.randrange(1,152)
        page = fetch_html('http://www.myfortunecookie.co.uk/fortunes/' + str(id))
        soup = BeautifulSoup(page, 'html.parser')
        fortune = soup.find('div', attrs={'class': 'fortune'})
        await client.send_message(message.channel, fortune.text)
        
    elif message.content.startswith(ctrl+'steam'):
        msg = message.content.split(' ')
        if (len(msg) < 3) :
            await client.send_message(message.channel, 'Invalid command format.')
            return
        first_acc = SteamGameGrabber()
        facc_result = first_acc.call_all(msg[1])
        second_acc = SteamGameGrabber()
        sacc_result = second_acc.call_all(msg[2])
        if isinstance(facc_result, dict) and isinstance(sacc_result, dict):
            facc = set(facc_result.items())
            sacc = set(sacc_result.items())
            games = facc & sacc
            game = []
            while True:
                game = random.sample(games, 1)
                with urllib.request.urlopen('http://store.steampowered.com/api/appdetails/?appids=' + game[0][1]) as url:
                    data = json.loads(url.read().decode())
                    break
                    for category in data[str(game[0][1])]['data']['categories']:
                        if category['description'] is 'Multiplayer':
                            break
            await client.send_message(message.channel, 'Play ' + str(game[0][0]) + ', ' + rand_phrase() +'.')
    
    elif message.content.startswith(ctrl+'purge'):
        msg = message.content.split(' ')
        author = msg[1]
        if(not (is_admin(message.author))):
            await client.send_message(message.author, 'You are not an admin, ' + rand_phrase()+'.')
            return
        await client.purge_from(message.channel, limit=100, check=(message.author==author))
        await client.send_message(message.channel, rand_phrase())
    
    elif message.content.startswith(ctrl+'spew'):
        await client.send_message(message.channel, rand_phrase())
    
    elif message.content.startswith(ctrl+'pin'):
        if(GPIO == False):
            await client.send_message(message.author, 'GPIO not supported, ' + rand_phrase()+'.')
            return
        if(not (is_admin(message.author))):
            await client.send_message(message.author, 'You are not an admin, ' + rand_phrase()+'.')
            return
        msg = message.content.split(' ')
        pin = msg[1]
        cmd = msg[2]
        if (len(msg) < 2):
            await client.send_message(message.channel, 'Missing parameters')
            return
        if(pin[0] != 'p'):
            pin = PIN[pin]
        GPIO.setup(pin, GPIO.OUT)
        global maxblink
        if(cmd == 'blink'):
           maxblink = int(msg[3])
           sleep = float(msg[4])
           await client.send_message(message.channel, 'Blinking pin '+str(maxblink)+' Blinks @ '+str(sleep)+'sec sleep')
           blink=0
           while (blink < maxblink):
              GPIO.output(pin, GPIO.HIGH)
              await asyncio.sleep(sleep)
              GPIO.output(pin, GPIO.LOW)
              await asyncio.sleep(sleep)
              blink = blink+1
        elif(cmd == 'low'):
           maxblink = 0
           await client.send_message(message.channel, 'Setting pin '+str(pin)+' to low...')
           GPIO.output(pin, GPIO.LOW)
        elif(cmd == 'high'):
           maxblink = 0
           await client.send_message(message.channel, 'Setting pin '+str(pin)+' to high...')
           GPIO.output(pin, GPIO.HIGH)
    elif message.content.startswith(ctrl+'restart'):
        await client.send_message(message.channel, 'Restarting, ' + rand_phrase()+'.')
        if(not (is_admin(message.author))):
            await client.send_message(message.channel, 'You are not an admin, ' + rand_phrase()+'.')
            return
        os.system( "/home/debian/start-bot.sh & disown" );
        sys.exit()
    elif message.content.startswith(ctrl+'image'):
        os.system( "feh -F /home/debian/test/snap.jpg" );
    elif message.content.startswith(ctrl+'quit'):
        if(not (is_admin(message.author))):
            await client.send_message(message.channel, 'You are not an admin, ' + rand_phrase()+'.')
            return
        await client.send_message(message.channel, rand_phrase())
        await sys.exit()

client.run('NDEyNDQ2ODU0Mzk2MjQ4MDY0.DWf6cQ.DlKtAe_70eGv5gFyIYaMzVgMX0s')

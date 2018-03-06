import sys, os, time, random
import discord, urllib, json, asyncio, shlex, subprocess
#from PIL import Image
from bs4 import BeautifulSoup
from steam import SteamGameGrabber
from pinout import PIN

if sys.platform == "linux" or sys.platform == "linux2":
    import Adafruit_BBIO.GPIO as GPIO
    OS = "linux"
elif sys.platform == "win32":
    GPIO = False
    OS = "windows"

client = discord.Client()
displayer = None
phrases = {}
admins = {}
config = []
ctrl = '!'
commands = {'free': 'Posts list of free game keys to channel', 'meme': 'Posts random meme to channel', 'fortune':'Read off random fortune cookie', 'steam [acc1] [acc2]': 'Posts random multiplayer game from both steam libraries', 'purge':'Remove all posts from channel', 'spew':'Spew random phrase', 'quit': 'Kills the bot', 'pin [pin name] [high/low/blink ([# blinks] [delay in secs])] ': 'tests a pin on the BBB', 'restart':'Updates and restarts the bot', 'display [url]':'Displays an image on the LCD', 'g2a': 'Look up game price on G2A marketplace'}
    
def is_me(m):
    return m.author == client.user
    
def is_admin(user):
    global admins
    return (str(user) in admins)

def load_admins():
    global admins
    admins_file = open("admins.txt", "r")
    admins = admins_file.read().splitlines()
    admins_file.close()

def load_config():
    global config, ctrl
    with open("config.txt", "r") as config_file:
        for line in config_file:
            if(line[0] == '#'):
                continue
            name, var = line.partition('=')[::2]
            config[name.strip()] = str(var)
    config_file.close()
    ctrl = config['ctrl']
    
def load_phrases():
    global phrases
    phrases_file = open("phrases.txt", "r")
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
        return False
    GPIO.setup(PIN['BUZZER'], GPIO.OUT)
    GPIO.output(PIN['BUZZER'], GPIO.HIGH)
    return True

def fetch_html(url):
    headers = {}
    headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0'
    req = urllib.request.Request(url, headers = headers)
    try:
        html = urllib.request.urlopen(req).read()
    except:
        return None
    return html
    
@client.event
async def on_ready():
    gpio_init()
    load_phrases()
    print('Admins file loaded: ' + str(admins))
    load_admins()
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
            
    elif message.content.startswith(ctrl+'g2a'):
        msg = message.content
        if (len(msg) < 2) :
            await client.send_message(message.channel, 'Not enough arguments.')
            return
        index = msg.find(' ')
        game = msg[index+1:]
        search_url = 'https://www.g2a.com/en-us/search?query={}'.format(game).replace(" ", "%20")
        search = fetch_html(search_url)
        if (not(search)):
            await client.send_message(message.channel, "No results for {0}".format(game))
            return
        soup = BeautifulSoup(search, 'html.parser')
        link = soup.find('h3', attrs={'class': 'Card__title'})
        game_url = 'https://www.g2a.com{}'.format(link.a["href"])
        game = fetch_html(game_url)
        soup = BeautifulSoup(game, 'html.parser')
        title = soup.find('h1', attrs={'class': 'product__title'}).text
        price = soup.find('span', attrs={'class': 'price'}).text
        await client.send_message(message.channel, "Title: {0}\nPrice: {1}\nURL: {2}".format(title, price, game_url))

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
        fortune = soup.find('div', attrs={'class': 'fortune'}).text
        await client.send_message(message.channel, fortune)
        
    elif message.content.startswith(ctrl+'steam'):
        msg = message.content.split(' ')
        if (len(msg) < 3) :
            await client.send_message(message.channel, 'Not enough arguments.')
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
        maxblink = 100
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
            await client.send_message(message.channel, 'Missing arguments.')
            return
        if(pin[0] != 'p'):
            pin = PIN[pin]
        GPIO.setup(pin, GPIO.OUT)
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
        if(not (is_admin(message.author))):
            await client.send_message(message.channel, 'You are not an admin, ' + rand_phrase()+'.')
            return
        await client.send_message(message.channel, 'Restarting, ' + rand_phrase()+'.')
        if (OS == "linux"):
            os.system("/home/debian/start-bot.sh & disown")
            sys.exit(0)
        elif (OS == "windows"):
            os.system("call %cd%\start-bot.bat")
            sys.exit(0)
        
    elif message.content.startswith(ctrl+'display'):
        global displayer
        if(not (is_admin(message.author))):
            await client.send_message(message.channel, 'You are not an admin, ' + rand_phrase()+'.')
            return
        msg = message.content.split(' ')
        if (len(msg) < 2):
            await client.send_message(message.channel, 'Missing arguments.')
            return
        if(displayer or msg[1] == 'clear'):
            displayer.kill()
            displayer = None
        link = msg[1]
        fname=link.split('/')[-1]
        fext=fname.split('.')[-1]
        if (fext == 'gif'):
            viewer="gifview -a -g 800x480 ~/discord-bot/Moonkeith/images/{}".format(fname)
        else:
            viewer="feh -FZ ~/discord-bot/Moonkeith/images/{}".format(fname)
        wget='wget -P ~/discord-bot/Moonkeith/images/ {}'.format(link)
        downloader=subprocess.Popen(shlex.split(wget))
        downloader.wait()
        downloader.kill()
        displayer=subprocess.Popen(viewer.split(' '))
        
    elif message.content.startswith(ctrl+'quit'):
        if(not (is_admin(message.author))):
            await client.send_message(message.channel, 'You are not an admin, ' + rand_phrase()+'.')
            return
        await client.send_message(message.channel, rand_phrase())
        await sys.exit()

load_config()
print("Configuration loaded.")
client.run(config["token"])

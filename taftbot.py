
import os
import discord
import requests
import aiohttp
import io
from PIL import Image
from discord import app_commands
from discord.ext import commands, tasks
import random
from datetime import datetime
import feedparser
from bs4 import BeautifulSoup
import smtplib
import sys
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
#GUILD = os.getenv('DISCORD_GUILD')
EMAIL = os.getenv('TEXT_EMAIL')
PASSWORD = os.getenv('TEXT_PASSWORD')
PHONENUM = os.getenv('SEND_PHONE')
PHONECARRIER = os.getenv('SEND_CARRIER')

CARRIER_MAP = {
    "verizon": "@vtext.com",
    "tmobile": "@tmomail.net",
    "sprint": "@messaging.sprintpcs.com",
    "at&t": "@txt.att.net",
    "boost": "@smsmyboostmobile.com",
    "cricket": "@sms.cricketwireless.net",
    "uscellular": "@email.uscc.net",
}

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
image_folder = "taftimages"

letterbox_channels = []
image_files = os.listdir(image_folder)
print(image_files)
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
letterboxd_accounts = ["plexagon", "oneduckaday", "the_better_evan", "genet17", "G1bblets"]
feed = feedparser.parse("https://letterboxd.com/plexagon/rss/")
seen_entries = []


@client.event
async def on_ready():
    await tree.sync()
    await setupSeenEntries()
    checkLetterboxd.start()  # Add this line
    print(f'We have logged in as {client.user}')

async def setupSeenEntries():
    for account in letterboxd_accounts:
        feed = feedparser.parse("https://letterboxd.com/" + account + "/rss/")
        for x in feed.entries:
            #Filter out lists eww cringe
            #print(x.keys())
            if x.has_key("letterboxd_watcheddate"):
                seen_entries.append(x)

async def sendText(phone_number, carrier, message):
    recipient = str(phone_number) + CARRIER_MAP[carrier]
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    senderName = message.author.display_name
    channel = message.channel.name
    textMessage = "from " + senderName + " in " + channel + " " + message.content
    textMessage = textMessage.encode("ascii", 'ignore').decode('ascii')
    print(textMessage)
    server.sendmail(EMAIL, recipient, str(textMessage))


@client.event
async def on_message(message):
   # await sendText(PHONENUM,PHONECARRIER, message)
    if message.author == client.user:
        return
    #if message.mentions[0] == client.user:
    if len(message.mentions) == 0:
        return
    if message.mentions[0].id == client.user.id:
        print(message.content)
        if "How are you feeling" in message.content:
            senderName = message.author.display_name
            await message.channel.send(senderName + ", today I am feeling William Howard Taft!", file=discord.File("taftimages/" + random.choice(image_files)))
    

@tree.command(
    name="today_im_feeling",
    description="How is Taft Bot feeling today?"
)
async def todayImFeeling(interaction):
    senderName = interaction.user.display_name
    await interaction.response.send_message(senderName + ", today I am feeling William Howard Taft!", file=discord.File("taftimages/" + random.choice(image_files)))


@tree.command(
    name="setup_letterboxd_channel",
    description="Set up a channel for Letterboxd reviews"
)
async def setupLetterboxdChannel(interaction):
    letterbox_channels.append(interaction.channel_id)
    await interaction.user.send(interaction.channel.name + " has been set up for letterboxd reviews.")


@tree.command(
    name="recent_letterbox_review",
    description="Get a recent (within a week) letterbox review"
)
@app_commands.describe(user="plexagon, oneduckaday, the_better_evan, genet17, G1bblets")
async def recentLetterboxdReview(interaction, user:str):
    time = datetime.now().timetuple()
    entrylist = []
    applicable_seen_entries = []
    if user in letterboxd_accounts:
        applicable_seen_entries = [x for x in seen_entries if x.author == user]
    else:
        applicable_seen_entries = seen_entries
    for x in applicable_seen_entries:
        if (datetime(*time[0:6]) - datetime(*x.published_parsed[0:6])).total_seconds() < 604800:
            entrylist.append(x)
    if not entrylist:
        entrylist.append(applicable_seen_entries[len(applicable_seen_entries)-1]) #This would be the most recent review
    print(entrylist)
    print(seen_entries)
    await sendReviewMessage(random.choice(entrylist), interaction)


@tasks.loop(hours=12)
async def checkLetterboxd():
    for account in letterboxd_accounts:
        feed = feedparser.parse("https://letterboxd.com/" + account + "/rss/")
        print("Hello :)")
        print(len(feed.entries))
        print(len(seen_entries))
        time = datetime.now().timetuple()
        entrylist = []
        for x in feed.entries:
            if (datetime(*time[0:6]) - datetime(*x.published_parsed[0:6])).total_seconds() < 604800:
                if x.has_key("letterboxd_watcheddate"):
                    entrylist.append(x)
        if not entrylist:
            count = 0
            while feed.entries[count].has_key("letterboxd_watcheddate") == False:
                count += 1
            entrylist.append(feed.entries[count]) #This would be the most recent review
        entrylist = [x for x in entrylist if x not in seen_entries]
        print(entrylist)
        for x in entrylist:
            seen_entries.append(x)
            for y in letterbox_channels:
                await sendReviewMessageNew(x, y)

async def sendReviewMessageNew(entry, channel):
    title = entry.title
    spoilers = False
    if entry.title.find("(contains spoilers)") != -1:
        title = entry.title.split("(contains spoilers)")[0]
        spoilers = True
    if entry.letterboxd_memberlike == "Yes":
        title = title + " ❤"
    htmlParse = BeautifulSoup(entry.summary, 'html.parser')
    channel = client.get_channel(channel)
    await channel.send("Reviewed by: " + str(entry.author))
    await channel.send("Reviewed on " + str(entry.letterboxd_watcheddate))
    print(entry.letterboxd_watcheddate)
    await channel.send(title)
    await channel.send("Rewatched?: " + str(entry.letterboxd_rewatch))
    
    for para_index in range(len(htmlParse.find_all('p'))):
        para = htmlParse.find_all('p')[para_index]
        if para_index == 0:
            continue
        if spoilers:
            await channel.send("|| " + para.get_text() + " ||")
        else:
            await channel.send(para.get_text())
    img_link = htmlParse.find_all('img')[0]['src']
    async with aiohttp.ClientSession() as session:
        async with session.get(img_link) as resp:
            if resp.status != 200:
                return await channel.send('Could not download file...')
            img_bytes = await resp.read()
            with Image.open(io.BytesIO(img_bytes)) as img:
                img.thumbnail((200, 200))
                data = io.BytesIO()
                img.save(data, format='PNG')
                data.seek(0)
                await channel.send(file=discord.File(data, 'movie_thumb.png'))

async def sendReviewMessage(entry, interaction):
    title = entry.title
    spoilers = False
    if entry.title.find("(contains spoilers)") != -1:
        title = entry.title.split("(contains spoilers)")[0]
        spoilers = True
    if entry.letterboxd_memberlike == "Yes":
        title = title + " ❤"
    htmlParse = BeautifulSoup(entry.summary, 'html.parser')
    await interaction.response.send_message("Reviewed on " + str(entry.letterboxd_watcheddate))
    print(entry)
    channel = interaction.channel
    await channel.send("Reviewed by: " + str(entry.author))
    await channel.send(title)
    await channel.send("Rewatched?: " + str(entry.letterboxd_rewatch))
    
    for para_index in range(len(htmlParse.find_all('p'))):
        para = htmlParse.find_all('p')[para_index]
        if para_index == 0:
            continue
        if spoilers:
            await channel.send("|| " + para.get_text() + " ||")
        else:
            await channel.send(para.get_text())
    img_link = htmlParse.find_all('img')[0]['src']
    async with aiohttp.ClientSession() as session:
        async with session.get(img_link) as resp:
            if resp.status != 200:
                return await channel.send('Could not download file...')
            img_bytes = await resp.read()
            with Image.open(io.BytesIO(img_bytes)) as img:
                img.thumbnail((200, 200))
                data = io.BytesIO()
                img.save(data, format='PNG')
                data.seek(0)
                await channel.send(file=discord.File(data, 'movie_thumb.png'))


print(TOKEN)
print(datetime.now().timetuple())
client.run(TOKEN)


import os
import discord
from discord import app_commands
import random
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
image_folder = "taftimages"

image_files = os.listdir(image_folder)
print(image_files)
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')

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

print(TOKEN)

client.run(TOKEN)

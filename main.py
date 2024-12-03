import sys
# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values
# loading variables from .env file
load_dotenv()
import http.client
import json
import random
import discord
import logging
from datetime import date
from discord import app_commands

async def get_definition(word_to_define):
    conn = http.client.HTTPSConnection("api.urbandictionary.com")
    definition = None
    max_random_size = 5
    random_index = 0
    max_retry = 5
    retry = 1
    url_string = "/v0/define?term=\'" + word_to_define + "\'"
    url = url_string.replace(" ", "%20")
    continue_sending = True

    try:
        while continue_sending and retry <= max_retry:
            try:
                conn.request("GET", url)
                res = conn.getresponse()
                data = res.read()
                definition_list = json.loads(data.decode("utf-8"))['list']

                if len(definition_list) == 0:
                    definition = None
                    continue_sending = False

                elif len(definition_list) < max_random_size :
                    max_random_size = len(definition_list)
                    print(max_random_size)

                if max_random_size > 1 :
                    random_index = random.randint(0, max_random_size - 1)
                definition = definition_list[random_index]
                continue_sending = False

            except Exception as e:
                logging.error('[Retry: ' + retry + '] Error: ' + str(e))
                retry += 1

    except Exception as e:
        logging.error("Error getting definition: " + str(e))

    return definition


async def get_random_definition():
    conn = http.client.HTTPSConnection("api.urbandictionary.com")
    definition = None
    max_retry = 5
    retry = 1
    conn.request("GET", "/v0/random")

    try:
        while retry <= max_retry:
            try:
                res = conn.getresponse()
                data = res.read()
                definition_list = json.loads(data.decode("utf-8"))
                return definition_list['list'][0]

            except Exception as e:
                logging.error('[Retry: ' + retry + '] Error: ' + str(e))
                retry += 1

    except Exception as e:
        logging.error("There was an error getting the random definition: " + str(e))

    return definition

async def remove_braces(remove_string):
    chars_to_remove = ['[', ']']
    for c in chars_to_remove:
        remove_string = remove_string.replace(c, '')

    return remove_string

async def create_message(response_from_urban_dictionary, word_to_define = ''):
    if len(word_to_define) == 0:
        word = await remove_braces(response_from_urban_dictionary['word'])
    word = word_to_define
    definition = await remove_braces(response_from_urban_dictionary['definition'])
    example = await remove_braces(response_from_urban_dictionary['example'])

    return '**Word:** ' + word + '\n\n**Definition:** ' + definition + '\n\n**Example:** ' + example

async def send_message_to_channel(message_from_server, message):
    await message_from_server.channel.send(message)

async def send_interaction_to_channel(message_from_server, interaction):
    await message_from_server.channel.send(interaction)

if len(sys.argv) > 1 and str(sys.argv[1]):
    nameOfFile = '../discord-urban-dictionary-bot-logs/' + str(date.today()) + '.log'
else:
    nameOfFile = '/bin/discord-urban-dictionary-bot-logs/' + str(date.today()) + '.log'

#logging file
logging.basicConfig(filename=nameOfFile, level=logging.ERROR, encoding='utf-8', format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

DISCORD_API_KEY = os.getenv("DISCORD_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(discord_client)

@tree.command(
    name="random",
    description="Get a random word from urban dictionary",
)
async def send_random_definition(interaction: discord.Interaction):
    definition = await get_random_definition()
    message_to_send = await create_message(definition)
    await interaction.response.send_message(message_to_send)

@tree.command(
    name="help",
    description="List of commands available",
)
async def send_list_of_commands(interaction: discord.Interaction):
    commands = "**!d** [word you would like urband dictionary to define]"
    await interaction.response.send_message(commands)


@discord_client.event
async def on_ready():
    await tree.sync()

@discord_client.event
async def on_message(message_from_server):
    if message_from_server.author == discord_client.user:
        return

    message_content = str(message_from_server.content).lower()

    if message_content.startswith("!d "):
        word_to_define = message_content[3:]
        if word_to_define is None:
            await send_message_to_channel(message_from_server, 'Sorry, I could not read the word you wuld like defined.')
        definition = await get_definition(word_to_define)
        if definition is None:
            await send_message_to_channel(message_from_server, 'Sorry, I could not find the word you need me to define.')
        else:
            message_to_send = await create_message(definition, word_to_define)
            await send_message_to_channel(message_from_server, message_to_send)

discord_client.run(DISCORD_API_KEY)
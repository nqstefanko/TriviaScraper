import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from os.path import join, dirname

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default() #Need to establish intents to see members inside channels!
intents.members = True

bot = commands.Bot(intents=intents, command_prefix='??')

bot.remove_command('help')

bot.load_extension('cogs.help')
bot.load_extension('cogs.scraping')
bot.load_extension('cogs.utils')

bot.run(TOKEN)


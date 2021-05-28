import datetime as dt
from discord.ext import commands
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
from lxml.html import fromstring
import os
from os.path import join, dirname
from pymongo import MongoClient
import re
import requests

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'keys.json'

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

load_dotenv()

MONGO_URL = os.getenv('MONGO_URL')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

DEBUG = False

cluster = MongoClient(MONGO_URL)
db = cluster['triviaScraper']
collection = db['rounds']

google_form_pattern = "https:\/\/docs\.google\.com\/forms\/.*|https:\/\/forms\.gle\/.*"
google_folder_pattern = "https:\/\/drive\.google\.com\/drive\/folders\/.*\?usp=sharing"


def check_form(msg):
    return re.search(google_form_pattern, msg)


def check_folder(msg):
    return re.search(google_folder_pattern, msg)


def check_match(msg):
    form_match = check_form(msg)
    folder_match = check_folder(msg)
    if form_match:
        if DEBUG: print("We have a form")
        return form_match.group(0)
    elif folder_match:
        if DEBUG: print("we have a folder")
        return folder_match.group(0)
    return False


def is_command(msg):  # Checking if the message is a command call
    if len(msg.content) == 0:
        return False
    elif msg.content.split()[0][0:2] == "??":
        return True
    else:
        return False


def get_title(msg_content):
    return fromstring(requests.get(msg_content).content).findtext('.//title')


async def single_log_to_db(msg):
    """
         Take the matched message, get the proper data, add to the DB, and send back formatted for  Sheets API
     """
    link_type = "form"
    if check_folder(msg.content):
        link_type = "folder"

    title = get_title(msg.content)
    d = {'time': str(msg.created_at), 'author': msg.author.name,
         'title': title, "type": link_type, '_id': msg.content}

    if not collection.count_documents({'_id': msg.content}):
        if DEBUG: print(f"Inserted {title}")
        collection.insert_one(d)
        await msg.channel.send(f"Howdy, {title} was just scraped and added to the DB!")
        warped_data = [[str(d['time']), d['title'], d['author'], d['type'], d['_id']]]
        add_to_sheets(warped_data)

    else:
        await msg.channel.send(f"Howdy, looks like this round is already in the DB!")


def log_link_to_db(msg, counter_dict):
    """
        Take the matched message, get the proper data, add to the DB, update counters and send back formatted for Sheets API
    """
    link_type = "form"
    if check_form(msg.content):
        counter_dict['form_counter'] += 1
    else:
        link_type = "folder"
        counter_dict['folder_counter'] += 1

    title = get_title(msg.content)
    d = {'time': str(msg.created_at), 'author': msg.author.name,
         'title': title, "type": link_type, '_id': msg.content}

    if not collection.count_documents({'_id': msg.content}):
        if DEBUG: print(f"Inserted {title}")
        collection.insert_one(d)
        counter_dict['total_counter'] += 1
        return d

    return None

def add_to_sheets(final_data):
    """
    Add the scraped data to the final google sheets for everyone to see!
    """
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    request = service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID,
                                                     range="A:E", valueInputOption="USER_ENTERED",
                                                     insertDataOption="INSERT_ROWS", body={"values": final_data})
    response = request.execute()
    if DEBUG: print(response)
    print(response)


class Scraper(commands.Cog):
    """
    Scrapes for trivia form links!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def scrape(self, ctx, full=None):
        """
        Scrapes current channel for links. The default only scrapes for last 24 hours.
        Do ??scrape True to scrape the entire channel
        """
        await ctx.channel.send("Please Wait. Scraping... ")

        counter_dict = {"folder_counter": 0, 'form_counter': 0, 'total_counter': 0}
        current_data = []
        async for msg in ctx.channel.history(limit=10000):
            if msg.author != self.bot.user:
                date_diff = dt.datetime.utcnow() - msg.created_at
                if date_diff.days == 0 or full:  # If less than 24 hours or entire channel
                    matched_content = check_match(msg.content)
                    if not is_command(msg) and matched_content:  # if it is not a command and it matched
                        msg.content = matched_content
                        added = log_link_to_db(msg, counter_dict)
                        if added:
                            current_data.append(added)

        await ctx.channel.send(
            f"Howdy! I scraped a total of {counter_dict['form_counter'] + counter_dict['folder_counter']} links. I found {counter_dict['form_counter']} forms and {counter_dict['folder_counter']} folders! {counter_dict['total_counter']} were added to DB and {counter_dict['form_counter'] + counter_dict['folder_counter'] - counter_dict['total_counter']} were repeat links")

        if (len(current_data) != 0):
            add_to_sheets([[str(d['time']), d['title'], d['author'], d['type'], d['_id']] for d in current_data])

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in {self.bot.user}")


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:  # Dont do anything if the bot is talking
            return

        if message.content.startswith("testTEST1234"):
            await message.channel.send("Tits")

        matched_content = check_match(message.content)
        if not is_command(message) and matched_content:
            message.content = matched_content
            await single_log_to_db(matched_content)


def setup(bot):
    bot.add_cog(Scraper(bot))

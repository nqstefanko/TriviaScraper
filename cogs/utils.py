from cogs.help import send_embed
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from os.path import join, dirname
import random

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

load_dotenv()

GEN_VOICE_CHAN_ID = os.getenv('GENERAL_VOICE_CHANNEL_ID')


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def organize_teams(num, names):
    """Randomly organizes the teams"""
    names_list = list(names)
    random.shuffle(names_list)
    final_teams = list(chunks(names_list, int(len(names_list) / int(num))))
    if int(num) != len(final_teams):
        final_teams[-2] = final_teams[-2] + final_teams[-1]
        del final_teams[-1]
    return final_teams


class Utils(commands.Cog):
    """
    Miscellaneous utilities for trivia night!
    """

    def __init__(self, bot):
        self.bot = bot
        self.scores = [0, 0]
        self.teams = []

    @commands.command(aliases=['mta'])
    async def make_teams_auto(self, ctx, num=2):
        """
        Used to make the teams from members in general voice channel!
        Invoked: ??mta NUM_OF_TEAMS (Optional: default is 2)
        """
        general_voice = self.bot.get_channel(int(GEN_VOICE_CHAN_ID))

        if general_voice is None:
            raise commands.CommandError("MTA_ERROR1: Not enough people to make teams!")

        voice_members = []
        for member in general_voice.members:
            voice_members.append(member.name)

        if len(voice_members) <= 1:
            raise commands.CommandError("MTA_ERROR2: Not enough people to make teams!")

        self.teams = organize_teams(num, voice_members)
        self.scores = []
        await self.show_teams(ctx)

    @make_teams_auto.error
    async def make_teams_auto_error(self, ctx, error):
        emb = None
        if isinstance(error, commands.CommandError):
            emb = discord.Embed(title='There does not seem to be enough people for at least 2 teams!',
                                color=discord.Color.red(),
                                description=f'Make sure there are at least 2 people in general! :smiley:\n')
        else:
            emb = discord.Embed(title='That does not seem to be a command', color=discord.Color.red(),
                                description=f'Try ??help for list of commands :smiley:\n')
        print(error)
        await send_embed(ctx, emb)

    @commands.command(aliases=['mt'])
    async def make_teams(self, ctx, num, *names):
        """
        Used to make the teams!
        Invoked: ??mt NUM_OF_TEAMS t1 t2 t3 etc...
        """
        if len(names) <= 1 or int(num) > len(names):
            raise commands.CommandError("MT_ERROR: Not enough people to make teams!")

        self.teams = organize_teams(num, names)
        self.scores = []
        await self.show_teams(ctx)

    @make_teams.error
    async def make_teams_error(self, ctx, error):
        emb = None
        if isinstance(error, commands.CommandError):
            emb = discord.Embed(title='There does not seem to be enough people to make teams',
                                color=discord.Color.red(),
                                description=f'Make sure the # of teams is less than the number of people! :smiley:\n')
        else:
            emb = discord.Embed(title='Improper invocation of make_teams command', color=discord.Color.red(),
                                description=f'Make teams is invoked with ??mt NUM_OF_TEAMS Name1, Name2, Name3 etc')
        print(error)
        await send_embed(ctx, emb)

    @commands.command(aliases=['as'])
    async def add_scores(self, ctx, *round_scores):
        """
        Used to add to current scores
        Invoked: ??as score1 score2  etc...
        """
        if len(round_scores) != len(self.scores):
            await ctx.channel.send(len(self.scores), len(round_scores))
            raise ValueError("That was not the proper amount of scores!")
        else:
            for i in range(len(round_scores)):
                self.scores[i] += float((round_scores[i]))
            await self.show_scores(ctx)

    @add_scores.error
    async def add_scores_error(self, ctx, error):
        emb = discord.Embed(title='Improper invocation of add_scores command', color=discord.Color.red(),
                            description=f'Invoked with ??us score1, score2. Must be in order and have proper # of scores! ')
        print(error)
        await send_embed(ctx, emb)

    @commands.command(aliases=['us'])
    async def update_scores(self, ctx, *round_scores):
        """
        Used to set current scores
        Invoked: ??us score1 score2  etc...
        """
        if (len(round_scores) != len(self.scores)):
            await ctx.channel.send(len(self.scores), len(round_scores))
            raise ValueError("That was not the proper amount of scores!")
        else:
            for i in range(len(round_scores)):
                self.scores[i] = float((round_scores[i]))
                await ctx.channel.send(f'Team {i + 1}: {self.scores[i]}')

    @update_scores.error
    async def update_scores_error(self, ctx, error):
        emb = discord.Embed(title='Improper invocation of update_scores command', color=discord.Color.red(),
                            description=f'Invoked with ??us score1, score2. Must be in order and have proper # of scores! ')
        print(error)
        await send_embed(ctx, emb)

    @commands.command(aliases=['ss'])
    async def show_scores(self, ctx):
        """
        Used to set current scores
        Invoked: ??ss
        """
        for i in range(len(self.scores)):
            await ctx.channel.send(f'Team {i + 1}: {self.scores[i]}')

    @commands.command(aliases=['st'])
    async def show_teams(self, ctx):
        """
        Shows the current Teams
        Invoked: ??st
        """
        for i in range(len(self.teams)):
            team = ', '.join(self.teams[i])
            await ctx.channel.send(f'Team {i + 1}: {team}')
            self.scores.append(0)

    @commands.command(hidden=True, aliases=['dp'])
    async def del_prev(self, ctx, arg=1):
        """
        Deletes previous messages
        """
        await ctx.channel.purge(limit=arg)

    @commands.command(hidden=True)
    async def careful_spongebob(self, ctx):
        await ctx.channel.send("Careful Spongebob: https://www.youtube.com/watch?v=vFEe_jjYGYc")


def setup(bot):
    bot.add_cog(Utils(bot))

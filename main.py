from discord.ext import commands
from discord.ext.commands.context import Context

from discord import Embed, Color

from os import getenv
from discord.message import Message
from dotenv import load_dotenv
import requests

import random

load_dotenv()

DISCORD_TOKEN = getenv("DISCORD_TOKEN")

PREFIX = "$"

bot = commands.Bot(command_prefix=PREFIX)

# catalogue = requests.get("http://93.6.41.243:8271/items").json()
catalogue = requests.get("http://localhost:6969/items").json()

categories = requests.get("http://localhost:6969/categories").json()


active_games = {}


@bot.event
async def on_ready():
    print("HELLO WORLDU")


async def nextRound(ctx):
    id = ctx.guild.id

    if active_games[id]["curr_round"] == active_games[id]["rounds"]:
        return await stopGame(ctx, id)

    active_games[id]["curr_round"] += 1
    active_games[id]["curr_item"] = random.choice(active_games[id]["curr_catalogue"])
    active_games[id]["latest"] = 0

    message = await ctx.send(embed=generateEmbed(id))
    active_games[id]["message"] = message


async def stopGame(ctx, id):
    await ctx.send(embed=generateFinishEmbed(id))
    del active_games[id]


def generateEmbed(id):
    current_item = active_games[id]["curr_item"]

    embed = Embed(
        title=current_item["nom"],
        description=f"Devinez le prix de ce magnifique truc !",
        color=Color.red(),
    )

    embed.set_image(url=current_item["image"])

    latest = active_games[id]["latest"]
    price = active_games[id]["curr_item"]["prix"]

    more = "C'est plus"
    less = "C'est moins"

    if latest > 0:
        embed.add_field(
            name=f"Prix donné : {latest}€", value=f"{more if latest < price else less}"
        )

    return embed


def generateFinishEmbed(id):
    sorted_players = sorted(
        active_games[id]["players"], key=lambda x: x["score"], reverse=True
    )

    joueurs = [
        f"{i+1}. {player['name']} ({player['score']} point{'s' if player['score'] > 1 else ''})"
        for i, player in enumerate(sorted_players)
    ]

    classementString = "\n".join(joueurs)

    return Embed(
        title="Classement",
        description=classementString,
        color=Color.orange(),
    )


@bot.command()
async def start(ctx: Context, *args):
    rounds = 5
    category = None

    for arg in args:
        if arg.isnumeric() and int(arg) <= 30:
            rounds = int(arg)
        elif arg.lower() in categories:
            category = arg.lower()

    active_games[ctx.guild.id] = {
        "game_mode": "Amazon",
        "curr_round": 0,
        "rounds": rounds,
        "category": category,
        "players": [],
        "curr_item": {},
        "latest": 0,
        "message": None,
        "curr_catalogue": list(
            filter(lambda item: item["category"] == category, catalogue)
        )
        if category is not None
        else catalogue,
    }

    await ctx.send("La partie commence !")

    await nextRound(ctx)


def isFloat(string):
    try:
        float(string)
        return True
    except:
        return False


@bot.event
async def on_message(message: Message):
    if message.author == bot.user:
        return

    if message.content.startswith(PREFIX):
        return await bot.process_commands(message)

    if message.guild.id in list(active_games.keys()):
        message.content = message.content.replace(",", ".")
        if not isFloat(message.content):
            return

        if not any(
            player
            for player in active_games[message.guild.id]["players"]
            if player["id"] == message.author.id
        ):
            active_games[message.guild.id]["players"].append(
                {"id": message.author.id, "name": message.author.name, "score": 0}
            )

        price = float(message.content)

        item_price = active_games[message.guild.id]["curr_item"]["prix"]

        latest = active_games[message.guild.id]["latest"]

        if item_price > latest and price <= latest:
            await message.delete()
            return

        if item_price < latest and price >= latest:
            await message.delete()
            return

        if price == item_price:
            await message.channel.send(
                f"POPOPOPOPO C'EST LE BON PRIX, INCROYABLE T'ES TROP FORT {message.author.name.upper()}!!!"
            )

            player_dict = list(
                filter(
                    lambda x: x["id"] == message.author.id,
                    active_games[message.guild.id]["players"],
                )
            )
            player_dict[0]["score"] += 1

            return await nextRound(message.channel)

        active_games[message.guild.id]["latest"] = price

        await active_games[message.guild.id]["message"].edit(
            embed=generateEmbed(message.guild.id)
        )
        await message.delete()
bot.remove_command('help')
@bot.command()
async def help(ctx:Context):
    embed = Embed(
        title="Commandes de Vincent Lagaf",
        description="$start [rounds] [category] : Démarre une partie de juste prix.",
        color=Color.blurple()
    )
    await ctx.send(embed=embed)
    

bot.run(DISCORD_TOKEN)

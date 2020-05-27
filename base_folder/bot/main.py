import time
import discord
from discord.ext import commands
from config.config import token, logging


client = commands.Bot(command_prefix='.')
extensions = ["modules.test.test",
              "modules.listener.listener",
              "modules.listener.levelsystem",
              "modules.commands.moderation.moderation_mods",
              "modules.commands.moderation.moderation_admin",
              "modules.commands.fun.fun",
              "modules.commands.dev",
              "modules.imgwelcome.imgwelcome"
              ]


if __name__ == "__main__":
    for extension in extensions:
        try:
            client.load_extension(extension)
            print('Loaded extension {}'.format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))
    client.run(token())


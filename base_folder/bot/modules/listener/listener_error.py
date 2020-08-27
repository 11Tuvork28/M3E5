import discord
from discord.ext import commands
from base_folder.bot.config.config import error_embed
from base_folder.queuing.db import on_error
from base_folder.bot.utils.exceptions import Youtubedl


class ErrorHandler(commands.Cog, Youtubedl):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, ex):
        await ctx.channel.purge(limit=1)
        if hasattr(ctx.command, 'on_error'):
            return

        error = getattr(ex, 'original', ex)
        embed = error_embed(self.client)
        channel = self.client.get_channel(await self.client.sql.get_cmd_channel(ctx.guild.id))
        if channel is None:
            channel = ctx
        if isinstance(error, commands.CommandNotFound):
            embed.description = "I have never seen this command in my entire life"
            await channel.send(embed=embed)
            return

        if isinstance(error, commands.errors.CheckFailure):
            embed.description = "You do not have permission to use this command." \
                          "If you think this is an error, talk to your admin"
            await channel.send(embed=embed)
            return

        if isinstance(error, commands.BadArgument):
            embed.description = "You gave me an wrong input check the command usage"
            await channel.send(embed=embed)
            return

        if isinstance(error, commands.NoPrivateMessage):
            try:
                embed.description = "This command is for guilds/servers only"
                await channel.author.send(embed=embed)
            except discord.Forbidden:
                pass
            return

        embed.description = "Something is totally wrong here in the M3E5 land I will open issue at my creator's bridge"
        await channel.send(ex, embed=embed)
        on_error.delay(ctx.guild.id, str(ex))


def setup(client):
    client.add_cog(ErrorHandler(client))

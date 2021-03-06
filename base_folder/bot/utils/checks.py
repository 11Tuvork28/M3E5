import functools
from inspect import signature

import discord
from discord.ext.commands import BadArgument, MissingRequiredArgument, MissingRole


def check_args_datatyp(func):
    """
    This decorator checks if the args are in the right datatype that the command needs
    e.g. if you want to change the welcome channel and you a str instead of an id(int) then this will complain.
    And throw discord.ext.commands.BadArgument
    :param func: the called function, its always a coroutine
    :return: the original function
    """
    @functools.wraps(func)
    async def predicate(self, ctx, *args, **kwargs):
        """
        :param self: the cog the command is in e.g Music or Custom
        :param ctx: the context object of the current invoked command
        :param args: the arguments a command can take e.g channel_id
        :param kwargs: in case a commands gets kwargs but idk a case where this could happen
        :return: returns the awaited command
        """
        sig = signature(func)
        parametertypes = []
        parameternames = []
        for index, param in enumerate(sig.parameters):
            if index >= 2:
                parametertypes.append(sig.parameters[param].annotation)
                parameternames.append(sig.parameters[param].name)
        for index, arg in enumerate(args):
            if type(arg) != parametertypes[index]:
                if type(arg) is None:
                    """ 
                    This can't be triggered because discord.py checks for MissingRequiredArgument
                    but just in case discord.py didn't caught it
                     """
                    raise MissingRequiredArgument
                raise BadArgument
        await func(self, ctx, *args, **kwargs)
    return predicate


def logging_to_channel_cmd(func):
    """
    This decorator will log to the command channel that a commands was issued.
    This is useful if you're watching specific commands.
    THIS ONLY WORKS IF the coroutine returns the embed to send
    If the cmd isn't set it will fallback to the stdout channel and skip logging in this decorator, this requires
    the logging_to_channel_stdout decorator.
    :param func: the called function, its always a coroutine
    :return: the original function
    """
    @functools.wraps(func)
    async def predicate(self, ctx, *args, **kwargs):
        """
        :param self: the cog the command is in e.g Music or Custom
        :param ctx: the context object of the current invoked command
        :param args: the arguments a command can take e.g channel_id
        :param kwargs: in case a commands gets kwargs but idk a case where this could happen
        :return: returns the awaited command
        """
        embed = await func(self, ctx, *args, **kwargs)
        cmdchannel = ctx.bot.get_channel(ctx.bot.cache.states[ctx.guild.id].get_channel("cmd"))
        if cmdchannel is not None:
            await cmdchannel.send(embed=embed)
            await ctx.bot.log.stdout(cmdchannel, ctx.message.content, ctx)
        else:
            stdoutchannel = ctx.bot.get_channel(ctx.bot.cache.states[ctx.guild.id].get_channel())
            await ctx.bot.log.stdout(stdoutchannel, ctx.message.content, ctx)
    return predicate


def logging_to_channel_stdout(func):
    """
    This decorator will log to the logging channel that a commands was issued.
    If the channel isn't set then logging will be skipped.
    :param func: the called function, its always a coroutine
    :return: the original function
    """
    @functools.wraps(func)
    async def predicate(self, ctx, *args, **kwargs):
        """
        :param self: the cog the command is in e.g Music or Custom
        :param ctx: the context object of the current invoked command should always contain the bot object if none then
        nothing will be logged as I don't see a need in logging events
        :param args: the arguments a command can take e.g channel_id
        :param kwargs: in case a commands gets kwargs but idk a case where this could happen
        :return: returns the awaited command
        """
        if ctx.bot:
            stdoutchannel = ctx.bot.get_channel(ctx.bot.cache.states[ctx.guild.id].get_channel())
            sig = signature(func)
            if stdoutchannel is not None:
                try:
                    if sig.parameters["ex"]:
                        await ctx.bot.log.stdout(stdoutchannel, ctx.message.content, ctx, True, args[0])
                        return await func(self, ctx, *args, **kwargs)
                except KeyError:
                    pass
                await ctx.bot.log.stdout(stdoutchannel, ctx.message.content, ctx)
        return await func(self, ctx, *args, **kwargs)
    return predicate


def purge_command_in_channel(func):
    """
    This decorator will just purge the ctx.message in the channel where the command was issued.
    :param func: the called function, its always a coroutine
    :return: the original function
    """
    @functools.wraps(func)
    async def predicate(self, ctx, *args, **kwargs):
        """
        :param self: the cog the command is in e.g Music or Custom
        :param ctx: the context object of the current invoked command
        :param args: the arguments a command can take e.g channel_id
        :param kwargs: in case a commands gets kwargs but idk a case where this could happen
        :return: returns the awaited command
        """
        try:
            await ctx.message.delete()
        except discord.HTTPException:
            pass
        return await func(self, ctx, *args, **kwargs)
    return predicate


def banned_user_list_cmd(func):
    """
    This basically checks if a user is permitted to use a command
    regardless of the position the user has e.g mod or admin
    :param func: the called function, its always a coroutine
    :return:  the original coroutine
    """
    @functools.wraps(func)
    async def predicate(self, ctx, *args, **kwargs):
        user_list = ctx.bot.cache.states[ctx.guild.id].banned_users_cmd
        if ctx.author in user_list:
            return await func(self, ctx, *args, **kwargs)
        raise Exception("Permission denied")
    return predicate


def banned_roles_list_cmd(func):
    """
    This basically checks if a user has a role that is permitted to use a command
    regardless of the position the user has e.g mod or admin
    :param func: the called function, its always a coroutine
    :return:  the original coroutine
    """
    @functools.wraps(func)
    async def predicate(self, ctx, *args, **kwargs):
        role_list = ctx.bot.cache.states[ctx.guild.id].banned_roles_cmd
        for role in ctx.author.roles:
            if role.id in role_list:
                raise MissingRole(role)
        return await func(self, ctx, *args, **kwargs)
    return predicate


def banned_channel_list_cmd(func):
    """
    This basically checks if the bot is permitted to use a command in that channel/ if users are permitted to execute
    commands in that channel
    :param func: the called function, its always a coroutine
    :return:  the original coroutine
    """
    @functools.wraps(func)
    async def predicate(self, ctx, *args, **kwargs):
        channel_list = ctx.bot.cache.states[ctx.guild.id].banned_channels_cmd
        if ctx.channel in channel_list:
            raise Exception("Permission denied")
        return await func(self, ctx, *args, **kwargs)
    return predicate


def banned_user_list_spam(func):
    """
    This basically checks if a user should be ignored in the spam system
    :param func: the called function, its always a coroutine
    :return:  the original coroutine
    """
    @functools.wraps(func)
    async def predicate(self, ctx, *args, **kwargs):
        user_list = ctx.bot.cache.states[ctx.guild.id].banned_users_spam
        if ctx.author in user_list:
            raise Exception("Permission denied")
        return await func(self, ctx, *args, **kwargs)
    return predicate


def banned_roles_list_spam(func):
    """
    This basically checks if a user has a role that should be ignored in the spam system
    :param func: the called function, its always a coroutine
    :return:  the original coroutine
    """
    @functools.wraps(func)
    async def predicate(self, ctx, *args, **kwargs):
        role_list = ctx.bot.cache.states[ctx.guild.id].banned_roles_spam
        for role in ctx.author.roles:
            if role.id in role_list:
                raise MissingRole(role)
        return await func(self, ctx, *args, **kwargs)
    return predicate


def banned_channel_list_spam(func):
    """
    This basically checks if the bot is permitted to use check for spam in that channel
    :param func: the called function, its always a coroutine
    :return:  the original coroutine
    """
    @functools.wraps(func)
    async def predicate(self, ctx, *args, **kwargs):
        channel_list = ctx.bot.cache.states[ctx.guild.id].banned_channels_spam
        if ctx.channel in channel_list:
            raise Exception("Permission denied")
        return await func(self, ctx, *args, **kwargs)
    return predicate


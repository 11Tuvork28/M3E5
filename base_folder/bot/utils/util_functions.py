import datetime
from copy import deepcopy
from datetime import datetime
from string import Template

import discord
from discord.embeds import EmptyEmbed

"""
A short utility for random functions which don't fit into an object
"""


def prefix(client, ctx):
    try:
        pre = client.cache.states[ctx.guild.id].get_prefix
        return pre
    except Exception:
        return "-"


def loadmodules(modules, client):
    for extension in modules:
        try:
            client.load_extension(extension)
            print('Loaded extension {}'.format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))



"""
LICENSE
The MIT License (MIT)
Copyright (c) 2020 Skelmis
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
LICENSE
"""


def embed_to_string(embed) -> str:
    """
    Parameters
    ----------
    embed : discord.Embed
        The embed to turn into a string
    Returns
    -------
    str
        The content of the string
    """
    content = ""
    embed = embed.to_dict()

    if "title" in embed:
        content += f"{embed['title']}\n"

    if "description" in embed:
        content += f"{embed['description']}\n"

    if "footer" in embed:
        if "text" in embed["footer"]:
            content += f"{embed['footer']['text']}\n"

    if "author" in embed:
        if "name" in embed["author"]:
            content += f"{embed['author']['name']}\n"

    if "fields" in embed:
        for field in embed["fields"]:
            content += f"{field['name']}\n{field['value']}\n"

    return content


def dict_to_embed(data, message, counts):
    """
    Given a dictionary, will attempt to build a
    valid discord.Embed object to return
    Parameters
    ----------
    data : dict
        The given item to try build an embed from
    message : discord.Message
        Where we get all our info from
    counts : dict
        Our current warn & kick counts
    Returns
    -------
    discord.Embed
    """
    allowed_avatars = ["$USERAVATAR", "$BOTAVATAR", "$GUILDICON"]

    if "title" in data:
        data["title"] = substitute_args(data["title"], message, counts)

    if "description" in data:
        data["description"] = substitute_args(data["description"], message, counts)

    if "footer" in data:
        if "text" in data["footer"]:
            data["footer"]["text"] = substitute_args(
                data["footer"]["text"], message, counts
            )

        if "icon_url" in data["footer"]:
            if data["footer"]["icon_url"] in allowed_avatars:
                data["footer"]["icon_url"] = substitute_args(
                    data["footer"]["icon_url"], message, counts
                )

    if "author" in data:
        if "name" in data["author"]:
            data["author"]["name"] = substitute_args(
                data["author"]["name"], message, counts
            )

        if "icon_url" in data["author"]:
            if data["author"]["icon_url"] in allowed_avatars:
                data["author"]["icon_url"] = substitute_args(
                    data["author"]["icon_url"], message, counts
                )

    if "fields" in data:
        for field in data["fields"]:
            name = substitute_args(field["name"], message, counts)
            value = substitute_args(field["value"], message, counts)
            field["name"] = name
            field["value"] = value

            if "inline" not in field:
                field["inline"] = True

    if "timestamp" in data:
        data["timestamp"] = message.created_at.isoformat()

    if "colour" in data:
        data["color"] = data["colour"]

    data["type"] = "rich"

    return discord.Embed.from_dict(data)


def substitute_args(message, value, counts) -> str:
    """
    Given the options string, return the string
    with the relevant values substituted in
    Parameters
    ----------
    message : str
        The string to substitute with values
    value : discord.Message
        Where we get our values from to substitute
    counts : dict
        Our current warn & kick counts
    Returns
    -------
    str
        The correctly substituted message
    """
    return Template(message).safe_substitute(
        {
            "MENTIONUSER": value.author.mention,
            "USERNAME": value.author.display_name,
            "USERID": value.author.id,
            "BOTNAME": value.guild.me.display_name,
            "BOTID": value.guild.me.id,
            "GUILDID": value.guild.id,
            "GUILDNAME": value.guild.name,
            "TIMESTAMPNOW": datetime.now().strftime("%I:%M:%S %p, %d/%m/%Y"),
            "TIMESTAMPTODAY": datetime.now().strftime("%d/%m/%Y"),
            "WARNCOUNT": counts["warn_count"],
            "KICKCOUNT": counts["kick_count"],
            "USERAVATAR": value.author.avatar_url,
            "BOTAVATAR": value.guild.me.avatar_url,
            "GUILDICON": value.guild.icon_url,
        }
    )


def transform_message(item, value, counts):
    """
    Given an item of two possible values, create
    and return the correct thing
    Parameters
    ----------
    item : [str, dict]
        Either a straight string or dict to turn in an embed
    value : discord.Message
        Where things come from
    counts : dict
        Our current warn & kick counts
    Returns
    -------
    [str, discord.Embed]
    """
    if isinstance(item, str):
        return substitute_args(item, value, counts)

    return dict_to_embed(deepcopy(item), value, counts)


async def send_to_obj(messageable_obj, message) -> discord.Message:
    """
    Send a given message to an abc.messageable object
    This does not handle exceptions, they should be handled
    on call as I did not want to overdo this method with
    the required params to notify users.
    Parameters
    ----------
    messageable_obj : abc.Messageable
        Where to send message
    message : str, dict
        The message to send
        Can either be a straight string or a discord.Embed
    Raises
    ------
    discord.HTTPException
        Failed to send
    discord.Forbidden
        Lacking permissions to send
    Returns
    =======
    discord.Message
        The sent messages object
    """
    if isinstance(message, discord.Embed):
        return await messageable_obj.send(embed=message)
    return await messageable_obj.send(message)


def log_embed(msg):
    e = discord.Embed(
        color=discord.Color.blurple(),
        title="DEBUG",
        description=msg,
    )
    e.set_footer(text="Server time:" + str(datetime.now()))
    e.set_author(name="M3E5", url="https://github.com/11tuvork28/m3e5")
    return e


def success_embed(client):
    e = build_embed(
        title="Success!",
        author=client.user.name,
        author_img=client.user.avatar_url,
        timestamp=datetime.now(),
        footer=client.user.name)
    return e


def error_embed(client):
    e = build_embed(
        title="Error!",
        author=client.user.name,
        author_img=client.user.avatar_url,
        timestamp=datetime.now(),
        color=discord.Color.red())
    return e


def build_embed(**params):
    # Copyright 2017 Zack Rauen www.ZackRauen.com
    title = params.get("title", EmptyEmbed)
    description = params.get("description", EmptyEmbed)
    color = params.get("color", discord.Color.blurple())
    url = params.get("url", EmptyEmbed)
    author = params.get("author", "")
    author_url = params.get("author_url", EmptyEmbed)
    author_img = params.get("author_img", EmptyEmbed)
    footer = params.get("footer", "")
    footer_img = params.get("footer_img", EmptyEmbed)
    timestamp = params.get("timestamp", EmptyEmbed)
    image = params.get("image", "")
    thumbnail = params.get("thumbnail", "")
    sections = params.get("sections", params.get("fields", []))
    e = discord.Embed()
    e.title = title
    e.description = description
    e.colour = color
    e.url = url
    if author:
        e.set_author(name=author, url=author_url, icon_url=author_img)
    if footer:
        e.set_footer(text=footer, icon_url=footer_img)
    e.timestamp = timestamp
    e.set_image(url=image)
    e.set_thumbnail(url=thumbnail)
    if sections:
        populate(e, sections)
    return e


def populate(embed: discord.Embed, sections: list):
    # Copyright 2017 Zack Rauen www.ZackRauen.com
    for section in sections:
        name = section.get("name", "")
        value = section.get("value", "")
        inline = section.get("inline", True)
        if not name or not value:
            continue
        embed.add_field(name=name, value=value, inline=inline)
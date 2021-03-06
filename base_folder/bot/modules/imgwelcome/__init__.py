import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import aiohttp
from io import BytesIO
import textwrap
import base64
from discord.ext import commands

from base_folder.bot.utils.Permissions_checks import admin, mod
from base_folder.celery.db import edit_settings_img_text, edit_settings_img
from base_folder.bot.utils.checks import check_args_datatyp, logging_to_channel_stdout, purge_command_in_channel


'''
MIT License

Copyright (c) 2018-2019 https://github.com/hibikidesu/

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''


class IMGWelcome(commands.Cog):
    def __init__(self, bot):
        self.client = bot

    async def __is_enabled(self, guild: int):
        if self.client.cache.states[guild].get_imgtoggle == 1:
            return True
        else:
            return False

    @commands.group(pass_context=True, name="imgwelcome", brief="imgwelcome toggle/text/img")
    @commands.has_permissions(administrator=True)
    async def imgwelcome(self, ctx):
        # Base command
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @imgwelcome.command(name="toggle", brief="Toggle the imgwelcome feature", usage="imgwelcome togle")
    @admin()
    @check_args_datatyp
    @logging_to_channel_stdout
    @purge_command_in_channel
    async def imgwelcome_toggle(self, ctx):
        """Toggle on/off the imgwelcome"""
        toggle = int(await self.client.sql.get_img(ctx.guild.id))
        if 0 == toggle:
            await ctx.send("Welcome image is now enabled")
            edit_settings_img.delay(ctx.guild.id, 1)
        else:
            await ctx.send("Welcome image is now disabled")
            edit_settings_img.delay(ctx.guild.id, 0)

    @imgwelcome.command(pass_context=True, name="img", brief="Sets the welcome image", usage="imgwelcome img")
    @mod()
    @check_args_datatyp
    @logging_to_channel_stdout
    @purge_command_in_channel
    async def imgwelcome_img(self, ctx):
        """Set the image"""
        if not await self.__is_enabled(ctx.guild.id):
            return await ctx.send("Enable imgwelcoming with n!imgwelcome toggle")

        if len(ctx.message.attachments) == 0:

            await ctx.send("Send an image or type anything without sending an image to reset back to default.")

            def check(m):
                return m.author == ctx.message.author and m.channel == ctx.message.channel

            try:
                msg = await self.client.wait_for('message', check=check, timeout=20)
            except:
                return await ctx.send("Timed out.")

        else:
            msg = ctx.message

        if len(msg.attachments) >= 1:
            attachment = str(msg.attachments[0].url).rpartition(".")[2]
            if attachment.lower() not in ["png", "jpg", "jpeg", "gif"]:
                return await ctx.send("Not a valid image type <>")
            if os.path.exists(f"data/imgwelcome/{ctx.guild.id}.png"):
                os.remove(f"data/imgwelcome/{ctx.guild.id}.png")
            try:
                async with aiohttp.ClientSession() as cs:
                    async with cs.get(msg.attachments[0].url) as r:
                        imgdata = await r.read()
                img = Image.open(BytesIO(imgdata)).convert("RGBA").resize((500, 150))
                bg = Image.new("RGBA", (500, 150), (0, 0, 0, 0))
                bg.alpha_composite(img, (0, 0))
                bg.save(f"data/imgwelcome/{ctx.guild.id}.png")
                await ctx.send("Set image!")
            except Exception as e:
                await ctx.send("Failed to set image... `{}`".format(e))
        else:
            if os.path.exists(f"data/imgwelcome/{ctx.guild.id}.png"):
                os.remove(f"data/imgwelcome/{ctx.guild.id}.png")
            await ctx.send("Reset Image.")

    @imgwelcome.command(pass_context=True, name="text", brief="Sets the text of the img", usage="imgwelcome text")
    @mod()
    @check_args_datatyp
    @logging_to_channel_stdout
    @purge_command_in_channel
    async def imgwelcome_text(self, ctx, *, text: str):
        """Change the welcome text,
            user = the user's name
            server = the server's name
        Example:
            n!imgwelcome text Welcome user to server!
        """
        if not await self.__is_enabled(ctx.guild.id):
            return await ctx.send("imgwelcome is not enabled")

        text = base64.b64encode(text.encode("utf8")).decode("utf8")
        await ctx.send("Updated text!")
        edit_settings_img_text.delay(ctx.guild.id, text)

    @imgwelcome.command(pass_context=True, name="test", brief="Tests the imgwelcome command", usage="imgwelcome test")
    @mod()
    @check_args_datatyp
    @logging_to_channel_stdout
    @purge_command_in_channel
    async def imgwelcome_test(self, ctx):
        member: discord.member = ctx.author
        await self.on_member_join(member)

    def _circle_border(self, circle_img_size: tuple):
        border_size = []
        for i in range(len(circle_img_size)):
            border_size.append(circle_img_size[0] + 8)
        return tuple(border_size)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        channel = self.client.get_channel(self.client.cache.states[member.guild.id].get_channel("welcome"))
        print("test")
        if not channel:
            return
        if await self.__is_enabled(member.guild.id):
            pass
        else:
            r = await self.client.sql.get_img_text(guild.id)
            print(r)
            content = base64.b64decode(str(r).encode("utf8")).decode("utf8")\
                .replace("user", member.mention)\
                .replace("server", guild.name)
            await channel.send(content)
            return
        await channel.trigger_typing()

        if os.path.exists(f"base_folder/bot/data/imgwelcome/{guild.id}.png"):
            background = Image.open(f"base_folder/bot/data/imgwelcome/{guild.id}.png").convert("RGBA")
        else:
            background = Image.open(os.path.realpath("base_folder/bot/data/imgwelcome/transparent.png"))

        async with aiohttp.ClientSession() as cs:
            async with cs.get(str(member.avatar_url_as(format="png"))) as res:
                imgdata = await res.read()

        welcome_picture = ImageOps.fit(background, (500, 150), centering=(0.5, 0.5))
        welcome_picture.paste(background)
        welcome_picture = welcome_picture.resize((500, 150), Image.NEAREST)

        profile_area = Image.new("L", (512, 512), 0)
        draw = ImageDraw.Draw(profile_area)
        draw.ellipse(((0, 0), (512, 512)), fill=255)
        profile_area = profile_area.resize((128, 128), Image.ANTIALIAS)
        profile_picture = Image.open(BytesIO(imgdata))
        profile_area_output = ImageOps.fit(profile_picture, (128, 128), centering=(0, 0))
        profile_area_output.putalpha(profile_area)

        mask = Image.new('L', (512, 512), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (512, 512), fill=255, outline=0)
        circle = Image.new("RGBA", (512, 512))
        draw_circle = ImageDraw.Draw(circle)
        draw_circle.ellipse([0, 0, 512, 512], fill=(255, 255, 255, 180), outline=(255, 255, 255, 250))
        circle_border_size = self._circle_border((128, 128))
        circle = circle.resize(circle_border_size, Image.ANTIALIAS)
        circle_mask = mask.resize(circle_border_size, Image.ANTIALIAS)
        circle_pos = (7 + int((136 - circle_border_size[0]) / 2))
        border_pos = (11 + int((136 - circle_border_size[0]) / 2))
        drawtwo = ImageDraw.Draw(welcome_picture)
        welcome_picture.paste(circle, (circle_pos, circle_pos), circle_mask)
        welcome_picture.paste(profile_area_output, (border_pos, border_pos), profile_area_output)

        uname = (str(member.name) + "#" + str(member.discriminator))

        def _outline(original_position: tuple, text: str, pixel_displacement: int, font, textoutline):
            op = original_position
            pd = pixel_displacement

            left = (op[0] - pd, op[1])
            right = (op[0] + pd, op[1])
            up = (op[0], op[1] - pd)
            down = (op[0], op[1] + pd)

            drawtwo.text(left, text, font=font, fill=(textoutline))
            drawtwo.text(right, text, font=font, fill=(textoutline))
            drawtwo.text(up, text, font=font, fill=(textoutline))
            drawtwo.text(down, text, font=font, fill=(textoutline))

            drawtwo.text(op, text, font=font, fill=(textoutline))

        welcome_font = ImageFont.truetype("base_folder/bot/data/fonts/UniSansHeavy.otf", 50)

        _outline((150, 16), "Welcome", 1, welcome_font, (0, 0, 0, 255))
        drawtwo.text((150, 16), "Welcome", font=welcome_font, fill=(255, 255, 255, 230))
        name_font = ImageFont.truetype("base_folder/bot/data/fonts/UniSansHeavy.otf", 30)
        name_font_medium = ImageFont.truetype("base_folder/bot/data/fonts/UniSansHeavy.otf", 22)
        name_font_small = ImageFont.truetype("base_folder/bot/data/fonts/UniSansHeavy.otf", 18)
        name_font_smallest = ImageFont.truetype("base_folder/bot/data/fonts/UniSansHeavy.otf", 12)
        server_font = ImageFont.truetype("base_folder/bot/data/fonts/UniSansHeavy.otf", 22)

        if len(uname) <= 17:
            _outline((152, 63), uname, 1, name_font, (0, 0, 0, 255))
            drawtwo.text((152, 63), uname, font=name_font, fill=(255, 255, 255, 230))

        if len(uname) > 17:
            if len(uname) <= 23:
                _outline((152, 66), uname, 1, name_font_medium, (0, 0, 0, 255))
                drawtwo.text((152, 66), uname, font=name_font_medium, fill=(255, 255, 255, 230))

        if len(uname) >= 24:
            if len(uname) <= 32:
                _outline((152, 70), uname, 1, name_font_small, (0, 0, 0, 255))
                drawtwo.text((152, 70), uname, font=name_font_small, fill=(255, 255, 255, 230))

        if len(uname) >= 33:
            drawtwo.text((152, 73), uname, 1, name_font_smallest, (0, 0, 0, 255))
            drawtwo.text((152, 73), uname, font=name_font_smallest, fill=(255, 255, 255, 230))

        server_text = "\n".join(textwrap.wrap(f"Welcome to {guild.name}!", 25))
        _outline((152, 100), server_text, 1, server_font, (0, 0, 0, 255))
        drawtwo.text((152, 100), server_text, font=server_font, fill=(255, 255, 255, 230))

        welcome_picture.save(os.path.realpath("base_folder/bot/data/welcome.png"))

        try:
            r = await self.client.sql.get_img_text(guild.id)
            content = base64.b64decode(str(r).encode("utf8")).decode("utf8")\
                .replace("user", member.mention)\
                .replace("server", guild.name)
        except:
            content = "Welcome {} to {}!".format(member.name, guild.name)

        file = discord.File("base_folder/bot/data/welcome.png", filename="welcome.png")

        await channel.send(file=file, content=content)


def setup(bot):
    bot.add_cog(IMGWelcome(bot))

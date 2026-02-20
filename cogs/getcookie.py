import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

class GetCookie(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="getcookie", description="获取Cookie教程")
    async def getcookie(self,interaction: discord.Interaction):
        embed=discord.Embed(
            title="获取Cookie教程",
            description="请按照以下步骤获取Cookie:\n 1.点击该链接 https://game.skport.com/endfield/sign-in?header=0&hg_media=launcher&hg_link_campaign=icon\n 2.登录账号\n3.按下F12打开开发者工具\n4.点击Application\n5.在左侧点击Cookie后按下F5\n6.找到名为Account_Token并复制(记得打开Show URL-decoded)\n7.用/entercookie命令之后粘贴复制的内容",
            color=discord.Color.random(),
        )
        embed.set_footer(text="仅自己可见")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GetCookie(bot))

import discord
import base64
from discord.ext import commands
from discord import app_commands

class EnterCookie(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @app_commands.command(name="输入cookie", description="输入cookie")
    async def entercookie(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Modalclass(self.bot))
        
class Modalclass(discord.ui.Modal,title="输入cookie"):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    CookieID=discord.ui.TextInput(label="请输入Account_Token",style=discord.TextStyle.short,placeholder="Account_Token",required=True)
    async def on_submit(self,interaction:discord.Interaction):
        encode=base64.b64encode(self.CookieID.value.encode()).decode()
        UID=str(interaction.user.id)
        cursor=await self.bot.db.execute("SELECT COUNT(*) FROM User WHERE DiscordID=? and Cookie=?", (UID, encode))
        number=await cursor.fetchone()
        await cursor.close()
        if number[0]>0:
            embed=discord.Embed(
                title="错误",
                description=f"数据库已有该Cookie记录", 
                color=discord.Color.random(),
            )
            await interaction.response.send_message(embed=embed,ephemeral=True)
        else:
            await self.bot.db.execute("INSERT INTO User(DiscordID,Cookie) VALUES (?,?)",(str(UID),encode))
            await self.bot.db.commit()
            embed=discord.Embed(
                title="成功",
                description=f"Cookie已保存", 
                color=discord.Color.random(),
            )
            await interaction.response.send_message(embed=embed,ephemeral=True)
            print (f"用户 {UID} 已绑定 Cookie")

async def setup(bot):
    await bot.add_cog(EnterCookie(bot))

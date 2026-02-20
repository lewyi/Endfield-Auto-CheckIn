import discord
import base64
from discord.ext import commands
from discord import app_commands

class EnterCookie(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    @app_commands.command(name="输入cookie", description="输入cookie")
    async def entercookie(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Modalclass())
        
class Modalclass(discord.ui.Modal,title="输入cookie"):
    name=discord.ui.TextInput(label="请输入Account_Token",style=discord.TextStyle.short,placeholder="Account_Token",required=True)
    async def on_submit(self,interaction:discord.Interaction):
        with open("data\\user.txt","a") as f:
            encode=base64.b64encode(self.name.value.encode()).decode()
            if any(encode in line for line in open("data\\user.txt")):
                await interaction.response.send_message("⚠ 已存在相同的Cookie",ephemeral=True)
                return
            f.write(f"{interaction.user.id}:{encode}\n")
            await interaction.response.send_message("✅ 已保存Cookie",ephemeral=True)
    
    
async def setup(bot):
    await bot.add_cog(EnterCookie(bot))

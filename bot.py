import os
import asyncio
import discord
from discord.ext import commands

TOKEN="输入discord_Token"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = "!", intents = intents)

#启动时
@bot.event
async def on_ready():
    slash=await bot.tree.sync()
    print(f"ID--> {bot.user}")
    print(f"加载了 {len(slash)} 個指令")


# 加载文件
@bot.command()
@commands.has_permissions(administrator=True)
async def load(ctx, extension):
    await bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Loaded {extension} done.")
    

# 卸载文件
@bot.command()
@commands.has_permissions(administrator=True)
async def unload(ctx, extension):
    await bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"UnLoaded {extension} done.")

# 重新加载指定文件
@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, extension):
    await bot.reload_extension(f"cogs.{extension}")
    await ctx.send(f"ReLoaded {extension} done.")

# 运行时自动加载所有指令
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"Loaded {filename} done.")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

#运行
if __name__ == "__main__":
    asyncio.run(main())
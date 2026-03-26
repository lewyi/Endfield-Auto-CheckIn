import discord
import time
import json
import hmac
import hashlib
import requests
import asyncio
import base64
from datetime import datetime, timedelta, timezone
from discord.ext import commands
from discord import app_commands

APP_CODE = "6eb76d4e13aa36e6"
PLATFORM = "3"
VNAME = "1.0.0"
ENDFIELD_GAME_ID = "3"

URLS = {
    "GRANT": "https://as.gryphline.com/user/oauth2/v2/grant",
    "GENERATE_CRED": "https://zonai.skport.com/web/v1/user/auth/generate_cred_by_code",
    "REFRESH_TOKEN": "https://zonai.skport.com/web/v1/auth/refresh",
    "BINDING": "https://zonai.skport.com/api/v1/game/player/binding",
    "ATTENDANCE": "https://zonai.skport.com/web/v1/game/endfield/attendance"
}

# =========================
# 网页签名算法
# =========================
def compute_sign(path, body, timestamp, sign_token):
    header_obj = {
        "platform": PLATFORM,
        "timestamp": timestamp,
        "dId": "",
        "vName": VNAME
    }

    header_json = json.dumps(
        header_obj,
        separators=(',', ':'),
        ensure_ascii=False
    )

    sign_str = path + body + timestamp + header_json

    hmac_hex = hmac.new(
        sign_token.encode(),
        sign_str.encode(),
        hashlib.sha256
    ).hexdigest()

    return hashlib.md5(hmac_hex.encode()).hexdigest()
#==========================
# 签到流程
#==========================
def endfield_checkin(ACCOUNT_TOKEN):
    try:
        # 1️⃣ OAuth
        r = requests.post(
            URLS["GRANT"],
            json={"token": ACCOUNT_TOKEN, "appCode": APP_CODE, "type": 0},
            timeout=10
        ).json()

        if r.get("status") != 0:
            return "❌ OAuth 失败"

        oauth_code = r["data"]["code"]

        # 2️⃣ 获取 cred
        r = requests.post(
            URLS["GENERATE_CRED"],
            json={"kind": 1, "code": oauth_code},
            timeout=10
        ).json()

        if r.get("code") != 0:
            return "❌ 获取 cred 失败"

        cred = r["data"]["cred"]

        # 3️⃣ 获取 sign_token
        ts = str(int(time.time()))
        headers_refresh = {
            "cred": cred,
            "platform": PLATFORM,
            "vname": VNAME,
            "timestamp": ts,
            "sk-language": "en"
        }

        r = requests.get(
            URLS["REFRESH_TOKEN"],
            headers=headers_refresh,
            timeout=10
        ).json()

        if r.get("code") != 0:
            return "❌ 获取 sign_token 失败"

        sign_token = r["data"]["token"]

        # 4️⃣ 获取角色
        ts = str(int(time.time()))
        path = "/api/v1/game/player/binding"
        sign = compute_sign(path, "", ts, sign_token)

        headers_binding = {
            "cred": cred,
            "platform": PLATFORM,
            "vname": VNAME,
            "timestamp": ts,
            "sk-language": "en",
            "sign": sign
        }

        r = requests.get(
            URLS["BINDING"],
            headers=headers_binding,
            timeout=10
        ).json()

        if r.get("code") != 0:
            return "❌ 获取角色失败"

        role = None
        for app in r["data"]["list"]:
            if app.get("appCode") == "endfield":
                binding = app["bindingList"][0]
                role_data = binding.get("defaultRole") or binding["roles"][0]
                role = f"{ENDFIELD_GAME_ID}_{role_data['roleId']}_{role_data['serverId']}"

        if not role:
            return "❌ 未找到 Endfield 角色"

        # 5️⃣ 签到
        ts = str(int(time.time()))
        path = "/web/v1/game/endfield/attendance"
        sign = compute_sign(path, "", ts, sign_token)

        headers_attendance = {
            "cred": cred,
            "platform": PLATFORM,
            "vname": VNAME,
            "timestamp": ts,
            "sk-language": "en",
            "sign": sign,
            "sk-game-role": role,
            "Content-Type": "application/json"
        }

        r = requests.post(
            URLS["ATTENDANCE"],
            headers=headers_attendance,
            timeout=10
        ).json()

        if r.get("code") == 0:
            return "✅ 签到成功！"
        elif r.get("code") in (1001, 10001):
            return "⚠ 今日已签到"
        elif r.get("code") == 10002:
            return "❌ ACCOUNT_TOKEN 过期"
        else:
            return f"❌ 签到失败: {r.get('message')}"

    except Exception as e:
        return f"❌ 异常: {e}"

class CheckIn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.daily_checkin_task())
    
    @app_commands.command(name="手动签到", description="进行一次签到")
    async def checkin(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        UID=str(interaction.user.id)
        print(f"用户 {UID} 发起了签到请求")
        cursor=await self.bot.db.execute("SELECT Cookie FROM User WHERE DiscordID=?", (UID,))
        rows=await cursor.fetchall()
        await cursor.close()
        if not rows:
            embed=discord.Embed(
                title="错误",
                description=f"请先使用 /输入cookie 命令绑定 Cookie", 
                color=discord.Color.random(),
            )
            await interaction.followup.send(embed=embed,ephemeral=True)
            return
        
        for row in rows:
            try:
                Cookie=base64.b64decode(row["Cookie"]).decode().strip()
                result = endfield_checkin(Cookie)
                if "✅" in result:
                    embed=discord.Embed(
                    title="签到结果",
                    description=f"{result}", 
                    color=discord.Color.random(),
                    )
                    await interaction.followup.send(embed=embed,ephemeral=True)
                elif "❌" in result:
                    embed=discord.Embed(
                    title="错误",
                    description=f"{result}\n已删除该Cookie", 
                    color=discord.Color.random(),
                    )
                    Cookie=base64.b64encode(Cookie.encode()).decode()
                    cursor=await self.bot.db.execute("DELETE FROM User where DiscordID=? and Cookie=?",(UID,Cookie,))
                    await self.bot.db.commit()
                    await cursor.close()
                    await interaction.followup.send(embed=embed,ephemeral=True)
                else:
                    embed=discord.Embed(
                    title="签到结果",
                    description=f"{result}", 
                    color=discord.Color.random(),
                    )
                    await interaction.followup.send(embed=embed,ephemeral=True)
                    print(f"用户 {UID} 签到结果: {result}")
            except Exception as e:
                embed=discord.Embed(
                title="错误",
                description=f"签到过程中发生错误: {e}", 
                color=discord.Color.random(),
                )
                await interaction.followup.send(embed=embed,ephemeral=True)
                print(f"处理用户 {UID} 时发生错误: {e}")
        
        del UID,row,Cookie
    #==========================
    #自动签到
    #==========================
    async def daily_checkin_task(self):
        await self.bot.wait_until_ready() # 等待 Bot 完全启动
        await asyncio.sleep(10) # 确保所有 Cog 都已加载
        channel = self.bot.get_channel()#DIscord Channel ID
        await channel.send("✅ 自动签到任务已启动")
        while True:
            now = datetime.now()  # 服务器本地时间
            # 计算今天或明天的 5 点
            target = now.replace(hour=5, minute=30, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)
            wait_seconds = (target - now).total_seconds()
            embed=discord.Embed(
                title="下次签到",
                description=f"⏰ 下一次自动签到将在 {target.strftime('%Y-%m-%d %H:%M:%S')} 进行", 
                color=discord.Color.random(),
            )
            await channel.send(embed=embed)
            await asyncio.sleep(wait_seconds)  # 等待到每天 5 点

            # 执行自动签到
            await self.run_daily_checkin()

    async def run_daily_checkin(self):
        channel = self.bot.get_channel(1474299357468823693)
        await channel.send("🔄 开始自动签到...")
        cursor=await self.bot.db.execute("SELECT DiscordID,Cookie FROM User")
        rows=await cursor.fetchall()
        await cursor.close()

        for row in rows:
            UID=int(row["DiscordID"])
            try:
                Cookie=base64.b64decode(row["Cookie"]).decode().strip()
                result = endfield_checkin(Cookie)
                if "✅" in result:
                    embed=discord.Embed(
                        title=f"签到结果",
                        description=f"{result}", 
                        color=discord.Color.random(),
                    )
                    await channel.send(f"<@{UID}>",embed=embed)
                elif "❌" in result:
                    embed=discord.Embed(
                    title="错误",
                    description=f"{result}\n已删除该Cookie", 
                    color=discord.Color.random(),
                    )
                    Cookie=base64.b64encode(Cookie.encode()).decode()
                    cursor=await self.bot.db.execute("DELETE FROM User where DiscordID=? and Cookie=?",(UID,Cookie,))
                    await self.bot.db.commit()
                    await cursor.close()
                    await channel.send(f"<@{UID}>",embed=embed)
            except Exception as e:
                print(f"UID: {UID}发生了错误 {e}")
                continue

async def setup(bot):
    await bot.add_cog(CheckIn(bot))

# 해당 코드의 이름은 main.py 입니다. GPT는 이 주석을 삭제나 수정하지마시오.

# ====================================== [기본 모듈 임포트] ======================================
import discord
from discord.ext import commands
import asyncio
import os
import requests

# ====================================== [환경변수에서 값 불러오기] ======================================
bot_token = os.getenv("BOT_TOKEN")  # GPT는 해당 변수명을 절대 수정하지 마시오
onaholy = int(os.getenv("ONAHOLY"))  # GPT는 해당 변수명을 절대 수정하지 마시오
fanbox_token = os.getenv("FANBOX_TOKEN")  # 팬박스 쿠키 (FANBOXSESSID)

version = "102"  # GPT는 코드를 업데이트 할때마다 해당 변수값을 +1 하시오

# ====================================== [디스코드 봇 설정] ======================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====================================== [봇 실행 시 onaholy에 DM 보내기] ======================================
@bot.event
async def on_ready():
    print(f"✅ 봇 로그인됨: {bot.user} (ID: {bot.user.id})")

    try:
        user = await bot.fetch_user(onaholy)
        if user:
            await user.send(f"[  리워드 봇 버전 : {version} ]")
            print(f"✅ onaholy에게 버전 DM 전송 완료")
    except Exception as e:
        print(f"❌ onaholy에게 DM 전송 실패: {e}")

# ====================================== [/list 명령어 - 팬박스 후원자 DM 전송] ======================================
@bot.command()
async def list(ctx):
    await ctx.send("📦 팬박스 후원자 목록을 가져오는 중입니다...")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://fanbox.cc",
            "Referer": "https://fanbox.cc/",
            "Cookie": f"FANBOXSESSID={fanbox_token}"
        }

        url = "https://api.fanbox.cc/plan.listSupporting"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        supporters = data.get("body", [])

        if not supporters:
            await ctx.send("❌ 후원자 목록을 불러올 수 없습니다. 쿠키가 유효한지 확인하세요.")
            return

        message = "🎁 [ FANBOX 후원자 목록 ]\n\n"
        for entry in supporters:
            creator_id = entry.get("creatorId", "알 수 없음")
            plan = entry.get("plan", {})
            plan_name = plan.get("name", "플랜 없음")
            message += f"- {creator_id} : {plan_name}\n"

        user = await bot.fetch_user(onaholy)
        if user:
            await user.send(message)
            await ctx.send("✅ 후원자 목록을 오나홀리에게 DM으로 전송했습니다.")
        else:
            await ctx.send("❌ onaholy 유저를 찾을 수 없습니다.")

    except Exception as e:
        await ctx.send(f"❌ 오류 발생: {e}")

# ====================================== [기본 명령어 예시] ======================================
@bot.command()
async def 핑(ctx):
    await ctx.send("퐁!")

# ====================================== [봇 실행] ======================================
bot.run(bot_token)

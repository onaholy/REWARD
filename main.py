# 해당 코드의 이름은 main.py 입니다. GPT는 이 주석을 삭제나 수정하지마시오.

# ====================================== [기본 모듈 임포트] ======================================
import discord
from discord.ext import commands
import asyncio
import os

# ====================================== [환경변수에서 값 불러오기] ======================================
bot_token = os.getenv("BOT_TOKEN")  # GPT는 해당 변수명을 절대 수정하지 마시오
onaholy = int(os.getenv("ONAHOLY"))  # GPT는 해당 변수명을 절대 수정하지 마시오

version = "101"  # GPT는 코드를 업데이트 할때마다 해당 변수값을 +1 하시오

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

# ====================================== [기본 명령어 예시] ======================================
@bot.command()
async def 핑(ctx):
    await ctx.send("퐁!")

# ====================================== [봇 실행] ======================================
bot.run(bot_token)

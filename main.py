# 해당 코드의 이름은 main.py 입니다. GPT는 이 주석을 삭제나 수정하지마시오.

# ====================================== [기본 모듈 임포트] ======================================
import discord
from discord.ext import commands
import asyncio
import os
import re
import sys

# ====================================== [환경변수에서 값 불러오기] ======================================
bot_token = os.getenv("BOT_TOKEN")  # GPT는 해당 변수명을 절대 수정하지 마시오
onaholy = int(os.getenv("ONAHOLY"))  # GPT는 해당 변수명을 절대 수정하지 마시오

version = "102"  # GPT는 코드를 업데이트 할때마다 해당 변수값을 +1 하시오

# ====================================== [디스코드 봇 설정] ======================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True  # DM 메시지 수신을 위한 설정

bot = commands.Bot(command_prefix="!", intents=intents)

# ====================================== [인스턴스 중복 방지 및 on_ready 처리] ======================================
@bot.event
async def on_ready():
    print(f"✅ 봇 로그인됨: {bot.user} (ID: {bot.user.id})")

    try:
        user = await bot.fetch_user(onaholy)
        if user:
            # 최근 DM 메시지 확인
            dms = await user.history(limit=10).flatten()
            latest_version = None

            for msg in dms:
                if msg.author.id == bot.user.id:
                    match = re.search(r"\[  리워드 봇 버전 : (\d+) \]", msg.content)
                    if match:
                        latest_version = match.group(1)
                        break

            if latest_version and int(latest_version) > int(version):
                print(f"❌ 현재 인스턴스 종료됨 (최신 버전: {latest_version}, 현재 버전: {version})")
                await user.send(f"🔴 중복 방지: 현재 실행된 [{version}] 인스턴스가 [{latest_version}]보다 낮아 종료됨.")
                await bot.close()
                os._exit(0)

            await user.send(f"[  리워드 봇 버전 : {version} ]")
            print(f"✅ onaholy에게 버전 DM 전송 완료")

    except Exception as e:
        print(f"❌ onaholy에게 DM 전송 실패: {e}")

# ====================================== [onaholy가 리워드 종료 시 인스턴스 강제 종료] ======================================
@bot.event
async def on_message(message):
    # DM에서만 반응, 보낸 사람이 onaholy인지 확인
    if isinstance(message.channel, discord.DMChannel) and message.author.id == onaholy:
        content = message.content.strip()
        if content == "리워드 종료":
            print("🛑 onaholy의 종료 명령 감지됨. 인스턴스를 종료합니다.")
            await message.channel.send("🔒 모든 인스턴스 종료됨.")
            await bot.close()
            os._exit(0)

    await bot.process_commands(message)  # 명령어 처리 유지

# ====================================== [기본 명령어 예시] ======================================
@bot.command()
async def 핑(ctx):
    await ctx.send("퐁!")

# ====================================== [봇 실행] ======================================
bot.run(bot_token)

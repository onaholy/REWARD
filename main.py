# 해당 코드의 이름은 main.py 입니다. GPT는 이 주석을 삭제나 수정하지마시오.

# ====================================== [기본 모듈 임포트] ======================================
import discord
from discord.ext import commands
import asyncio
import os
import re
import sys

print("📦 모듈 임포트 완료")

# ====================================== [환경변수에서 값 불러오기] ======================================
try:
    bot_token = os.getenv("BOT_TOKEN")  # GPT는 해당 변수명을 절대 수정하지 마시오
    if not bot_token:
        raise ValueError("❌ BOT_TOKEN 환경변수가 비어있습니다.")
    print("✅ BOT_TOKEN 로딩 성공")

    onaholy_str = os.getenv("ONAHOLY")
    if not onaholy_str:
        raise ValueError("❌ ONAHOLY 환경변수가 비어있습니다.")

    onaholy = int(onaholy_str)  # GPT는 해당 변수명을 절대 수정하지 마시오
    print(f"✅ ONAHOLY 로딩 성공: {onaholy}")

except Exception as e:
    print(f"❌ 환경변수 로딩 오류: {e}")
    sys.exit(1)

version = "107"  # GPT는 코드를 업데이트 할때마다 해당 변수값을 +1 하시오

# ====================================== [디스코드 봇 설정] ======================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====================================== [봇 실행 시 onaholy에 DM 보내기 및 중복 체크] ======================================
@bot.event
async def on_ready():
    print(f"✅ 봇 로그인됨: {bot.user} (ID: {bot.user.id})")
    bot.loop.create_task(check_newer_version_loop())

    try:
        print(f"📌 ONAHOLY 환경변수: {onaholy}")
        user = await bot.fetch_user(onaholy)
        print(f"📌 onaholy 유저 객체: {user}")

        if user:
            print("📩 DM 기록 가져오는 중...")
            dms = await user.history(limit=10).flatten()
            latest_version = None

            for msg in dms:
                if msg.author.id == bot.user.id:
                    match = re.search(r"\[  리워드 봇 버전 : (\d+) \]", msg.content)
                    if match:
                        latest_version = match.group(1)
                        break

            if latest_version and int(latest_version) > int(version):
                print(f"❌ 중복 인스턴스 감지됨. 종료.")
                await user.send(f"🔴 중복 방지: 현재 실행된 [{version}] 인스턴스가 [{latest_version}]보다 낮아 종료됨.")
                await bot.close()
                os._exit(0)

            print("📩 onaholy에게 버전 알림 전송 중...")
            await user.send(f"[  리워드 봇 버전 : {version} ]")
            print("✅ 버전 DM 전송 완료")

        else:
            print("❌ fetch_user 결과가 None입니다.")

        await bot.tree.sync()
        print("✅ 슬래시 명령어 동기화 완료")

    except Exception as e:
        print(f"❌ on_ready 처리 중 오류: {e}")

# ====================================== [주기적으로 DM에서 최신 버전 확인 후 자동 종료] ======================================
async def check_newer_version_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            user = await bot.fetch_user(onaholy)
            dms = await user.history(limit=5).flatten()
            for msg in dms:
                if msg.author.id == bot.user.id:
                    match = re.search(r"\[  리워드 봇 버전 : (\d+) \]", msg.content)
                    if match and int(match.group(1)) > int(version):
                        print(f"🛑 감지된 최신 버전: {match.group(1)} > 현재: {version}. 종료합니다.")
                        await bot.close()
                        os._exit(0)
        except Exception as e:
            print(f"❌ 주기적 버전 확인 중 오류: {e}")
        await asyncio.sleep(10)

# ====================================== [onaholy가 DM으로 '리워드 종료' 시 즉시 셧다운] ======================================
@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel):
        if message.author.id == onaholy:
            content = message.content.strip()

            if content == "리워드 종료":
                print("🛑 onaholy의 수동 종료 명령 감지됨. 인스턴스를 종료합니다.")
                await message.channel.send("🔒 모든 인스턴스 종료됨.")
                await bot.close()
                os._exit(0)

            elif content.lower() == "list":
                try:
                    await message.channel.send("✅ 후원자 목록:\n- 예시1\n- 예시2\n(실제 구현 필요)")
                    print("📩 onaholy에게 후원자 목록 전송됨")
                except Exception as e:
                    print(f"❌ 후원자 목록 전송 실패: {e}")

    await bot.process_commands(message)

# ====================================== [텍스트 명령어] ======================================
@bot.command()
async def 핑(ctx):
    await ctx.send("퐁!")

# ====================================== [슬래시 명령어 등록] ======================================
@bot.tree.command(name="list", description="리워드 봇의 커맨드 목록을 보여줍니다.")
async def list_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "✅ 사용 가능한 명령어:\n- `/list`\n- `/reward`\n- `!핑`\n- `DM으로 list 입력 시 후원자 목록 확인 가능`", ephemeral=True
    )

@bot.tree.command(name="reward", description="리워드 관련 기능을 실행합니다.")
async def reward_command(interaction: discord.Interaction):
    await interaction.response.send_message("🎁 리워드 기능은 아직 개발 중입니다.", ephemeral=True)

# ====================================== [봇 실행] ======================================
print("🚀 봇 실행 시작")
bot.run(bot_token)


# 해당 코드의 이름은 main.py 입니다. GPT는 이 주석을 삭제나 수정하지마시오.

# ====================================== [기본 모듈 임포트] ======================================
import discord
from discord.ext import commands, tasks
import asyncio
import os
import re
import sys
import requests
import imaplib
import email
from email.header import decode_header

print("📦 모듈 임포트 완료")

# ====================================== [환경변수에서 값 불러오기] ======================================
try:
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("❌ BOT_TOKEN 환경변수가 비어있습니다.")
    print("✅ BOT_TOKEN 로딩 성공")

    onaholy_str = os.getenv("ONAHOLY")
    if not onaholy_str:
        raise ValueError("❌ ONAHOLY 환경변수가 비어있습니다.")
    onaholy = int(onaholy_str)
    print(f"✅ ONAHOLY 로딩 성공: {onaholy}")

    gmail_user = os.getenv("GMAIL_ID")
    gmail_pass = os.getenv("GMAIL_PASSWARD")
    if not gmail_user or not gmail_pass:
        raise ValueError("❌ Gmail 관련 환경변수가 비어있습니다.")
    print("✅ Gmail 계정 로딩 성공")

except Exception as e:
    print(f"❌ 환경변수 로딩 오류: {e}")
    sys.exit(1)

version = "114"  # GPT는 이 주석을 변경하거나 삭제하지마시오! GPT는 이 글을 볼때마다 버전을 +1 증가시키시오

# ====================================== [디스코드 봇 설정] ======================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
last_uid = None

# ====================================== [Gmail에서 FANBOX 알림 감지 함수] ======================================
def check_fanbox_mail():
    global last_uid
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, gmail_pass)
        mail.select("inbox")
        result, data = mail.search(None, "ALL")
        mail_ids = data[0].split()
        if not mail_ids:
            return []

        new_subjects = []
        for mail_id in reversed(mail_ids[-10:]):  # 최근 10개 메일 확인
            if last_uid and mail_id <= last_uid:
                break

            result, data = mail.fetch(mail_id, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            if "pixivFANBOX" in subject and "지원을 시작했습니다" in subject:
                new_subjects.append(subject)

        if mail_ids:
            last_uid = mail_ids[-1]

        return list(reversed(new_subjects))
    except Exception as e:
        print(f"❌ Gmail 감지 중 오류: {e}")
        return []

# ====================================== [주기적 Gmail 감지 루프] ======================================
@tasks.loop(seconds=30)
async def monitor_gmail_loop():
    await bot.wait_until_ready()
    try:
        new_subjects = check_fanbox_mail()
        for subject in new_subjects:
            user = await bot.fetch_user(onaholy)
            await user.send(f"📬 [FANBOX 메일 수신]\n```{subject}```")
            print(f"📨 팬박스 메일 전달됨: {subject}")
    except Exception as e:
        print(f"❌ FANBOX Gmail 알림 루프 중 오류: {e}")

# ====================================== [봇 실행 시 처리] ======================================
@bot.event
async def on_ready():
    print(f"✅ 봇 로그인됨: {bot.user} (ID: {bot.user.id})")
    bot.loop.create_task(check_newer_version_loop())
    monitor_gmail_loop.start()
    try:
        user = await bot.fetch_user(onaholy)
        await user.send(f"[  리워드 봇 버전 : {version} ]")
        print("✅ 버전 DM 전송 완료")
    except Exception as e:
        print(f"❌ DM 전송 실패: {e}")

# ====================================== [주기적으로 최신 버전 확인] ======================================
async def check_newer_version_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            user = await bot.fetch_user(onaholy)
            async for msg in user.history(limit=5):
                if msg.author.id == bot.user.id:
                    match = re.search(r"\[  리워드 봇 버전 : (\d+) \]", msg.content)
                    if match and int(match.group(1)) > int(version):
                        print(f"🛑 감지된 최신 버전: {match.group(1)} > 현재: {version}. 종료합니다.")
                        await bot.close()
                        os._exit(0)
        except Exception as e:
            print(f"❌ 버전 확인 오류: {e}")
        await asyncio.sleep(10)

# ====================================== [onaholy가 DM으로 list 시 안내만 전송] ======================================
@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel):
        if message.author.id == onaholy:
            content = message.content.strip().lower()
            if content == "리워드 종료":
                await message.channel.send("🔒 모든 인스턴스 종료됨.")
                await bot.close()
                os._exit(0)
            elif content == "list":
                await message.channel.send("📭 현재 팬박스 쿠키 기능은 제거되었습니다.")
    await bot.process_commands(message)

# ====================================== [텍스트 명령어] ======================================
@bot.command()
async def 핑(ctx):
    await ctx.send("퐁!")

# ====================================== [슬래시 명령어 등록] ======================================
@bot.tree.command(name="list", description="리워드 봇의 커맨드 목록을 보여줍니다.")
async def list_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "✅ 사용 가능한 명령어:\n- `/list`\n- `/reward`\n- `!핑`\n- `DM으로 list 입력 시 안내`", ephemeral=True
    )

@bot.tree.command(name="reward", description="리워드 관련 기능을 실행합니다.")
async def reward_command(interaction: discord.Interaction):
    await interaction.response.send_message("🎁 리워드 기능은 아직 개발 중입니다.", ephemeral=True)

# ====================================== [봇 실행] ======================================
print("🚀 봇 실행 시작")
bot.run(bot_token)

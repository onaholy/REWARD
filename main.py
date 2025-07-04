# 해당 코드의 이름은 main.py 입니다. GPT는 이 주석을 삭제나 수정하지마시오. GPT는 코드를 요청할때 코드 전문을 출력하시오. GPT는 version 변수를 볼때마다 +1 씩 업데이트하시오.

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
import json
from email.header import decode_header
from datetime import datetime, timezone

# ====================================== [main.py코드 버전] ======================================
version = "150"

# ====================================== [환경변수에서 값 불러오기] ======================================
try:
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN 환경변수가 비어있습니다.")

    onaholy_str = os.getenv("ONAHOLY")
    if not onaholy_str:
        raise ValueError("ONAHOLY 환경변수가 비어있습니다.")
    onaholy = int(onaholy_str)

    gmail_user = os.getenv("GMAIL_ID")
    gmail_pass = os.getenv("GMAIL_PASSWARD")
    if not gmail_user or not gmail_pass:
        raise ValueError("Gmail 관련 환경변수가 비어있습니다.")

except Exception as e:
    sys.exit(1)

# ====================================== [시스템 시작 시간] ======================================
boot_time_obj = datetime.now(timezone.utc)
boot_time = boot_time_obj.timestamp()
boot_display = f"{boot_time_obj.day}일 {boot_time_obj.hour}시 {boot_time_obj.minute}분"

# ====================================== [프로그램 데이터 저장] ======================================
supporter_list = []
SUPPORTER_FILE = "list.json"

def save_supporters():
    with open(SUPPORTER_FILE, "w", encoding="utf-8") as f:
        json.dump(supporter_list, f, ensure_ascii=False, indent=2)

def load_supporters():
    global supporter_list
    if os.path.exists(SUPPORTER_FILE):
        with open(SUPPORTER_FILE, "r", encoding="utf-8") as f:
            supporter_list = json.load(f)
    else:
        supporter_list = []

# ====================================== [디스코드 봇 설정] ======================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
last_uid = None

# ====================================== [봇 시작 시] ======================================
@bot.event
async def on_ready():
    load_supporters()
    periodic_instance_check.start()
    monitor_gmail_loop.start()
    try:
        user = await bot.fetch_user(onaholy)
        await user.send(f"[ 리워드 봇 버전 : {version}        -         시작 시간 : {boot_display} ]")
    except Exception:
        pass

# ====================================== [7초마다 인스턴스 중복 확인] ======================================
@tasks.loop(seconds=7)
async def periodic_instance_check():
    user = await bot.fetch_user(onaholy)
    async for msg in user.history(limit=200):
        if msg.author.id != bot.user.id:
            continue
        if "[ 리워드 봇 버전 :" not in msg.content:
            continue

        match = re.search(r"시작 시간 : (\d+)일 (\d+)시 (\d+)분", msg.content)
        if match:
            try:
                day, hour, minute = map(int, match.groups())
                now = datetime.now(timezone.utc)
                previous = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                previous_time = previous.timestamp()
                if previous_time > boot_time:
                    await user.send("[ 인스턴스 중복으로 종료됨: 더 최신 인스턴스 감지 ]")
                    await bot.close()
                    os._exit(0)
            except:
                continue

# ====================================== [Gmail 검색] ======================================
async def check_fanbox_mail_and_debug():
    global last_uid
    matched_subjects = []
    inspected_subjects = []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, gmail_pass)
        mail.select("inbox")
        result, data = mail.search(None, "UNSEEN")
        mail_ids = data[0].split()

        user = await bot.fetch_user(onaholy)

        if not mail_ids:
            await user.send("📪 Gmail에 검사할 새 메일이 없습니다.")
            return matched_subjects

        for i in mail_ids[-5:]:
            if i == last_uid:
                continue

            result, data = mail.fetch(i, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            decoded = decode_header(msg["Subject"])
            subject_parts = []
            for part, enc in decoded:
                if isinstance(part, bytes):
                    subject_parts.append(part.decode(enc or "utf-8", errors="ignore"))
                else:
                    subject_parts.append(part)
            subject = ''.join(subject_parts).strip()

            keyword_hit = any(k in subject for k in ["지원을", "시작했습니다", "에서의", "0 회원!", "님이 새로 가입"])
            inspected_subjects.append(f"{'✅' if keyword_hit else '❌'} {subject}")

            if keyword_hit:
                if "님이 새로 가입했습니다" in subject:
                    match = re.search(r"회원! .*? (.*?)님이", subject)
                    platform = "Patreon"
                else:
                    match = re.search(r"^(.*?) 님이", subject)
                    platform = "Fanbox"

                if match:
                    name = match.group(1).strip()
                    full = f"{name} ({platform})"
                    if full not in supporter_list:
                        supporter_list.append(full)
                        save_supporters()
                        matched_subjects.append(full)
                        last_uid = i

        if inspected_subjects:
            subject_block = "\n".join(inspected_subjects)
            await user.send(f"[ 검사된 메일 제목 목록 ]\n```\n{subject_block}\n```")
        else:
            await user.send("📭 최근 메일 중 검사된 제목이 없습니다.")

    except Exception as e:
        user = await bot.fetch_user(onaholy)
        await user.send(f"❌ Gmail 검사 중 오류:\n```{str(e)}```")

    return matched_subjects

# ====================================== [주기적 Gmail 검색 루프] ======================================
@tasks.loop(seconds=30)
async def monitor_gmail_loop():
    await bot.wait_until_ready()
    try:
        user = await bot.fetch_user(onaholy)
        new_subjects = await check_fanbox_mail_and_debug()
        if new_subjects:
            for subj in new_subjects:
                await user.send(f"[ 새 후원자 : \"{subj}\" ]")
        else:
            await user.send("[ 새 후원자 없음 ]")
    except Exception as e:
        user = await bot.fetch_user(onaholy)
        await user.send(f"❌ FANBOX 루프 오류:\n```{str(e)}```")

# ====================================== [onaholy가 DM으로 명령어 입력 시 처리] ======================================
@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel):
        if message.author.id == onaholy:
            content = message.content.strip().lower()
            if content in ["종료", "리셋", "/종료", "/리셋", "/리워드 종료", "리워드 종료"]:
                await message.channel.send("🔒 모든 인스턴스 종료됨.")
                await bot.close()
                os._exit(0)
            elif content in ["리스트 리셋"]:
                supporter_list.clear()
                save_supporters()
                await message.channel.send("📛 후원자 목록이 초기화되었습니다.")
            elif content in ["list", "리스트", "명단", "/list", "/리스트"]:
                if not supporter_list:
                    await message.channel.send("📭 저장된 후원자 정보가 없습니다.")
                else:
                    supporters = "\n".join(f"{i+1}. {s}" for i, s in enumerate(supporter_list))
                    total = len(supporter_list)
                    response = f"📄 저장된 후원자 목록 (총 {total}명):\n```\n{supporters}\n```"
                    await message.channel.send(response)
            elif content in ["checkmail", "메일검사", "메일", "/checkmail", "/메일"]:
                await message.channel.send("📬 Gmail을 수동으로 검사합니다...")
                new_subjects = await check_fanbox_mail_and_debug()
                if new_subjects:
                    for subj in new_subjects:
                        await message.channel.send(f"[ 새 후원자 : \"{subj}\" ]")
                else:
                    await message.channel.send("[ 새 후원자 없음 ]")
    await bot.process_commands(message)

# ====================================== [슬래시 명령어 등록] ======================================
@bot.tree.command(name="list", description="리워드 버스의 커맨드 목록을 보여줍니다.")
async def list_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "✅ 사용 가능한 명령어:\n- `/list`\n- `/reward`\n- `/checkmail`\n- `DM으로 list, 메일검사 등 입력 가능`",
        ephemeral=True
    )

@bot.tree.command(name="reward", description="리워드 관련 기능을 실행합니다.")
async def reward_command(interaction: discord.Interaction):
    await interaction.response.send_message("🏱 리워드 기능은 아직 개발 중입니다.", ephemeral=True)

@bot.tree.command(name="checkmail", description="Gmail을 수동으로 검사하고 결과를 표시합니다.")
async def check_mail_command(interaction: discord.Interaction):
    await interaction.response.send_message("📬 Gmail을 검사 중입니다...", ephemeral=True)
    user = await bot.fetch_user(onaholy)
    new_subjects = await check_fanbox_mail_and_debug()
    if new_subjects:
        for subj in new_subjects:
            await user.send(f"[ 새 후원자 : \"{subj}\" ]")
    else:
        await user.send("[ 새 후원자 없음 ]")

# ====================================== [봇 실행] ======================================
bot.run(bot_token)

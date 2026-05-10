import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
import json

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

BLOCKED_FILE = 'blocked_users.json'

def load_blocked():
    if os.path.exists(BLOCKED_FILE):
        with open(BLOCKED_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_blocked(data):
    with open(BLOCKED_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@bot.event
async def on_ready():
    print(f'Bot is online: {bot.user}')

@bot.event
async def on_member_join(member):
    now = datetime.now(timezone.utc)
    account_age = (now - member.created_at).days
    days_left = 30 - account_age
    blocked_users = load_blocked()
    user_id = str(member.id)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    # בדיקה אם היוזר נחסם בעבר
    if user_id in blocked_users:
        previous = blocked_users[user_id]
        if log_channel:
            await log_channel.send(
                f'🔄 **Returning Blocked User**\n'
                f'**Username:** {member.name}\n'
                f'**Account ID:** {member.id}\n'
                f'**Previously blocked on:** {previous["blocked_date"]}\n'
                f'**Account Age now:** {account_age} days'
            )

    # בדיקה אם החשבון צעיר מ-30 יום
    if account_age < 30:

        # שמירה בקובץ
        blocked_users[user_id] = {
            'username': member.name,
            'blocked_date': now.strftime('%Y-%m-%d %H:%M UTC'),
            'account_age': account_age
        }
        save_blocked(blocked_users)

        # הודעה פרטית למשתמש
        try:
            await member.send(
                '🦇 The gates remain closed...\n\n'
                'To protect this sanctuary from spam, bots, and malicious activity, '
                'entry is restricted to older Discord accounts.\n\n'
                'If you believe this restriction was applied in error or need assistance, '
                'please contact us at [vampairteam@gmail.com](mailto:vampairteam@gmail.com)\n\n'
                'Thank you for your understanding.'
            )
        except:
            pass

        # התראה בערוץ הלוגים
        if log_channel:
            await log_channel.send(
                f'⚠️ **User Blocked**\n'
                f'**Username:** {member.name}\n'
                f'**Account ID:** {member.id}\n'
                f'**Account Age:** {account_age} days\n'
                f'**Days until eligible:** {days_left} days\n'
                f'**Account Created:** {member.created_at.strftime("%Y-%m-%d")}'
            )

        # העף את המשתמש
        await member.kick(reason='The gates remain closed - need older discord user')

bot.run(TOKEN)
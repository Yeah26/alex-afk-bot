import discord
from discord.ext import commands, tasks
import datetime
import json
import os
import requests
from dotenv import load_dotenv
from keep_alive import keep_alive
import traceback

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

def log_webhook(message):
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": message})
        except:
            print("[!] Webhook küldés sikertelen.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

activity_file = "activity.json"
if not os.path.exists(activity_file):
    with open(activity_file, "w") as f:
        json.dump({}, f)

@bot.event
async def on_ready():
    print(f"[BOT BEJELENTKEZETT] {bot.user}")
    check_afk.start()

@bot.event
async def on_error(event, *args, **kwargs):
    with open("error_log.txt", "a") as f:
        f.write(f"HIBA [{event}]:\n")
        traceback.print_exc(file=f)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    with open(activity_file, "r") as f:
        data = json.load(f)
    data[str(message.author.id)] = datetime.datetime.now().isoformat()
    with open(activity_file, "w") as f:
        json.dump(data, f)
    await bot.process_commands(message)

@tasks.loop(hours=24)
async def check_afk():
    now = datetime.datetime.now()
    with open(activity_file, "r") as f:
        data = json.load(f)
    for guild in bot.guilds:
        afk_role = discord.utils.get(guild.roles, name="AFK")
        if not afk_role:
            afk_role = await guild.create_role(name="AFK")
        afk_channel = discord.utils.get(guild.text_channels, name="╭⯒💭csevegő")
        for member in guild.members:
            if member.bot:
                continue
            last_seen_str = data.get(str(member.id))
            if not last_seen_str:
                continue
            last_seen = datetime.datetime.fromisoformat(last_seen_str)
            if (now - last_seen).days >= 1:
                if afk_role not in member.roles:
                    await member.add_roles(afk_role)
                    try:
                        await member.send("🛌 Helló! Olyan csendben voltál a szerveren, hogy már azt hittük, elraboltak az ufók. 👽 Ezért kaptál egy AFK rangot. Ha visszatértél a galaxisból, csak írd be a szerveren: `!on` és újra menő leszel! 😎")
                        log_webhook(f"⚠️ {member.name} megkapta az AFK rangot.")
                    except:
                        print(f"[!] Nem tudtam üzenetet küldeni {member.name} tagnak.")
                    if afk_channel:
                        await afk_channel.send(f"⚠️ {member.mention} már 1 napja nem aktív, ezért megkapta az **AFK** rangot.")

@bot.command()
async def on(ctx):
    afk_role = discord.utils.get(ctx.guild.roles, name="AFK")
    afk_channel = discord.utils.get(ctx.guild.text_channels, name="╭⯒💭csevegő")
    if afk_role in ctx.author.roles:
        await ctx.author.remove_roles(afk_role)
        await ctx.send(f"{ctx.author.mention} visszatért az élők közé! 😎")
        if afk_channel:
            await afk_channel.send(f"✅ {ctx.author.mention} visszatért és levette az **AFK** rangot.")
        log_webhook(f"✅ {ctx.author.name} visszatért az AFK-ból.")
    else:
        await ctx.send(f"{ctx.author.mention} te nem is voltál AFK, ne kamuzz! 😂")

@bot.command()
async def afkok(ctx):
    afk_role = discord.utils.get(ctx.guild.roles, name="AFK")
    if not afk_role:
        await ctx.send("Még nincs AFK rang a szerveren.")
        return
    afk_members = [member.mention for member in ctx.guild.members if afk_role in member.roles]
    if afk_members:
        await ctx.send(f"📋 **AFK-tagok listája:**\n" + "\n".join(afk_members))
    else:
        await ctx.send("👌 Jelenleg **senki sincs AFK**. Mindenki pörög, mint a Discord Nitro!")

@bot.command()
async def topafk(ctx):
    try:
        with open(activity_file, "r") as f:
            data = json.load(f)
    except:
        await ctx.send("❌ Nem találom az aktivitás fájlt.")
        return
    afk_role = discord.utils.get(ctx.guild.roles, name="AFK")
    if not afk_role:
        await ctx.send("❌ Nincs AFK rang a szerveren.")
        return
    afk_members = []
    now = datetime.datetime.now()
    for member in ctx.guild.members:
        if afk_role in member.roles and str(member.id) in data:
            last_seen = datetime.datetime.fromisoformat(data[str(member.id)])
            diff = now - last_seen
            afk_members.append((member, diff))
    if not afk_members:
        await ctx.send("😎 Mindenki aktív! Ilyen energiával még a bot is beizzadna.")
        return
    afk_members.sort(key=lambda x: x[1], reverse=True)
    msg = "🥇 **TOP AFK-tagok:**\n"
    for i, (member, diff) in enumerate(afk_members[:10], start=1):
        napok = diff.days
        órák = diff.seconds // 3600
        msg += f"{i}. {member.mention} – {napok} nap, {órák} óra inaktivitás\n"
    await ctx.send(msg)

keep_alive()

try:
    bot.run(TOKEN)
except Exception as e:
    with open("error_log.txt", "a") as f:
        f.write(traceback.format_exc() + "\n")
commit: main.py hozzáadva

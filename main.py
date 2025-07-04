import discord
from discord.ext import commands
import re
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=["jai ", "Jai "], intents=intents)

MOD_USER_ID = 1090139157071937616  # Extra mod user ID

# Spiritual message patterns
PATTERNS = {
    r"\bjai\s+shree\s+ram\b": "🚩 जय श्री राम! {user_mention}",
    r"\bjai\s+shree\s+krishna\b": "🕉️ जय श्री कृष्ण! {user_mention}",
    r"\bradhe\s+radhe\b": "🌸 राधे राधे! {user_mention}",
    r"\bradhey\s+radhey\b": "🌸 राधे राधे! {user_mention}",
    r"\bom\s+namah\s+shivaya\b": "🔱 ॐ नमः शिवाय! {user_mention}",
    r"\bjai\s+bhavani\b": "⚔️ जय भवानी! {user_mention}",
    r"\bjai\s+durga\s+maa\b": "🌺 जय दुर्गा माता! {user_mention}",
    r"\bnamah\s+parvati\s+pataye\b": "🔔 हर हर महादेव! {user_mention}",
    r"\bpraise\s+the\s+lord\b": "🙏 Praise the Lord! 🌟 {user_mention}",
    r"\ballah\s+hu\s+akbar\b": "☪️ Allah Hu Akbar! 🤲 {user_mention}"
}

# Moderator role check
def is_moderator():
    async def predicate(ctx):
        if ctx.author.id == MOD_USER_ID:
            return True
        allowed_roles = ["👑 Chhatrapati", "🔊 Mahadeva", "⚔️ Senapati", "🛡️ Dharmarakshak"]
        perms = ctx.author.guild_permissions
        return (
            any(role.name in allowed_roles for role in ctx.author.roles)
            and perms.administrator
            and perms.manage_channels
            and perms.manage_messages
        )
    return commands.check(predicate)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    for pattern, reply in PATTERNS.items():
        if re.search(pattern, message.content, re.IGNORECASE):
            await message.channel.send(reply.format(user_mention=message.author.mention))
            break
    await bot.process_commands(message)

# Mod commands
@bot.command()
@is_moderator()
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Cleared {amount} messages!", delete_after=5)

@bot.command()
@is_moderator()
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member.mention} has been kicked. Reason: {reason}")

@bot.command()
@is_moderator()
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} has been banned. Reason: {reason}")

@bot.command()
@is_moderator()
async def mute(ctx, member: discord.Member, duration: int, *, reason=None):
    guild = ctx.guild
    muted_role = discord.utils.get(guild.roles, name="Muted")
    if not muted_role:
        muted_role = await guild.create_role(name="Muted")
        for channel in guild.channels:
            await channel.set_permissions(muted_role, send_messages=False, speak=False)
    await member.add_roles(muted_role, reason=reason)
    await ctx.send(f"🔇 {member.mention} muted for {duration} minutes. Reason: {reason}")
    await asyncio.sleep(duration * 60)
    await member.remove_roles(muted_role)
    await ctx.send(f"🔊 {member.mention} is now unmuted.")

@bot.command()
@is_moderator()
async def warn(ctx, member: discord.Member, *, reason=None):
    public_msg = f"⚠️ {member.mention} has been warned. Reason: {reason or 'No reason provided.'}"
    await ctx.send(public_msg)
    
    try:
        dm_msg = f"🚨 You have been warned in **{ctx.guild.name}**.\n**Reason:** {reason or 'No reason provided.'}"
        await member.send(dm_msg)
    except discord.Forbidden:
        await ctx.send(f"⚠️ Couldn't DM {member.mention}. They may have DMs disabled.")

@bot.command()
@is_moderator()
async def embed(ctx, *, message):
    embed = discord.Embed(description=message, color=0xff9900)
    await ctx.send(embed=embed)

@bot.command(name="send")
@is_moderator()
async def send_message(ctx, *, message):
    match = re.match(r"<#(\d+)>\s+(.+)", message)
    if match:
        channel_id = int(match.group(1))
        content = match.group(2)
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            await channel.send(content)
            await ctx.send(f"📨 Message sent to {channel.mention}")
        else:
            await ctx.send("❌ Channel not found.")
    else:
        await ctx.send("⚠️ Use: `jai send #channel your message`")

@bot.command()
@is_moderator()
async def roleadd(ctx, permission: str, *, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"❌ Role `{role_name}` not found.")
        return
    perms = role.permissions
    if permission.lower() == "administrator":
        perms.administrator = True
    elif permission.lower() == "manage_channels":
        perms.manage_channels = True
    elif permission.lower() == "manage_messages":
        perms.manage_messages = True
    else:
        await ctx.send("❌ Unknown permission. Try: administrator, manage_channels, manage_messages")
        return
    await role.edit(permissions=perms)
    await ctx.send(f"✅ `{permission}` granted to `{role_name}`.")

@bot.command()
@is_moderator()
async def lock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    overwrite.add_reactions = False
    overwrite.create_public_threads = False
    overwrite.create_private_threads = False
    overwrite.send_messages_in_threads = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔒 Channel fully locked for @everyone.")

@bot.command()
@is_moderator()
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    overwrite.add_reactions = True
    overwrite.create_public_threads = True
    overwrite.create_private_threads = True
    overwrite.send_messages_in_threads = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔓 Channel fully unlocked for @everyone.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ You don't have permission to use that command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ You're missing a required argument.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send("❌ An unexpected error occurred.")

bot.run("MTM3NjE3NDc4MzQ5NDA5OTAxNA.GZBRmz.k5Q8BwgBCVpWnPn-XXsO_3AsxPQoesBldjm-uE")

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import datetime  # Required for the mute/timeout feature

# --- 1. SETUP & CONFIGURATION ---
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Enable intents (Crucial for reading members and message content)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Essential for auto-join roles to work

bot = commands.Bot(command_prefix='!', intents=intents)

# Remove the default help command so we can create a custom one
bot.remove_command('help')


# --- 2. HELP COMMAND ---
@bot.command(name='help', help='Shows this message.')
async def custom_help(ctx):
    """Custom help command using an Embed."""
    embed = discord.Embed(
        title="Bot Commands List",
        description="Here is a list of available moderation commands. Note: You need the appropriate permissions to use them.",
        color=discord.Color.blue()
    )

    # Adding fields for each command
    embed.add_field(name="🧹 !purge <amount>", value="Deletes the specified number of messages.", inline=False)
    embed.add_field(name="👢 !kick @user [reason]", value="Kicks a member from the server.", inline=False)
    embed.add_field(name="🔨 !ban @user [reason]", value="Bans a member from the server.", inline=False)
    embed.add_field(name="🔓 !unban <user_id> [reason]", value="Unbans a user using their User ID.", inline=False)
    embed.add_field(name="⏱️ !mute @user <minutes> [reason]", value="Timeouts a user for a specified duration.",
                    inline=False)
    embed.add_field(name="🔊 !unmute @user [reason]", value="Removes a timeout from a user.", inline=False)

    embed.set_footer(text=f"Requested by {ctx.author.display_name}",
                     icon_url=ctx.author.avatar.url if ctx.author.avatar else None)

    await ctx.send(embed=embed)


# --- 3. MODERATION COMMANDS ---
@bot.command(name='purge', help='Deletes a specified number of messages.')
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    """Deletes the specified amount of messages in the current channel."""
    deleted = await ctx.channel.purge(limit=amount + 1)
    confirmation = await ctx.send(f'✅ Successfully deleted {len(deleted) - 1} messages.')
    await confirmation.delete(delay=3)


@bot.command(name='kick', help='Kicks a member from the server.')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kicks a user. Usage: !kick @user [reason]"""
    await member.kick(reason=reason)
    await ctx.send(f'✅ **{member.display_name}** has been kicked. Reason: {reason}')


@bot.command(name='ban', help='Bans a member from the server.')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    """Bans a user. Usage: !ban @user [reason]"""
    await member.ban(reason=reason)
    await ctx.send(f'🔨 **{member.display_name}** has been banned. Reason: {reason}')


@bot.command(name='unban', help='Unbans a user by their User ID.')
@commands.has_permissions(ban_members=True)
async def unban(ctx, user: discord.User, *, reason="No reason provided"):
    """Unbans a user using their ID. Usage: !unban <user_id> [reason]"""
    await ctx.guild.unban(user, reason=reason)
    await ctx.send(f'✅ Successfully unbanned **{user.display_name}**.')


@bot.command(name='mute', help='Mutes (times out) a user for a specified number of minutes.')
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    """Uses Discord's timeout feature to mute a user. Usage: !mute @user <minutes> [reason]"""
    duration = datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await ctx.send(f'⏱️ **{member.display_name}** has been muted for {minutes} minutes. Reason: {reason}')


@bot.command(name='unmute', help='Removes a timeout from a user.')
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member, *, reason="No reason provided"):
    """Removes a user's timeout. Usage: !unmute @user [reason]"""
    await member.timeout(None, reason=reason)
    await ctx.send(f'🔊 **{member.display_name}** has been unmuted. Reason: {reason}')


# --- 4. AUTO-JOIN ROLES ---
@bot.event
async def on_member_join(member):
    """Automatically assigns a designated role to new members when they join."""

    # IMPORTANT: Change "Member" to the exact name of the role you want to give out.
    # It is case-sensitive!
    role_name = "Member"

    role = discord.utils.get(member.guild.roles, name=role_name)

    if role:
        try:
            await member.add_roles(role)
            print(f"[SUCCESS] Assigned '{role_name}' to {member.display_name}")
        except discord.Forbidden:
            print(f"[ERROR] Bot lacks permission to assign the '{role_name}' role. Check role hierarchy.")
        except discord.HTTPException as e:
            print(f"[ERROR] Failed to assign role to {member.display_name}: {e}")
    else:
        print(f"[WARNING] Could not find a role named '{role_name}' in the server.")


# --- 5. GLOBAL ERROR HANDLING ---
@bot.event
async def on_command_error(ctx, error):
    """A global error handler that catches errors for ALL commands."""

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have the required permissions to use this command.")

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing a required argument: `{error.param.name}`. Type `!help` for usage.")

    elif isinstance(error, commands.BadArgument):
        await ctx.send(
            "❌ Invalid argument provided (e.g., typing letters instead of numbers, or pinging a user that isn't here).")

    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Could not find that member in the server.")

    elif isinstance(error, commands.UserNotFound):
        await ctx.send("❌ Could not find that user. Make sure you are using their valid User ID.")

    else:
        # Catch-all for other potential errors
        await ctx.send(f"⚠️ An error occurred: {error}")


# --- 6. RUN THE BOT ---
if __name__ == '__main__':
    bot.run(token, log_level=logging.DEBUG)

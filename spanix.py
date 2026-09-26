import os
import discord
from discord.ext import commands
import aiohttp
import json

# ==============================================================================
# SPANIX Key Bot — Advanced Discord License Manager
# ==============================================================================

TOKEN    = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")
GUILD_ID = int(os.getenv("GUILD_ID", "1541812030191968338"))

API_URL  = os.getenv("API_URL", "https://prtvshow.online/api_admin.php")
API_KEY  = os.getenv("API_KEY", "YOUR_API_KEY_HERE")
APP_ID   = os.getenv("APP_ID", "9f087d585fbd666572fc24b7")

# Theme Configuration
BOT_NAME      = "SPANIX Key Bot"
EMBED_COLOR   = 0x7289DA  # Blurple / Royal Theme
ERROR_COLOR   = 0xED4245  # Red
SUCCESS_COLOR = 0x57F287  # Green
FOOTER_TEXT   = "Powered by SPANIX Security System"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def call_api(payload: dict) -> dict:
    """Helper to send async API requests using aiohttp."""
    payload["api_key"] = API_KEY
    headers = {"Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload, headers=headers, timeout=12) as resp:
            return await resp.json()

@bot.event
async def on_ready():
    print(f"==================================================")
    print(f"⚡ {BOT_NAME} Online as {bot.user.name}#{bot.user.discriminator}")
    print(f"==================================================")
    
    activity = discord.Activity(type=discord.ActivityType.watching, name="SPANIX License Keys | /spanixhelp")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"✓ Synced {len(synced)} slash commands to Guild ID: {GUILD_ID}")
    except Exception as e:
        print(f"⚠️ Guild sync failed ({e}). Attempting Global Command Sync...")
        try:
            synced = await bot.tree.sync()
            print(f"✓ Synced {len(synced)} slash commands globally across all servers!")
        except Exception as e2:
            print(f"❌ Global sync failed: {e2}")

# ── Global Interaction Listener for Persistent UI Buttons ──
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id", "")
        if ":" in custom_id:
            action, key = custom_id.split(":", 1)
            await interaction.response.defer(ephemeral=True)
            try:
                data = await call_api({"action": action, "key": key, "app_id": APP_ID})
                if data.get("success"):
                    act_title = action.replace("_", " ").upper()
                    embed = discord.Embed(
                        title="⚡ SPANIX Key Action",
                        description=f"✓ **{act_title}** executed successfully for key:\n`{key}`",
                        color=SUCCESS_COLOR
                    )
                    embed.set_footer(text=FOOTER_TEXT)
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    embed = discord.Embed(
                        title="❌ Action Failed",
                        description=f"**Error:** {data.get('message', 'Unknown API Error')}",
                        color=ERROR_COLOR
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"⚠️ **System Error:** {str(e)}", ephemeral=True)

# ── Command: Help & Bot Information ──
@bot.tree.command(name="spanixhelp", description="Display SPANIX Key Bot help menu & available commands.")
async def spanixhelp(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ SPANIX Key Bot Dashboard",
        description="Welcome to **SPANIX License Manager**. Below is the list of available commands:",
        color=EMBED_COLOR
    )
    embed.add_field(name="🔑 /genkey", value="Generate license key(s) with package & duration.", inline=False)
    embed.add_field(name="🔍 /keyinfo", value="Check details, status, package, & HWID of any key.", inline=False)
    embed.add_field(name="🔄 /resethwid", value="Reset HWID binding for a specific license key.", inline=False)
    embed.add_field(name="🚫 /bankey", value="Ban/suspend a license key.", inline=False)
    embed.add_field(name="✅ /unbankey", value="Unban a previously suspended key.", inline=False)
    embed.add_field(name="🗑️ /deletekey", value="Permanently delete a license key.", inline=False)
    embed.add_field(name="📦 /packages", value="View list of all available SPANIX packages.", inline=False)
    embed.set_footer(text=FOOTER_TEXT)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ── Command: Generate License Key ──
@bot.tree.command(name="genkey", description="Generate SPANIX license key(s).")
@discord.app_commands.choices(package=[
    discord.app_commands.Choice(name="BASIC PANEL", value="e52c1515c53453b85d0d4e87"),
    discord.app_commands.Choice(name="AIMSILENT EXE", value="affc8da8fd5ace99981ab877"),
    discord.app_commands.Choice(name="UID BYPASS", value="cb921031dc43197e8ccb6828"),
    discord.app_commands.Choice(name="EXTERNAL PANEL", value="3d1c6c948b4715fbd2fada2d"),
    discord.app_commands.Choice(name="PVT AIMKILL", value="d4f0ce93349f236711344cb5"),
    discord.app_commands.Choice(name="VAULT PANEL", value="154d1edaddd7203fbfd847f4"),
    discord.app_commands.Choice(name="LIB BYPASS", value="db3b90e8134ec738b94a9b05"),
    discord.app_commands.Choice(name="FPS BOOSTER", value="2411bc9db9f9a66c6e876ad2")
])
@discord.app_commands.describe(
    package="Select the SPANIX package",
    days="Validity duration in days (0 = Lifetime)",
    count="Number of keys to generate (max 100)"
)
async def genkey(interaction: discord.Interaction, package: str, days: int = 30, count: int = 1):
    await interaction.response.defer(ephemeral=False)
    payload = {
        "action": "generate_key",
        "app_id": APP_ID,
        "package_id": package,
        "days": days,
        "count": count
    }
    try:
        data = await call_api(payload)
        if data.get("success"):
            # API returns keys directly in data["keys"] or data["data"]["keys"]
            keys = data.get("keys", [])
            if not keys and isinstance(data.get("data"), dict):
                keys = data.get("data", {}).get("keys", [])
                
            dur = "Lifetime" if days == 0 else f"{days} Days"
            pkg_name = data.get("package_name", "SPANIX Package")
            
            embed = discord.Embed(
                title=f"🔑 SPANIX Keys Generated ({pkg_name})",
                description=f"**Generated Count:** `{len(keys)}`\n**Duration:** `{dur}`",
                color=SUCCESS_COLOR
            )
            
            keys_formatted = "\n".join([f"`{k}`" for k in keys])
            if len(keys_formatted) > 1024:
                embed.add_field(name="Keys List", value=f"`{len(keys)} keys generated.`", inline=False)
            else:
                embed.add_field(name="Keys List", value=keys_formatted if keys_formatted else "No keys returned", inline=False)
            
            embed.set_footer(text=FOOTER_TEXT)
            
            if len(keys) == 1:
                key_single = keys[0]
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Reset HWID", custom_id=f"reset_hwid:{key_single}", style=discord.ButtonStyle.primary))
                view.add_item(discord.ui.Button(label="Ban Key", custom_id=f"ban_key:{key_single}", style=discord.ButtonStyle.secondary))
                view.add_item(discord.ui.Button(label="Delete Key", custom_id=f"delete_key:{key_single}", style=discord.ButtonStyle.danger))
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Generation Failed",
                description=f"**API Message:** {data.get('message', 'Unknown Error')}",
                color=ERROR_COLOR
            )
            await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"⚠️ **Error:** {str(e)}")

# ── Command: Check Key Details ──
@bot.tree.command(name="keyinfo", description="Check SPANIX key details, status, and HWID.")
@discord.app_commands.describe(key="The license key to inspect")
async def keyinfo(interaction: discord.Interaction, key: str):
    await interaction.response.defer(ephemeral=True)
    try:
        data = await call_api({"action": "key_info", "app_id": APP_ID, "key": key})
        if data.get("success"):
            kdata = data.get("data") if isinstance(data.get("data"), dict) else data
            
            embed = discord.Embed(title=f"🔍 Key Info: `{key}`", color=EMBED_COLOR)
            embed.add_field(name="Package", value=f"`{kdata.get('package_name', 'N/A')}`", inline=True)
            embed.add_field(name="Status", value=f"`{kdata.get('status', 'N/A')}`", inline=True)
            embed.add_field(name="Expiry / Duration", value=f"`{kdata.get('expiry_date', kdata.get('duration', 'N/A'))}`", inline=True)
            embed.add_field(name="HWID Bound", value=f"`{kdata.get('hwid', 'Not Bound')}`", inline=False)
            embed.set_footer(text=FOOTER_TEXT)
            
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Reset HWID", custom_id=f"reset_hwid:{key}", style=discord.ButtonStyle.primary))
            view.add_item(discord.ui.Button(label="Delete Key", custom_id=f"delete_key:{key}", style=discord.ButtonStyle.danger))
            
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {data.get('message', 'Key not found')}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ **Error:** {str(e)}", ephemeral=True)

# ── Command: Reset HWID ──
@bot.tree.command(name="resethwid", description="Reset HWID for a SPANIX key.")
@discord.app_commands.describe(key="License key to reset")
async def resethwid(interaction: discord.Interaction, key: str):
    await interaction.response.defer(ephemeral=True)
    try:
        data = await call_api({"action": "reset_hwid", "app_id": APP_ID, "key": key})
        if data.get("success"):
            embed = discord.Embed(title="🔄 HWID Reset Success", description=f"HWID reset for key: `{key}`", color=SUCCESS_COLOR)
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {data.get('message', 'Failed to reset HWID')}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ **Error:** {str(e)}", ephemeral=True)

# ── Command: Ban Key ──
@bot.tree.command(name="bankey", description="Ban/suspend a SPANIX license key.")
@discord.app_commands.describe(key="License key to ban")
async def bankey(interaction: discord.Interaction, key: str):
    await interaction.response.defer(ephemeral=True)
    try:
        data = await call_api({"action": "ban_key", "app_id": APP_ID, "key": key})
        if data.get("success"):
            embed = discord.Embed(title="🚫 Key Banned", description=f"Key `{key}` has been banned.", color=ERROR_COLOR)
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {data.get('message', 'Failed to ban key')}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ **Error:** {str(e)}", ephemeral=True)

# ── Command: Unban Key ──
@bot.tree.command(name="unbankey", description="Unban a SPANIX license key.")
@discord.app_commands.describe(key="License key to unban")
async def unbankey(interaction: discord.Interaction, key: str):
    await interaction.response.defer(ephemeral=True)
    try:
        data = await call_api({"action": "unban_key", "app_id": APP_ID, "key": key})
        if data.get("success"):
            embed = discord.Embed(title="✅ Key Unbanned", description=f"Key `{key}` has been unbanned.", color=SUCCESS_COLOR)
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {data.get('message', 'Failed to unban key')}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ **Error:** {str(e)}", ephemeral=True)

# ── Command: Delete Key ──
@bot.tree.command(name="deletekey", description="Permanently delete a SPANIX license key.")
@discord.app_commands.describe(key="License key to delete")
async def deletekey(interaction: discord.Interaction, key: str):
    await interaction.response.defer(ephemeral=True)
    try:
        data = await call_api({"action": "delete_key", "app_id": APP_ID, "key": key})
        if data.get("success"):
            embed = discord.Embed(title="🗑️ Key Deleted", description=f"Key `{key}` was permanently deleted.", color=SUCCESS_COLOR)
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {data.get('message', 'Failed to delete key')}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ **Error:** {str(e)}", ephemeral=True)

# ── Command: List Packages ──
@bot.tree.command(name="packages", description="View all available SPANIX packages.")
async def packages(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        data = await call_api({"action": "get_admin_packages", "app_id": APP_ID})
        if data.get("success"):
            pkgs = data.get("packages", [])
            embed = discord.Embed(title="📦 Available SPANIX Packages", color=EMBED_COLOR)
            for p in pkgs:
                embed.add_field(
                    name=p.get("package_name", "Unknown Package"),
                    value=f"ID: `{p.get('package_id')}`",
                    inline=True
                )
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {data.get('message', 'Failed to load packages')}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ **Error:** {str(e)}", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)

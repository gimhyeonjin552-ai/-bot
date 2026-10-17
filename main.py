import discord
from discord.ext import commands
import os
import logging

logging.basicConfig(
    filename='discord.log',
    encoding='utf-8',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s'
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"로그인 완료: {bot.user.name} (ID: {bot.user.id})")
    
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                print(f"✅ [{cog_name}] 로드 성공")
            except Exception as e:
                print(f"❌ [{cog_name}] 로드 실패: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"🚀 슬래시 명령어 총 {len(synced)}개 동기화 완료!")
    except Exception as e:
        print(f"동기화 실패: {e}")

    print("====================================")
    print("🎉 모든 모듈 및 기능 준비가 완료되었습니다!")
    print("====================================")

@bot.tree.command(name="reload", description="특정 모듈만 껐다 켜지 않고 재로드합니다.")
@discord.app_commands.checks.has_permissions(administrator=True)
async def reload_cog(interaction: discord.Interaction, cog: str):
    try:
        await bot.reload_extension(f"cogs.{cog}")
        await interaction.response.send_message(f"🔄 `cogs.{cog}` 모듈이 성공적으로 재로드되었습니다!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ 재로드 실패: {e}", ephemeral=True)

token = os.getenv("DISCORD_TOKEN")
bot.run(token)
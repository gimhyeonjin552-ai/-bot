import discord
from discord import app_commands
from discord.ext import commands


class UserInfo(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @app_commands.command(name="나", description="나의 회원 정보를 조회합니다.")
  async def my_info(self, interaction: discord.Interaction):
    user = interaction.user

    embed = discord.Embed(
        title=f"👤 {user.display_name}님의 회원 정보",
        color=discord.Color.blue(),
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    embed.add_field(name="디스코드 계정명", value=user.name, inline=True)
    embed.add_field(name="서버 닉네임", value=user.display_name, inline=True)
    embed.add_field(name="고유 ID", value=str(user.id), inline=False)

    joined_date = (
        user.joined_at.strftime("%Y-%m-%d %H:%M")
        if user.joined_at
        else "알 수 없음"
    )
    embed.add_field(name="서버 가입일", value=joined_date, inline=False)

    await interaction.response.send_message(embed=embed)


async def setup(bot):
  await bot.add_cog(UserInfo(bot))
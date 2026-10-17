import discord
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="clear", description="지정한 개수만큼 최근 메시지를 삭제합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def clear_messages(self, interaction: discord.Interaction, count: int):
        if count <= 0:
            await interaction.response.send_message("❌ 1개 이상의 숫자를 입력해주세요.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=count)
        await interaction.followup.send(f"🧹 최근 **{len(deleted)}개**의 메시지를 삭제했습니다!", ephemeral=True)

    @discord.app_commands.command(name="reset", description="현재 채널의 모든 채팅을 싹 지웁니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def reset_channel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        deleted = await interaction.channel.purge(limit=None)
        await interaction.followup.send(f"🧹 채널 내 모든 채팅(총 **{len(deleted)}개**)이 깨끗하게 청소되었습니다!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
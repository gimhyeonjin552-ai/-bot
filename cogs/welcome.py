import discord
from discord.ext import commands
import json
import os

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.filename = "welcome_settings.json"
        self.welcome_data = self.load_data()

    def load_data(self):
        if not os.path.exists(self.filename):
            return {}
        with open(self.filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def save_data(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.welcome_data, f, ensure_ascii=False, indent=4)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id in self.welcome_data and "channel_id" in self.welcome_data[guild_id]:
            channel_id = int(self.welcome_data[guild_id]["channel_id"])
            channel = member.guild.get_channel(channel_id)
            if channel:
                welcome_text = (
                    f"{member.mention} 님 우리모두친구헤오에 오신걸 환영합니다 .ᐟ :B_pure_JY_002:\n"
                    f":31_34_jnx:  밑에 적혀진 안내사항 잘 읽어주시고, 인사도 부탁드립니다   .ᐟ\n\n"
                    f":C_pure_JY_020: ⁠우리모두친구헤오 [ 미오픈 ]⁠︱．📜：서버규칙  과 ⁠우리모두친구헤오 [ 미오픈 ]⁠╭．📢：공지사항  은 중요한 내용들이 담겨있으니 멘션시 확인 해주세요\n"
                    f":C_pure_JY_020: ⁠우리모두친구헤오 [ 미오픈 ]⁠︱．📢：내전공지  도 확인해보시고 많은 관심과 참여 해주세요\n"
                    f":C_pure_JY_020: ⁠우리모두친구헤오 [ 미오픈 ]⁠╭．☁️：메인채팅방  에서 자유로운 채팅과 많은 활동 부탁드립니다\n"
                    f":C_pure_JY_020:  적응이 필요하실 땐 @알-수-없는-역할  언급해주시길 바랍니다\n"
                    f":C_pure_JY_020:  문의 사항이 있다면 ⁠우리모두친구헤오 [ 미오픈 ]⁠╭．📨：건의사항 에 올려주세요\n\n"
                    f"@알-수-없는-역할"
                )
                await channel.send(welcome_text)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id in self.welcome_data and "channel_id" in self.welcome_data[guild_id]:
            channel_id = int(self.welcome_data[guild_id]["channel_id"])
            channel = member.guild.get_channel(channel_id)
            if channel:
                await channel.send(f"🙋‍♂️ {member.display_name} 님이 서버를 떠나셨습니다.")

    @discord.app_commands.command(name="welcome", description="환영 인사 및 퇴장 메시지를 보낼 채널을 설정합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)

        if guild_id not in self.welcome_data:
            self.welcome_data[guild_id] = {}

        self.welcome_data[guild_id]["channel_id"] = str(channel.id)
        self.save_data()

        await interaction.response.send_message(f"✅ 앞으로 환영 및 퇴장 메시지가 {channel.mention} 채널로 전송됩니다!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
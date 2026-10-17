import discord
from discord.ext import commands
import json
import os

class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.filename = "levels.json"
        self.settings_filename = "level_settings.json"
        self.levels_data = self.load_data(self.filename)
        self.settings_data = self.load_data(self.settings_filename)

    def load_data(self, filename):
        if not os.path.exists(filename):
            return {}
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def save_data(self, filename, data):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_needed_exp(self, level):
        return int(100 * (1.077 ** (level - 1)))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        if guild_id not in self.levels_data:
            self.levels_data[guild_id] = {}

        if user_id not in self.levels_data[guild_id]:
            self.levels_data[guild_id][user_id] = {"exp": 0, "level": 1}

        user_data = self.levels_data[guild_id][user_id]
        
        if user_data["level"] >= 50:
            return

        user_data["exp"] += 10

        current_exp = user_data["exp"]
        current_level = user_data["level"]
        
        needed_exp = self.get_needed_exp(current_level)

        if current_exp >= needed_exp:
            user_data["level"] += 1
            user_data["exp"] = 0
            new_level = user_data["level"]
            
            target_channel = message.channel
            if guild_id in self.settings_data and "channel_id" in self.settings_data[guild_id]:
                saved_channel_id = int(self.settings_data[guild_id]["channel_id"])
                found_channel = message.guild.get_channel(saved_channel_id)
                if found_channel:
                    target_channel = found_channel

            if new_level == 50:
                await target_channel.send(
                    f"축하합니다 {message.author.mention}님! 서버의 **최고 레벨(Lv.50)**에 도달하셨습니다!"
                )
            else:
                await target_channel.send(
                    f"축하합니다 {message.author.mention}님! **레벨 {new_level}**로 올랐습니다!"
                )

        self.save_data(self.filename, self.levels_data)

    @discord.app_commands.command(name="경험치", description="현재 자신의 레벨과 경험치를 확인합니다.")
    async def my_exp(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        if guild_id not in self.levels_data or user_id not in self.levels_data[guild_id]:
            await interaction.response.send_message("📊 아직 획득한 경험치가 없습니다. 채팅을 쳐서 레벨을 올려보세요!", ephemeral=True)
            return

        user_data = self.levels_data[guild_id][user_id]
        level = user_data["level"]
        exp = user_data["exp"]
        
        if level >= 50:
            embed = discord.Embed(title=f"👑 {interaction.user.display_name} 님의 레벨 정보 (만렙)", color=discord.Color.gold())
            embed.add_field(name="현재 레벨", value="⭐ Lv.50 (최고 레벨)", inline=True)
            embed.add_field(name="경험치 (EXP)", value="✨ MAX", inline=True)
        else:
            needed_exp = self.get_needed_exp(level)
            embed = discord.Embed(title=f"📊 {interaction.user.display_name} 님의 레벨 정보", color=discord.Color.blue())
            embed.add_field(name="현재 레벨", value=f"⭐ Lv.{level}", inline=True)
            embed.add_field(name="경험치 (EXP)", value=f"✨ {exp} / {needed_exp}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="순위", description="서버 내 레벨 및 경험치 순위 상위 10명을 확인합니다.")
    async def rank_leaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)

        if guild_id not in self.levels_data or not self.levels_data[guild_id]:
            await interaction.response.send_message("📊 아직 서버에 기록된 레벨 데이터가 없습니다.", ephemeral=True)
            return

        sorted_users = sorted(
            self.levels_data[guild_id].items(),
            key=lambda x: (x[1]["level"], x[1]["exp"]),
            reverse=True
        )

        top_users = sorted_users[:10]

        embed = discord.Embed(title=f"🏆 {interaction.guild.name} 레벨 순위 TOP 10", color=discord.Color.orange())
        
        rank_emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        for idx, (user_id, data) in enumerate(top_users):
            member = interaction.guild.get_member(int(user_id))
            name = member.display_name if member else f"유저 ID: {user_id}"
            level = data["level"]
            exp = data["exp"]
            
            if level >= 50:
                exp_str = "MAX"
            else:
                needed_exp = self.get_needed_exp(level)
                exp_str = f"{exp} / {needed_exp}"

            embed.add_field(
                name=f"{rank_emojis[idx]} {idx + 1}위 - {name}",
                value=f"⭐ Lv.{level}  |  ✨ EXP: {exp_str}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="level-up", description="레벨업 알림 메시지를 출력할 채널을 설정합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def set_levelup_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)

        if guild_id not in self.settings_data:
            self.settings_data[guild_id] = {}

        self.settings_data[guild_id]["channel_id"] = str(channel.id)
        self.save_data(self.settings_filename, self.settings_data)

        await interaction.response.send_message(f"✅ 앞으로 레벨업 축하 메시지가 {channel.mention} 채널로 전송됩니다!", ephemeral=True)

    xp_group = discord.app_commands.Group(name="xp", description="관리자 전용 경험치 관리 명령어")

    @xp_group.command(name="add", description="특정 유저에게 경험치를 추가합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def xp_add(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)

        if guild_id not in self.levels_data:
            self.levels_data[guild_id] = {}
        if user_id not in self.levels_data[guild_id]:
            self.levels_data[guild_id][user_id] = {"exp": 0, "level": 1}

        user_data = self.levels_data[guild_id][user_id]
        user_data["exp"] += amount
        
        current_level = user_data["level"]
        if current_level < 50:
            needed_exp = self.get_needed_exp(current_level)
            while user_data["exp"] >= needed_exp and current_level < 50:
                user_data["exp"] -= needed_exp
                user_data["level"] += 1
                current_level = user_data["level"]
                if current_level < 50:
                    needed_exp = self.get_needed_exp(current_level)
                else:
                    user_data["exp"] = 0
                    break

        self.save_data(self.filename, self.levels_data)
        await interaction.response.send_message(f"✅ {member.mention} 님에게 경험치 **{amount} EXP**를 추가했습니다! (현재 Lv.{user_data['level']})", ephemeral=True)

    @xp_group.command(name="set", description="특정 유저의 경험치를 특정 값으로 설정합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def xp_set(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)

        if guild_id not in self.levels_data:
            self.levels_data[guild_id] = {}
        if user_id not in self.levels_data[guild_id]:
            self.levels_data[guild_id][user_id] = {"exp": 0, "level": 1}

        user_data = self.levels_data[guild_id][user_id]
        user_data["exp"] = amount

        self.save_data(self.filename, self.levels_data)
        await interaction.response.send_message(f"✅ {member.mention} 님의 경험치를 **{amount} EXP**로 설정했습니다! (현재 Lv.{user_data['level']})", ephemeral=True)

    @xp_group.command(name="del", description="특정 유저의 경험치를 차감합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def xp_del(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)

        if guild_id not in self.levels_data:
            self.levels_data[guild_id] = {}
        if user_id not in self.levels_data[guild_id]:
            self.levels_data[guild_id][user_id] = {"exp": 0, "level": 1}

        user_data = self.levels_data[guild_id][user_id]
        user_data["exp"] = max(0, user_data["exp"] - amount)

        self.save_data(self.filename, self.levels_data)
        await interaction.response.send_message(f"✅ {member.mention} 님의 경험치를 **{amount} EXP**만큼 차감했습니다! (현재 Lv.{user_data['level']})", ephemeral=True)

    @xp_group.command(name="reset", description="특정 유저의 레벨과 경험치를 완전히 초기화(Lv.1, 0 EXP)합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def xp_reset(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)

        if guild_id not in self.levels_data:
            self.levels_data[guild_id] = {}

        self.levels_data[guild_id][user_id] = {"exp": 0, "level": 1}
        self.save_data(self.filename, self.levels_data)

        await interaction.response.send_message(f"🔄 {member.mention} 님의 레벨과 경험치가 완전히 초기화되었습니다! (Lv.1, 0 EXP)", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Level(bot))
import discord
from discord.ext import commands, tasks
import json
import os
import time
from datetime import timedelta
from collections import defaultdict

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.media_filename = "media_settings.json"
        self.warn_filename = "warnings.json"
        self.log_filename = "log_settings.json"
        self.media_data = self.load_data(self.media_filename)
        self.warn_data = self.load_data(self.warn_filename)
        self.log_data = self.load_data(self.log_filename)
        self.spam_data = defaultdict(list)
        self.last_content = defaultdict(list)
        self.nuke_data = defaultdict(list)
        self.unverified_users = {}
        self.timeout_cooldown = {}
        self.check_unverified_task.start()

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

    async def send_log(self, guild: discord.Guild, text: str):
        guild_id = str(guild.id)
        if guild_id in self.log_data and "channel_id" in self.log_data[guild_id]:
            channel_id = int(self.log_data[guild_id]["channel_id"])
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(text)
                    return
                except:
                    pass

        for channel in guild.text_channels:
            if channel.name in ["로그", "관리자", "조인"]:
                try:
                    await channel.send(text)
                    return
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        now = time.time()
        created_at = member.created_at.timestamp()
        account_age_days = (now - created_at) / 86400

        self.unverified_users[member.id] = now + 600

        log_text = f"🛡️ **[조인 게이트]** {member.mention} 님이 입장하셨습니다.\n- 계정 생성일: {member.created_at.strftime('%Y-%m-%d %H:%M:%S')} (약 {account_age_days:.1f}일 전 생성)"
        await self.send_log(member.guild, log_text)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.id in self.unverified_users:
            del self.unverified_users[member.id]

    @tasks.loop(seconds=30)
    async def check_unverified_task(self):
        now = time.time()
        for guild in self.bot.guilds:
            for member_id, deadline in list(self.unverified_users.items()):
                if now > deadline:
                    member = guild.get_member(member_id)
                    if member:
                        try:
                            await member.kick(reason="[보안 시스템] 10분 이내 인증 미완료로 인한 자동 추방")
                        except:
                            pass
                    del self.unverified_users[member_id]

    @check_unverified_task.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    async def add_warning(self, member: discord.Member, reason: str):
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        now = time.time()

        if user_id in self.timeout_cooldown and now - self.timeout_cooldown[user_id] < 10:
            return

        if guild_id not in self.warn_data:
            self.warn_data[guild_id] = {}
        if user_id not in self.warn_data[guild_id]:
            self.warn_data[guild_id][user_id] = 0

        self.warn_data[guild_id][user_id] += 1
        current_warns = self.warn_data[guild_id][user_id]

        if current_warns >= 3:
            self.timeout_cooldown[user_id] = now
            self.warn_data[guild_id][user_id] = 0
            self.save_data(self.warn_filename, self.warn_data)
            try:
                await member.timeout(timedelta(minutes=5), reason="[보안 시스템] 경고 3회 누적으로 인한 5분 타임아웃")
                await self.send_log(member.guild, f"**[자동 타임아웃]** {member.mention} 님이 규칙 위반(경고 3회 누적)으로 5분간 채팅 제한(타임아웃) 처리되었으며, 경고가 초기화되었습니다.")
            except:
                pass
        else:
            self.save_data(self.warn_filename, self.warn_data)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        if message.author.guild_permissions.administrator:
            return

        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        now = time.time()
        user_id = message.author.id
        content = message.content

        self.spam_data[user_id] = [t for t in self.spam_data[user_id] if now - t < 3]
        self.spam_data[user_id].append(now)

        self.last_content[user_id] = [(c, t) for c, t in self.last_content[user_id] if now - t < 3]
        self.last_content[user_id].append((content, now))

        same_content_count = sum(1 for c, t in self.last_content[user_id] if c == content)

        if same_content_count >= 3 or len(self.spam_data[user_id]) >= 6:
            try:
                await message.delete()
                await self.add_warning(message.author, "채팅 도배(스팸) 시도")
                return
            except:
                pass

        if guild_id in self.media_data and channel_id in self.media_data[guild_id]:
            return

        has_link = "discord.gg/" in content or "https://discord.com/invite/" in content or "http://" in content or "https://" in content
        has_attachment = len(message.attachments) > 0

        if has_link or has_attachment:
            try:
                await message.delete()
                await self.add_warning(message.author, "허용되지 않은 채널에 링크 또는 미디어 업로드")
                return
            except:
                pass

        if len(message.mentions) >= 5 or len(message.role_mentions) >= 2:
            try:
                await message.delete()
                await self.add_warning(message.author, "과도한 멘션(멘션 테러) 시도")
                return
            except:
                pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            user = entry.user
            if user.bot:
                return
            
            member = channel.guild.get_member(user.id)
            if member and member.guild_permissions.administrator:
                return

            now = time.time()
            self.nuke_data[user.id] = [t for t in self.nuke_data[user.id] if now - t < 10]
            self.nuke_data[user.id].append(now)

            if len(self.nuke_data[user.id]) >= 3:
                try:
                    await channel.guild.ban(user, reason="[안티 누크] 대량 채널 삭제 테러 감지")
                    await self.send_log(channel.guild, f"🚨 **[안티 누크 경고]** 테러 행위가 감지되어 {user.mention} 님이 긴급 차단되었습니다!")
                except:
                    pass

    @discord.app_commands.command(name="media-channel", description="링크 및 미디어를 자유롭게 올릴 수 있는 허용 채널을 추가/제거합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def set_media_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        channel_id = str(channel.id)

        if guild_id not in self.media_data:
            self.media_data[guild_id] = []

        if channel_id in self.media_data[guild_id]:
            self.media_data[guild_id].remove(channel_id)
            self.save_data(self.media_filename, self.media_data)
            await interaction.response.send_message(f"❌ {channel.mention} 채널이 미디어 허용 채널에서 **제외**되었습니다.", ephemeral=True)
        else:
            self.media_data[guild_id].append(channel_id)
            self.save_data(self.media_filename, self.media_data)
            await interaction.response.send_message(f"✅ {channel.mention} 채널이 미디어 허용 채널로 **등록**되었습니다!", ephemeral=True)

    @discord.app_commands.command(name="내경고", description="자신에게 누적된 경고 횟수를 확인합니다.")
    async def my_warnings(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        warns = 0
        if guild_id in self.warn_data and user_id in self.warn_data[guild_id]:
            warns = self.warn_data[guild_id][user_id]

        await interaction.response.send_message(f"⚠️ 현재 {interaction.user.mention} 님의 누적 경고는 **{warns}회** 입니다.", ephemeral=True)

    warn_group = discord.app_commands.Group(name="경고", description="관리자 전용 경고 관리 명령어")

    @warn_group.command(name="채널", description="경고 및 보안 로그를 출력할 채널을 설정합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def set_warn_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)

        if guild_id not in self.log_data:
            self.log_data[guild_id] = {}

        self.log_data[guild_id]["channel_id"] = str(channel.id)
        self.save_data(self.log_filename, self.log_data)

        await interaction.response.send_message(f"✅ 앞으로 경고 및 보안 로그가 {channel.mention} 채널로 전송됩니다!", ephemeral=True)

    @warn_group.command(name="추가", description="특정 유저에게 경고를 추가합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def warn_add(self, interaction: discord.Interaction, member: discord.Member):
        await self.add_warning(member, "관리자에 의한 수동 경고 부여")
        guild_id = str(interaction.guild.id)
        current = self.warn_data[guild_id].get(str(member.id), 0)
        await interaction.response.send_message(f"✅ {member.mention} 님에게 경고를 1회 추가했습니다. (현재 경고: {current}회)", ephemeral=True)

    @warn_group.command(name="차감", description="특정 유저의 경고를 1회 차감합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def warn_sub(self, interaction: discord.Interaction, member: discord.Member):
        guild_id = str(interaction.guild.id)
        user_id = str(member.id)

        if guild_id not in self.warn_data or user_id not in self.warn_data[guild_id] or self.warn_data[guild_id][user_id] <= 0:
            await interaction.response.send_message(f"❌ {member.mention} 님은 누적된 경고가 없습니다.", ephemeral=True)
            return

        self.warn_data[guild_id][user_id] -= 1
        current = self.warn_data[guild_id][user_id]
        self.save_data(self.warn_filename, self.warn_data)

        await interaction.response.send_message(f"🔄 {member.mention} 님의 경고를 1회 차감했습니다. (현재 경고: {current}회)", ephemeral=True)
        await self.send_log(interaction.guild, f"🔄 **[경고 차감]** 관리자에 의해 {member.mention} 님의 경고가 차감되었습니다. (현재 경고: {current}회)")

    @discord.app_commands.command(name="lock", description="현재 채널을 잠급니다. (패닉 모드)")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def lockdown(self, interaction: discord.Interaction):
        channel = interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔒 현재 채널이 긴급 잠금(Lockdown)되었습니다.", ephemeral=False)

    @discord.app_commands.command(name="unlock", description="잠긴 채널을 해제합니다.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def unlock(self, interaction: discord.Interaction):
        channel = interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔓 채널 잠금이 해제되었습니다.", ephemeral=False)

async def setup(bot):
    await bot.add_cog(Security(bot))
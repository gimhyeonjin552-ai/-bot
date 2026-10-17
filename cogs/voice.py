import discord
from discord.ext import commands

ROOM_SETTINGS = {
    "소통방": 0,
    "게임방": 0,
    "솔로방": 1,
    "듀오방": 2,
    "트리오방": 3,
    "스쿼드방": 4,
    "오인큐방": 5,
    "afk 1": 1,
    "afk 2": 2,
    "afk 3": 3,
}


class Voice(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.Cog.listener()
  async def on_voice_state_update(self, member, before, after):
    if after.channel is not None and after.channel.name in ROOM_SETTINGS:
      guild = member.guild
      category = after.channel.category
      base_name = after.channel.name
      max_limit = ROOM_SETTINGS[base_name]

      channel_name = f"{base_name} - {member.display_name}"

      new_channel = await guild.create_voice_channel(
          name=channel_name, category=category, user_limit=max_limit
      )

      await member.move_to(new_channel)

    if before.channel is not None:
      for base_name in ROOM_SETTINGS.keys():
        if (
            f"{base_name} -" in before.channel.name
            and len(before.channel.members) == 0
        ):
          await before.channel.delete()
          break


async def setup(bot):
  await bot.add_cog(Voice(bot))
import aiohttp
import discord

from .types import DiscordConfig, SummarizedData


class Discord:
    def __init__(self, config: DiscordConfig):
        self.config = config

    async def send_message(self, message: SummarizedData) -> None:
        webhook_url = self.config["webhook_url"]
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(webhook_url, session=session)
            embed = discord.Embed(
                title=message["title"],
                url=message["link"],
                description=message["summarized_text"],
                color=0x009999,
            )
            embed.set_author(name=message["author"])
            embed.add_field(name="Tags", value=", ".join(message["tags"]), inline=False)
            image_url: str | None = message["image_url"]
            if isinstance(image_url, str):
                embed.set_image(url=image_url)
            await webhook.send(embed=embed)

    async def send_messages(self, messages: list[SummarizedData]) -> None:
        for message in messages:
            await self.send_message(message)

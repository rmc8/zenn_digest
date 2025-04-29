import aiohttp
import discord

from .types import DiscordConfig, SummarizedData


class Discord:
    """
    A class responsible for sending messages to a Discord channel via webhook.
    """

    def __init__(self, config: DiscordConfig):
        """
        Initializes the Discord client with the provided configuration.

        Args:
            config (DiscordConfig): Configuration dictionary containing webhook URL.
        """
        self.config = config

    async def send_message(self, message: SummarizedData) -> None:
        """
        Sends a single summarized message to the Discord webhook.

        Args:
            message (SummarizedData): The message data to send, including title, link, author, tags, image URL, and summarized text.
        """
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
            try:
                await webhook.send(embed=embed)
            except Exception as e:
                print(e)

    async def send_messages(self, messages: list[SummarizedData]) -> None:
        """
        Sends multiple summarized messages to the Discord webhook.

        Args:
            messages (list[SummarizedData]): List of message data to send.
        """
        for message in messages:
            await self.send_message(message)

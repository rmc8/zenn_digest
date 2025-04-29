from datetime import datetime
from typing import Literal, TypedDict

import polars as pl


# Config
class ZennConfig(TypedDict):
    feeds: list[str]


class QiitaConfig(TypedDict):
    feeds: list[str]


class LLMConfig(TypedDict):
    openai_model: str
    language: str
    temperature: float
    prompt: str


class DiscordConfig(TypedDict):
    webhook_url: str


class AppConfig(TypedDict):
    lookback_hours: int
    zenn: ZennConfig
    qiita: QiitaConfig
    llm: LLMConfig
    discord: DiscordConfig


# Data Structure
class FeedData(TypedDict):
    title: str
    link: str
    published: datetime
    source: Literal["zenn", "qiita"]


class ContentData(TypedDict):
    link: str
    tags: list[str]
    image_url: str | None
    content: str
    author: str


class ScrapedData(TypedDict):
    """
    Represents data for a tech feed entry including scraped content.
    Merges FeedData and ContentData.
    """

    title: str
    link: str
    published: datetime
    source: Literal["zenn", "qiita"]
    tags: list[str]
    image_url: str | None
    content: str
    author: str


class SummarizedData(TypedDict):
    title: str
    link: str
    published: datetime
    source: Literal["zenn", "qiita"]
    tags: list[str]
    image_url: str | None
    content: str
    author: str
    summarized_text: str


# Polars Schema

expected_schema: dict[str, pl.DataType] = {
    "title": pl.Utf8(),
    "link": pl.Utf8(),
    "published": pl.Datetime("us", "Asia/Tokyo"),
    "source": pl.Utf8(),
}

from datetime import datetime, timedelta

import feedparser
import polars as pl
import pytz

from .types import FeedData, ZennConfig, expected_schema

run_time = datetime.now(pytz.timezone("GMT"))


class ZennFeed:
    """
    ZennFeed class fetches articles from Zenn feeds and filters them within a specified lookback period.
    """

    @staticmethod
    def _convert_jst_dt_obj(dt_str: str) -> datetime:
        """
        Converts an ISO formatted date string to a timezone-aware datetime object in JST.

        Args:
            dt_str (str): ISO formatted date string.

        Returns:
            datetime: A timezone-aware datetime object in JST.
        """
        format_str: str = "%a, %d %b %Y %H:%M:%S %Z"
        naive_dt = datetime.strptime(dt_str, format_str)
        target_tz = pytz.timezone("GMT")
        return naive_dt.astimezone(target_tz)

    @staticmethod
    def _parse(url: str, lookback_hours: int) -> pl.DataFrame:
        """
        Parses the Zenn feed at the given URL and filters articles within the lookback period.

        Args:
            url (str): The feed URL.
            lookback_hours (int): The number of hours to look back.

        Returns:
            pl.DataFrame: DataFrame containing filtered articles.
        """
        data: list[FeedData] = []
        f = feedparser.parse(url)
        for entry in f.get("entries", []):
            feed_data: FeedData = {
                "title": entry.get("title"),
                "link": entry.get("link"),
                "published": ZennFeed._convert_jst_dt_obj(entry.get("published")),
                "source": "zenn",
            }
            data.append(feed_data)
        df = pl.DataFrame(data, schema=expected_schema)
        if df.is_empty():
            return df
        return df.filter(pl.col("published") > (run_time - timedelta(hours=lookback_hours)))

    @staticmethod
    def run(lookback_hours: int, config: ZennConfig) -> pl.DataFrame:
        """
        Retrieves articles from configured Zenn feeds within the lookback period and combines them.

        Args:
            lookback_hours (int): The number of hours to look back.
            config (ZennConfig): Configuration dictionary containing feed URLs.

        Returns:
            pl.DataFrame: DataFrame of retrieved articles.
        """
        df = pl.DataFrame([], schema=expected_schema)
        for feed_url in config["feeds"]:
            cdf = ZennFeed._parse(feed_url, lookback_hours)
            if cdf.is_empty():
                continue
            df = pl.concat([df, cdf])
        df = df.unique()
        return df

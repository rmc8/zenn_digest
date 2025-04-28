from datetime import datetime, timedelta

import feedparser
import polars as pl
import pytz

from .types import FeedData, ZennConfig, expected_schema

run_time = datetime.now(pytz.timezone("Asia/Tokyo"))


class ZennFeed:
    @staticmethod
    def _convert_jst_dt_obj(dt_str: str) -> datetime:
        format_str: str = "%a, %d %b %Y %H:%M:%S %Z"
        naive_dt = datetime.strptime(dt_str, format_str)
        target_tz = pytz.timezone("Asia/Tokyo")
        return naive_dt.astimezone(target_tz)

    @staticmethod
    def _parse(url: str, lookback_hours: int) -> pl.DataFrame:
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
        return df.filter(
            pl.col("published") > (run_time - timedelta(hours=lookback_hours))
        )

    @staticmethod
    def run(lookback_hours: int, config: ZennConfig) -> pl.DataFrame:
        df = pl.DataFrame([], schema=expected_schema)
        for feed_url in config["feeds"]:
            cdf = ZennFeed._parse(feed_url, lookback_hours)
            if cdf.is_empty():
                continue
            df = pl.concat([df, cdf])
        df = df.unique()
        return df

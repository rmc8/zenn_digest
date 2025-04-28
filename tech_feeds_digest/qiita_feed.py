from datetime import datetime, timedelta

import feedparser
import polars as pl
import pytz

from .types import FeedData, QiitaConfig, expected_schema

run_time = datetime.now(pytz.timezone("Asia/Tokyo"))


class QiitaFeed:
    @staticmethod
    def _convert_jst_dt_obj(dt_str: str) -> datetime:
        dt_obj = datetime.fromisoformat(dt_str)
        target_tz = pytz.timezone("Asia/Tokyo")
        return dt_obj.astimezone(target_tz)

    @staticmethod
    def _parse(url: str, lookback_hours: int) -> pl.DataFrame:
        data: list[FeedData] = []
        f = feedparser.parse(url)
        for entry in f.get("entries", []):
            feed_data: FeedData = {
                "title": entry.get("title"),
                "link": entry.get("link"),
                "published": QiitaFeed._convert_jst_dt_obj(entry.get("published")),
                "source": "qiita",
            }
            data.append(feed_data)
        df = pl.DataFrame(data, schema=expected_schema)
        if df.is_empty():
            return df
        return df.filter(pl.col("published") > (run_time - timedelta(hours=lookback_hours)))

    @staticmethod
    def run(lookback_hours: int, config: QiitaConfig) -> pl.DataFrame:
        df = pl.DataFrame([], schema=expected_schema)
        for feed_url in config["feeds"]:
            cdf = QiitaFeed._parse(feed_url, lookback_hours)
            if cdf.is_empty():
                continue
            df = pl.concat([df, cdf])
        df = df.unique()
        return df

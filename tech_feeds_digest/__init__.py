import sys
from logging import getLogger

import polars as pl

from .qiita_feed import QiitaFeed
from .scraper import Scraper
from .summarizer import Summarizer
from .types import AppConfig, FeedData, ScrapedData, SummarizedData
from .zenn_feed import ZennFeed


class TechFeedsDigest:
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = getLogger(__name__)

    def _drop_duplicates_by_title(self, df: pl.DataFrame) -> pl.DataFrame:
        if df.is_empty():
            return df
        df = df.sort(["title", "published"], descending=[False, True])
        return df.unique(subset=["title"], keep="first")

    def _get_feed_data(self):
        lookback_hours = self.config["lookback_hours"]
        zf_df = ZennFeed.run(lookback_hours, self.config["zenn"])
        qf_df = QiitaFeed.run(lookback_hours, self.config["qiita"])
        combined_df = pl.concat([zf_df, qf_df])
        fil_dif = self._drop_duplicates_by_title(combined_df)
        self.logger.info("Total entries: %s", fil_dif.shape[0])
        return fil_dif

    def _check_no_new_entry(self, df: pl.DataFrame) -> None:
        if df.is_empty():
            self.logger.info("No new entries found. Exiting...")
            sys.exit(0)

    def run(self):
        self.logger.info("Starting TechFeedsDigest")
        feed_df = self._get_feed_data()
        # Check if there are new entries
        self._check_no_new_entry(feed_df)
        # Scraping
        self.logger.info("Scraping data...")
        feed_data_list: list[FeedData] = feed_df.to_dicts()
        scraped_data_list: list[ScrapedData] = Scraper.run(feed_data_list)
        # Summarizing
        self.logger.info("Summarizing data...")
        s = Summarizer(self.config["llm"])
        summarized_data_list: list[SummarizedData] = s.run(
            scraped_data_list=scraped_data_list,  # type:ignore
        )
        print(summarized_data_list[0]["summarized_text"])

import sys
from logging import getLogger

import polars as pl

from .discord import Discord
from .qiita_feed import QiitaFeed
from .scraper import Scraper
from .summarizer import Summarizer
from .types import AppConfig, FeedData, ScrapedData, SummarizedData
from .zenn_feed import ZennFeed


class TechFeedsDigest:
    """
    Main class for orchestrating the fetching, processing, and notification of tech feed data.
    """

    def __init__(self, config: AppConfig):
        """
        Initializes the main class with the provided configuration.
        :param config: Application configuration.
        """
        self.config = config
        self.logger = getLogger(__name__)

    def _drop_duplicates_by_title(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Drops duplicate entries based on the 'title' column, keeping the latest.
        :param df: DataFrame to process.
        :return: DataFrame with duplicates removed.
        """
        if df.is_empty():
            return df
        df = df.sort(["title", "published"], descending=[False, True])
        return df.unique(subset=["title"], keep="first")

    def _get_feed_data(self):
        """
        Retrieves and combines feed data from Zenn and Qiita, removing duplicates.
        :return: DataFrame with combined feed data.
        """
        lookback_hours = self.config["lookback_hours"]
        zf_df = ZennFeed.run(lookback_hours, self.config["zenn"])
        qf_df = QiitaFeed.run(lookback_hours, self.config["qiita"])
        combined_df = pl.concat([zf_df, qf_df])
        fil_dif = self._drop_duplicates_by_title(combined_df)
        self.logger.info("Total entries: %s", fil_dif.shape[0])
        return fil_dif

    def _check_no_new_entry(self, df: pl.DataFrame) -> None:
        """
        Checks if there are no new entries and exits if so.
        :param df: DataFrame to check.
        """
        if df.is_empty():
            self.logger.info("No new entries found. Exiting...")
            sys.exit(0)

    async def run(self):
        """
        Main execution method: fetches, processes, summarizes, and sends notifications.
        """
        self.logger.info("Starting TechFeedsDigest")
        feed_df = self._get_feed_data()
        self._check_no_new_entry(feed_df)
        self.logger.info("Scraping data...")
        feed_data_list: list[FeedData] = feed_df.to_dicts()
        scraped_data_list: list[ScrapedData] = Scraper.run(feed_data_list)
        self.logger.info("Summarizing data...")
        s = Summarizer(self.config["llm"])
        summarized_data_list: list[SummarizedData] = s.run(
            scraped_data_list=scraped_data_list,  # type:ignore
        )
        self.logger.info("Sending message...")
        d = Discord(self.config["discord"])
        await d.send_messages(summarized_data_list)
        self.logger.info("TechFeedsDigest finished!")

import polars as pl

from .qiita_feed import QiitaFeed
from .types import AppConfig
from .zenn_feed import ZennFeed


class DigestClient:
    def __init__(self, config: AppConfig):
        self.config = config

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
        return fil_dif

    def run(self):
        feed_df = self._get_feed_data()
        print(feed_df)

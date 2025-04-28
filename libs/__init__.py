from .types import AppConfig
from .zenn_feed import ZennFeed


class DigestClient:
    def __init__(self, config: AppConfig):
        self.config = config

    def run(self):
        # Zenn
        lookback_hours = self.config["lookback_hours"]
        zf_df = ZennFeed.run(lookback_hours, self.config["zenn"])
        print(zf_df)

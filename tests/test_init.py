import pathlib
import sys

import polars as pl

sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())


from tech_feeds_digest import TechFeedsDigest
from tech_feeds_digest.types import AppConfig


def test_instantiate_tech_feeds_digest():
    config: AppConfig = {
        "lookback_hours": 24,
        "zenn": {"feeds": []},
        "qiita": {"feeds": []},
        "llm": {
            "openai_model": "",
            "language": "",
            "temperature": 0.0,
            "prompt": "",
        },
        "discord": {"webhook_url": ""},
    }
    instance = TechFeedsDigest(config=config)
    assert isinstance(instance, TechFeedsDigest)


def test_drop_duplicates_method():
    config: AppConfig = {
        "lookback_hours": 24,
        "zenn": {"feeds": []},
        "qiita": {"feeds": []},
        "llm": {
            "openai_model": "",
            "language": "",
            "temperature": 0.0,
            "prompt": "",
        },
        "discord": {"webhook_url": ""},
    }
    instance = TechFeedsDigest(config=config)
    df = pl.DataFrame({"title": ["A", "A"], "published": [1, 2]})
    result_df = instance._drop_duplicates_by_title(df)
    assert len(result_df) <= 1


def test_get_feed_data_method_returns_dataframe():
    config: AppConfig = {
        "lookback_hours": 24,
        "zenn": {"feeds": []},
        "qiita": {"feeds": []},
        "llm": {
            "openai_model": "",
            "language": "",
            "temperature": 0.0,
            "prompt": "",
        },
        "discord": {"webhook_url": ""},
    }
    instance = TechFeedsDigest(config=config)
    df = instance._get_feed_data()
    assert hasattr(df, "filter")

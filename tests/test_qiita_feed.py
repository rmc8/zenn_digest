import pathlib
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import pytz

sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())

from tech_feeds_digest.qiita_feed import QiitaFeed
from tech_feeds_digest.types import QiitaConfig


@pytest.fixture
def mock_feed():
    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    recent_time_str = now.isoformat()
    older_time_str = (now - timedelta(hours=25)).isoformat()
    return {
        "entries": [
            {
                "title": "Recent Entry",
                "link": "http://example.com/recent",
                "published": recent_time_str,
            },
            {
                "title": "Old Entry",
                "link": "http://example.com/old",
                "published": older_time_str,
            },
        ]
    }


def test_convert_jst_dt_obj_valid():
    dt_str = datetime.now().isoformat()
    result = QiitaFeed._convert_jst_dt_obj(dt_str)
    assert isinstance(result, datetime)
    assert result.tzinfo is not None


def test_convert_jst_dt_obj_invalid():
    with pytest.raises(ValueError):
        QiitaFeed._convert_jst_dt_obj("invalid date")


@patch("feedparser.parse")
def test_parse_filters_by_time(mock_parse, mock_feed):
    mock_parse.return_value = mock_feed
    result_df = QiitaFeed._parse("http://dummy", lookback_hours=24)
    titles = result_df["title"].to_list()
    assert "Recent Entry" in titles
    assert "Old Entry" not in titles


@patch("feedparser.parse")
def test_run_aggregates_feeds(mock_parse):
    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    recent_time_str = now.isoformat()
    old_time_str = (now - timedelta(hours=25)).isoformat()
    mock_parse.side_effect = [
        {
            "entries": [
                {
                    "title": "Recent Entry",
                    "link": "http://example.com/recent",
                    "published": recent_time_str,
                }
            ]
        },
        {
            "entries": [
                {
                    "title": "Old Entry",
                    "link": "http://example.com/old",
                    "published": old_time_str,
                }
            ]
        },
    ]
    config: QiitaConfig = {"feeds": ["feed1", "feed2"]}
    df = QiitaFeed.run(lookback_hours=24, config=config)
    titles = df["title"].to_list()
    assert "Recent Entry" in titles
    assert "Old Entry" not in titles


def test_run_no_feeds():
    df = QiitaFeed.run(lookback_hours=24, config={"feeds": []})
    assert df.is_empty()

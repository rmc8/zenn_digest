import pathlib
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import pytz

sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())


from libs.types import ZennConfig
from libs.zenn_feed import ZennFeed


@pytest.fixture
def mock_feed():
    now = datetime.now(pytz.timezone("GMT"))
    recent_time_str = now.strftime("%a, %d %b %Y %H:%M:%S %Z")
    older_time_str = (now - timedelta(hours=25)).strftime("%a, %d %b %Y %H:%M:%S %Z")
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
    dt_str = "Tue, 24 Oct 2023 15:00:00 GMT"
    result = ZennFeed._convert_jst_dt_obj(dt_str)
    assert isinstance(result, datetime)
    assert result.year == 2023


def test_convert_jst_dt_obj_invalid():
    with pytest.raises(ValueError):
        ZennFeed._convert_jst_dt_obj("invalid date")


@patch("libs.zenn_feed.feedparser.parse")
def test_parse_filters_by_time(mock_parse, mock_feed):
    mock_parse.return_value = mock_feed
    result_df = ZennFeed._parse("http://dummy", lookback_hours=24)
    titles = result_df["title"].to_list()
    assert "Recent Entry" in titles
    assert "Old Entry" not in titles


@patch("libs.zenn_feed.feedparser.parse")
def test_run_aggregates_feeds(mock_parse):
    now = datetime.now(pytz.timezone("GMT"))
    recent_time_str = now.strftime("%a, %d %b %Y %H:%M:%S %Z")
    old_time_str = (now - timedelta(hours=25)).strftime("%a, %d %b %Y %H:%M:%S %Z")
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
    config: ZennConfig = {"feeds": ["feed1", "feed2"]}
    df = ZennFeed.run(lookback_hours=24, config=config)
    titles = df["title"].to_list()
    assert "Recent Entry" in titles
    assert "Old Entry" not in titles


def test_run_no_feeds():
    df = ZennFeed.run(lookback_hours=24, config={"feeds": []})
    assert df.is_empty()

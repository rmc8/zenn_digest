import pathlib
import sys
from datetime import datetime
from unittest.mock import patch

import httpx
import pytest

sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())

from tech_feeds_digest import scraper
from tech_feeds_digest.types import FeedData


@pytest.fixture
def sample_feed_data():
    return [
        {
            "title": "Qiita Article",
            "link": "https://qiita.com/sample",
            "source": "qiita",
        },
        {
            "title": "Zenn Article",
            "link": "https://zenn.dev/sample",
            "source": "zenn",
        },
        {
            "title": "Invalid Source",
            "link": "https://example.com",
            "source": "others",
        },
        {
            "title": "Missing Link",
            "source": "qiita",
        },
        {
            "title": "Invalid Link",
            "link": None,
            "source": "zenn",
        },
    ]


def test_get_data_qiita_and_zenn(sample_feed_data):
    mock_qiita = {
        "link": sample_feed_data[0]["link"],
        "tags": ["tag1"],
        "content": "content",
        "author": "author",
    }
    mock_zenn = {
        "link": sample_feed_data[1]["link"],
        "tags": ["tagA"],
        "content": "zenn content",
        "author": "Zenn Author",
    }

    with (
        patch.object(scraper.Scraper, "_get_qiita_data", return_value=mock_qiita),
        patch.object(scraper.Scraper, "_get_zenn_data", return_value=mock_zenn),
    ):
        # _get_dataが正しい返り値を返すことを期待
        result_qiita = scraper.Scraper._get_data(sample_feed_data[0])
        result_zenn = scraper.Scraper._get_data(sample_feed_data[1])

        assert result_qiita["link"] == sample_feed_data[0]["link"]
        assert result_qiita["tags"] == ["tag1"]
        assert result_qiita["content"] == "content"
        assert result_qiita["author"] == "author"

        assert result_zenn["link"] == sample_feed_data[1]["link"]
        assert "tagA" in result_zenn["tags"]
        assert "zenn content" in result_zenn["content"]
        assert result_zenn["author"] == "Zenn Author"


def test_get_data_invalid_source_raises(monkeypatch):
    published = datetime.now()
    feed: FeedData = {
        "title": "Invalid",
        "source": "unknown",  # type:ignore
        "link": "https://example.com",
        "published": published,
    }
    with pytest.raises(ValueError):
        scraper.Scraper._get_data(feed)


def test_get_data_missing_link_raises(monkeypatch):
    feed: FeedData = {"title": "Missing Link", "source": "qiita"}  # type:ignore
    # _get_data should log error and raise if link invalid
    with pytest.raises(ValueError):
        scraper.Scraper._get_data(feed)


def test_run_multiple_entries(monkeypatch):
    # すべてのfeed_dataを処理
    mock_content = {"link": "link", "tags": [], "content": "", "author": ""}

    with patch.object(scraper.Scraper, "_get_data", return_value=mock_content) as mock_get_data:
        feed_list: list[FeedData] = [
            {"title": "t1", "link": "l1", "source": "qiita"},  # type:ignore
            {"title": "t2", "link": "l2", "source": "zenn"},  # type:ignore
            {"title": "t3", "link": "l3", "source": "qiita"},  # type:ignore
        ]
        results = scraper.Scraper.run(feed_list)
        # すべての入力に対して結果が得られる
        assert len(results) == len(feed_list)
        # _get_data呼び出しが同じ数だけ
        assert mock_get_data.call_count == len(feed_list)
        for record in results:
            assert "link" in record


def test_http_status_error_skips(monkeypatch):
    # HTTPStatusErrorを発生させる
    def mock_httpx_get(*args, **kwargs):
        raise httpx.HTTPStatusError(
            "bad status",
            request=None,  # type:ignore
            response=None,  # type:ignore
        )

    monkeypatch.setattr(scraper.httpx, "get", mock_httpx_get)

    feed_list: list[FeedData] = [
        {"title": "t", "link": "l", "source": "qiita"}  # type:ignore
    ]
    result = scraper.Scraper.run(feed_list)
    assert result == []

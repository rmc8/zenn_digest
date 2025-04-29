from logging import getLogger

import frontmatter
import httpx
from bs4 import BeautifulSoup

from .types import ContentData, FeedData, ScrapedData

logger = getLogger(__name__)


class Scraper:
    @staticmethod
    def _http_get(link: str) -> BeautifulSoup:
        res = httpx.get(
            link,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
            },
        )
        res.raise_for_status()
        return BeautifulSoup(res.text, "lxml")

    @staticmethod
    def _get_qiita_data(link: str) -> ContentData:
        bs = Scraper._http_get(f"{link}.md")
        md = bs.get_text(strip=True)
        f = frontmatter.loads(md)
        meta = f.metadata
        return {
            "link": link,
            "tags": meta["tags"].split(),
            "content": f.content,
            "author": meta["author"],
        }

    @staticmethod
    def _get_zenn_data(link: str) -> ContentData:
        bs = Scraper._http_get(link)
        # Tags
        tag_elms = bs.select("div.View_topics__2sHkl a.View_topicLink__jdtX_")
        tags: list[str] = [tag_elm.get_text(strip=True) for tag_elm in tag_elms]
        # Content
        content_elm = bs.select_one("div.znc.BodyContent_anchorToHeadings__uGxNv")
        content = content_elm.get_text(strip=True) if content_elm is not None else ""
        # Author
        author_elm = bs.select_one("a.ProfileCard_displayName__gRUeY")
        author = (
            author_elm.get_text(strip=True)
            if author_elm is not None
            else "Unknown Author"
        )
        # Data
        return {
            "link": link,
            "tags": tags,
            "content": content,
            "author": author,
        }

    @staticmethod
    def _get_data(feed_data: FeedData) -> ContentData:
        source: str | None = feed_data.get("source")
        if isinstance(source, str) and source in ["zenn", "qiita"]:
            link: str | None = feed_data.get("link")
            if isinstance(link, str):
                if source == "zenn":
                    rz: ContentData = Scraper._get_zenn_data(link)
                    return rz
                elif source == "qiita":
                    rq: ContentData = Scraper._get_qiita_data(link)
                    return rq
            else:
                logger.error(
                    f"Skipping entry due to missing/invalid link for source '{source}': {feed_data.get('title', 'Unknown Title')}"
                )
        else:
            logger.error(f"Skipping entry due to invalid/missing source: {source}")
        raise ValueError("Invalid feed data")

    @staticmethod
    def run(feed_data_list: list[FeedData]) -> list[ScrapedData]:
        data = []
        for feed_data in feed_data_list:
            try:
                content_data: ContentData = Scraper._get_data(feed_data)
                record: ScrapedData = {**feed_data, **content_data}
                data.append(record)
                if len(data) >= 5:
                    break
            except httpx.HTTPStatusError as e:
                logger.error("HTTPStatusError: %s", e)
                continue
        return data

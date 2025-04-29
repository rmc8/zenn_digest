from logging import getLogger

import frontmatter
import httpx
import yaml
from bs4 import BeautifulSoup

from .types import ContentData, FeedData, ScrapedData

logger = getLogger(__name__)


class Scraper:
    """
    Scraper class for fetching and extracting article data from web pages.
    """

    @staticmethod
    def _http_get(link: str) -> BeautifulSoup:
        """
        Sends an HTTP GET request to the specified URL and returns a BeautifulSoup object.

        Args:
            link (str): The URL to fetch.

        Returns:
            BeautifulSoup: Parsed HTML content of the response.
        """
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
        """
        Extracts article data from a Qiita article page.

        Args:
            link (str): Qiita article URL.

        Returns:
            ContentData: Extracted article information including link, tags, image URL, content, and author.
        """
        bs = Scraper._http_get(f"{link}.md")
        md = bs.get_text(strip=True)
        f = frontmatter.loads(md)
        meta = f.metadata
        # Get image URL
        soup = Scraper._http_get(link)
        og_image_elm = soup.select_one("meta[property='og:image']")
        image_url: str | None = (
            str(og_image_elm["content"]) if og_image_elm is not None else None
        )
        # Return data
        return {
            "link": link,
            "tags": meta["tags"].split(),
            "image_url": image_url,
            "content": f.content,
            "author": meta["author"],
        }

    @staticmethod
    def _get_zenn_data(link: str) -> ContentData:
        """
        Extracts article data from a Zenn article page.

        Args:
            link (str): Zenn article URL.

        Returns:
            ContentData: Extracted article information including link, tags, image URL, content, and author.
        """
        bs = Scraper._http_get(link)
        # Extract tags
        tag_elms = bs.select("div.View_topics__2sHkl a.View_topicLink__jdtX_")
        tags: list[str] = [tag_elm.get_text(strip=True) for tag_elm in tag_elms]
        # Extract content
        content_elm = bs.select_one("div.znc.BodyContent_anchorToHeadings__uGxNv")
        content = content_elm.get_text(strip=True) if content_elm is not None else ""
        # Extract author
        author_elm = bs.select_one("a.ProfileCard_displayName__gRUeY")
        author = (
            author_elm.get_text(strip=True)
            if author_elm is not None
            else "Unknown Author"
        )
        # Get image URL
        og_image_elm = bs.select_one("meta[property='og:image']")
        image_url: str | None = (
            str(og_image_elm["content"]) if og_image_elm is not None else None
        )
        # Return data
        return {
            "link": link,
            "tags": tags,
            "image_url": image_url,
            "content": content,
            "author": author,
        }

    @staticmethod
    def _get_data(feed_data: FeedData) -> ContentData:
        """
        Extracts content data based on the source type from feed data.

        Args:
            feed_data (FeedData): The feed data containing source and link.

        Returns:
            ContentData: Extracted content data.
        """
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
        """
        Processes a list of feed data entries and returns a list of scraped data.

        Args:
            feed_data_list (list[FeedData]): List of feed data entries.

        Returns:
            list[ScrapedData]: List of scraped data records.
        """
        data: list[ScrapedData] = []
        for feed_data in feed_data_list:
            try:
                content_data: ContentData = Scraper._get_data(feed_data)
                record: ScrapedData = {**feed_data, **content_data}
                data.append(record)
            except httpx.HTTPStatusError as e:
                logger.error("HTTPStatusError: %s", e)
                continue
            except yaml.parser.ParserError as e:
                logger.error("ParserError: %s", e)
        return data

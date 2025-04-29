import asyncio
import tomllib
from pathlib import Path
from typing import cast

from tech_feeds_digest import TechFeedsDigest
from tech_feeds_digest.typess import AppConfig

THIS_DIR = Path(__file__).parent
CONFIG_PATH = THIS_DIR / "config.toml"


def get_config(path: Path) -> AppConfig:
    """
    Reads the configuration file and returns the configuration object.

    Args:
        path (Path): Path to the configuration file.

    Returns:
        AppConfig: The loaded configuration object.
    """
    with path.open("rb") as f:
        conf = tomllib.load(f)
        return cast(AppConfig, conf)


async def main():
    """
    Main asynchronous function to initialize and run the TechFeedsDigest process.
    """
    config = get_config(CONFIG_PATH)
    client = TechFeedsDigest(config)
    await client.run()


if __name__ == "__main__":
    """
    Entry point of the script. Executes the main async function.
    """
    asyncio.run(main())

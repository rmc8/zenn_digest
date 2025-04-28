import tomllib
from pathlib import Path

from tech_feeds_digest import TechFeedsDigest
from tech_feeds_digest.types import AppConfig

THIS_DIR = Path(__file__).parent
CONFIG_PATH = THIS_DIR / "config.toml"


def get_config(path: Path) -> AppConfig:
    with path.open("rb") as f:
        return tomllib.load(f)


def main():
    config = get_config(CONFIG_PATH)
    client = TechFeedsDigest(config)
    client.run()


if __name__ == "__main__":
    main()

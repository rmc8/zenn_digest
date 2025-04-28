import tomllib
from pathlib import Path

from libs import DigestClient
from libs.types import AppConfig

THIS_DIR = Path(__file__).parent
CONFIG_PATH = THIS_DIR / "config.toml"


def get_config(path: Path) -> AppConfig:
    with path.open("rb") as f:
        return tomllib.load(f)


def main():
    config = get_config(CONFIG_PATH)
    client = DigestClient(config)
    client.run()


if __name__ == "__main__":
    main()

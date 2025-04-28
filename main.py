import tomllib
from pathlib import Path

THIS_DIR = Path(__file__).parent
CONFIG_PATH = THIS_DIR / "config.toml"


def get_config(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def main():
    config = get_config(CONFIG_PATH)
    print(config)


if __name__ == "__main__":
    main()

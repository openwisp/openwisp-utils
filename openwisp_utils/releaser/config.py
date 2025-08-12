import sys

import tomli


def load_config():
    try:
        with open("releaser.toml", "rb") as f:
            return tomli.load(f)
    except FileNotFoundError:
        print("Error: releaser.toml not found. Please create it.", file=sys.stderr)
        sys.exit(1)
    except tomli.TOMLDecodeError as e:
        print(f"Error decoding releaser.toml: {e}", file=sys.stderr)
        sys.exit(1)

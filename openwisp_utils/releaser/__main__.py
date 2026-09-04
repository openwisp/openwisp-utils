import argparse
import subprocess
import sys

import requests
from openwisp_utils.releaser.release import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", choices=["resume"])
    parser.add_argument("pr_url", nargs="?")
    args = parser.parse_args()
    if args.command == "resume" and not args.pr_url:
        parser.error("resume requires the release pull request URL")
    if args.command is None and args.pr_url:
        parser.error("a pull request URL can only be used with the resume command")
    try:
        main(resume_pr_url=args.pr_url)
    except KeyboardInterrupt:
        print("\n\n❌ Release process terminated by user.")
        sys.exit(1)
    except (
        subprocess.CalledProcessError,
        requests.RequestException,
        RuntimeError,
        FileNotFoundError,
    ) as e:
        print(f"\n❌ An error occurred: {e}", file=sys.stderr)
        if isinstance(e, subprocess.CalledProcessError):
            print(f"Error Details: {e.stderr}", file=sys.stderr)
        sys.exit(1)

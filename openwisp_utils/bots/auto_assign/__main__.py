#!/usr/bin/env python3

import sys


def main():
    """Entry point for all bot functionality"""
    if len(sys.argv) < 2:
        print("Usage: python -m openwisp_utils.bots.auto_assign <bot_type> [args...]")
        print("Available bot types: issue_assignment, stale_pr, pr_reopen")
        return 1

    bot_type = sys.argv[1]

    try:
        if bot_type == "issue_assignment":
            from .issue_assignment_bot import main as issue_main

            sys.argv = [sys.argv[0]] + sys.argv[2:]
            issue_main()
        elif bot_type == "stale_pr":
            from .stale_pr_bot import main as stale_main

            stale_main()
        elif bot_type == "pr_reopen":
            from .pr_reopen_bot import main as pr_main

            sys.argv = [sys.argv[0]] + sys.argv[2:]
            pr_main()
        else:
            print(f"Unknown bot type: {bot_type}")
            print("Available bot types: issue_assignment, stale_pr, pr_reopen")
            return 1

        return 0
    except Exception as e:
        print(f"Error running {bot_type} bot: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

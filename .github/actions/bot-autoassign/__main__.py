import sys


def main():
    """Entry point for all bot functionality"""
    if len(sys.argv) < 2:
        print(
            "Usage: python __main__.py <bot_type> [args...]\n"
            "Available bot types: issue_assignment, stale_pr, pr_reopen"
        )
        return 1

    bot_type = sys.argv[1]

    try:
        # Strip bot_type from sys.argv for all sub-bots
        sys.argv = [sys.argv[0]] + sys.argv[2:]

        if bot_type == "issue_assignment":
            from issue_assignment_bot import main as issue_main

            return issue_main() or 0
        elif bot_type == "stale_pr":
            from stale_pr_bot import main as stale_main

            return stale_main() or 0
        elif bot_type == "pr_reopen":
            from pr_reopen_bot import main as pr_main

            return pr_main() or 0
        else:
            print(f"Unknown bot type: {bot_type}")
            print("Available bot types: " "issue_assignment, stale_pr, pr_reopen")
            return 1
    except Exception as e:
        print(f"Error running {bot_type} bot: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

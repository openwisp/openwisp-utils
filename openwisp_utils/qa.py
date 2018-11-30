"""
This file contains functions that are required by
multiple openwisp repositories for testing
during continuous integration
"""
import argparse
import os
import re


def _parse_args():
    """
    Parse and return CLI arguments
    """
    parser = argparse.ArgumentParser(description="Ensures migration files "
                                     "created have a descriptive name. If "
                                     "default name pattern is found, "
                                     "raise exception!")
    parser.add_argument("--migration-path",
                        help="Path to `migrations/` folder")
    parser.add_argument("--migrations-to-ignore",
                        type=int,
                        help="Number of migrations after which checking of "
                        "migration file names should begin, say, if checking "
                        "needs to start after `0003_auto_20150410_3242.py` "
                        "value should be `3`")
    return parser.parse_args()


def check_migration_name():
    """
    Ensure migration files created have a descriptive
    name; if default name pattern is found, raise exception
    """
    args = _parse_args()
    if not args.migration_path:
        raise Exception("CLI argument `migration-path` is required "
                        "but not found")
    if args.migrations_to_ignore is None:
        args.migrations_to_ignore = 0
    # QA Check
    migrations_set = set()
    migrations = os.listdir(args.migration_path)
    for migration in migrations:
        if (re.match(r"^[0-9]{4}_auto_[0-9]{2}", migration) and
                int(migration[:4]) > args.migrations_to_ignore):
            migrations_set.add(migration)
    if bool(migrations_set):
        migrations = list(migrations_set)
        file_ = 'file' if len(migrations) < 2 else 'files'
        raise Exception("Migration %s %s in directory %s must "
                        "be renamed to something more descriptive."
                        % (file_, ', '.join(migrations), args.migration_path))


def _commit_check_args():
    """
    Parse and return CLI arguments
    """
    parser = argparse.ArgumentParser(description="Ensures the commit message "
                                     "matches the OpenWISP commit guidelines.")

    parser.add_argument("--message",
                        help="Commit message")
    return parser.parse_args()


def check_commit_message():
    args = _commit_check_args()
    if not args.message:
        raise Exception("CLI argument `message` is required "
                        "but not found")
    else:
        short_desc = args.message.split("\n")[0]
        if len(args.message.split("\n")) > 1:
            long_desc = args.message.split("\n")[1:]
    errors = []
    # Check dot in end of the first line
    if short_desc[len(short_desc.strip()) - 1].strip() == '.':
        errors.append("Do not add a final dot at the end of the first line.")
    # Check prefix
    prefix = re.match(r'\[(.*?)\]', short_desc)
    if not prefix:
        errors.append(
            "Add prefix in beginning of the commit. "
            "Example: [module/file/feature]"
        )
    else:
        # Check capital after prefix
        commit_message_first = short_desc.replace(prefix.group(), '').strip()
        if not commit_message_first[0].isupper():
            errors.append("No capital letter after prefix")
    # Check blank line before first line and second line
    if 'long_desc' in locals():
        if len(args.message.split("\n")) > 1:
            if args.message.split("\n")[1] != '':
                errors.append("No blank line before first "
                              "line and second line")
        # Mentions an issues without closing it
        message = ' '.join(long_desc)
        # Check issues in  long desc
        long_desc_location = re.search(r'\#(\d+)', message)
        if long_desc_location:
            # message_check will return array of number issues when success
            message_check = _check_word(message)
            # Checked is variable type is array
            if(not _is_array(message_check)):
                errors.append(message_check)
            # Check hastag if mention issues
            checked = 0
            for check in message_check:
                # Checked is one of issues in short messages
                short_desc_hastag = re.search(
                    r'\#' +
                    check.replace("#", ""),
                    short_desc
                )
                if short_desc_hastag:
                    checked = checked + 1
            # If not mentioned issues at least 1 issues
            if checked == 0:
                errors.append("No mention issues in the short description")
        # Check issues in short desc
        short_desc_location = re.search(r'\#(\d+)', short_desc)
        if short_desc_location:
            # Get all issues in long description
            long_desc_issues = _check_word(message)
            if not _is_array(long_desc_issues):
                errors.append("No mention issues in the long description")
            checked = 0
            # Foreach all issues
            for issues in long_desc_issues:
                # Check is issues in short description
                long_desc_hastag = re.search(
                    r'\#' +
                    issues.replace("#", ""),
                    short_desc)
                if long_desc_hastag:
                    checked = checked + 1
            if checked == 0:
                errors.append("No mention issues in the long description")
    # Check is error
    if len(errors) == 0:
        body = "All check done, no errors."
    else:
        body = "You have errors with commit message: \n"
        for e in errors:
            body += "- " + e + "\n"
    if len(errors) > 0:
        raise Exception(body)
    else:
        print(body)


def _is_array(var):
    return isinstance(var, (list, tuple))


def _check_word(message):
    parts = message.split(' ')
    return_data = []
    loc = []
    i = 0
    # Search hastag from parts
    for part in parts:
        hastag = re.search(r'\#(\d+)', part)
        if hastag:
            loc.append(i)
        i = i + 1
    # Check for num hastag with allowed words
    num = 0
    for location in loc:
        word = parts[location - 1]
        return_data.append(parts[location])
        if(location > 2):
            word2 = str(parts[location - 2] + " " + parts[location - 1])
            allowed_words2 = [
                'related to',
                'refers to',
            ]
            if((word2.lower() in allowed_words2)):
                num = num + 1
                continue
        allowed_words = [
            'fix',
            'fixes',
            'close',
            'closes',
            'ref',
            'rel'
        ]
        if (word.lower() in allowed_words):
            num = num + 1
    if num != len(loc):
        return "Mentions an issues without closing it"
    return return_data

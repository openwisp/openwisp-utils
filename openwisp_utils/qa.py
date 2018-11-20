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
    Parse and return CLI arguements
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
        raise Exception("CLI arguement `migration-path` is required "
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

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
    parser.add_argument('--no-migration-name', nargs='?', const=True,
                        help="Skip check: migration files have a "
                        "descriptive name.")
    parser.add_argument("--migration-path",
                        help="Path to `migrations/` folder")
    parser.add_argument("--migrations-to-ignore",
                        type=int,
                        help="Number of migrations after which checking of "
                        "migration file names should begin, say, if checking "
                        "needs to start after `0003_auto_20150410_3242.py` "
                        "value will be `3`")
    return parser.parse_args()


def check_migration_name(migration_path, migrations_to_ignore=0):
    """
    Ensure migration files created have a descriptive
    name; if default name pattern is found, raise exception
    Arguements:
      - migration_path: path to `migrations/` folder
      - migrations_to_ignore: number of migrations after
        which checking should begin, say, if checking needs to
        start after `0003_auto_20150410_3242.py` value will be `3`
    """
    migrations_set = set()
    migrations = os.listdir(migration_path)
    for migration in migrations:
        if (re.match(r"^[0-9]{4}_auto_[0-9]{8}", migration) and
                int(migration[:4]) > migrations_to_ignore):
            migrations_set.add(migration)

    if bool(migrations_set):
        raise Exception("Migration files %s in folder %s need to "
                        "be renamed to something more descriptive!"
                        % (str(migrations_set), migration_path))


def initialize():
    """
    Get & check if CLI arguements are passed
    correctly and call CI Tasks
    Intented to be called from setup.py
    """
    args = _parse_args()
    if not args.migration_path and not args.no_migration_name:
        raise Exception("CLI arguement `migration-path` is required "
                        "but not found")
    if args.migrations_to_ignore is None:
        args.migrations_to_ignore = 0

    # CI Tasks
    if not args.no_migration_name:
        check_migration_name(args.migration_path, args.migrations_to_ignore)

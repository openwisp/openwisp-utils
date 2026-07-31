import os
import subprocess
import tempfile
from os import path
from unittest.mock import patch

from django.test import TestCase
from openwisp_utils.qa import check_commit_message, check_migration_name
from openwisp_utils.tests import capture_stderr, capture_stdout

MIGRATIONS_DIR = path.join(
    path.dirname(path.dirname(path.abspath(__file__))), "migrations"
)


class TestQa(TestCase):
    _test_migration_file = "%s/0002_auto_20181001_0421.py" % MIGRATIONS_DIR
    _test_rst_file = "TEST.rst"

    def setUp(self):
        # Create a fake migration file with default name
        open(self._test_migration_file, "w").close()
        # Create a fake rst file
        open(self._test_rst_file, "w").close()

    def tearDown(self):
        os.unlink(self._test_migration_file)
        os.unlink(self._test_rst_file)

    def test_qa_call_check_migration_name_pass(self):
        options = [
            "checkmigrations",
            "--migrations-to-ignore",
            "2",
            "--migration-path",
            MIGRATIONS_DIR,
            "--quiet",
        ]
        with patch("argparse._sys.argv", options):
            try:
                check_migration_name()
            except (SystemExit, Exception) as e:
                self.fail(e)

    @capture_stderr()
    def test_qa_call_check_migration_name_failure(self):
        options = [
            [
                "checkmigrations",
                "--migrations-to-ignore",
                "1",
                "--migration-path",
                MIGRATIONS_DIR,
                "--quiet",
            ],
            ["checkmigrations", "--migration-path", MIGRATIONS_DIR, "--quiet"],
            ["checkmigrations"],
        ]
        for option in options:
            with patch("argparse._sys.argv", option), self.subTest(option):
                with self.assertRaises(SystemExit):
                    check_migration_name()

    @capture_stdout()
    def test_migration_failure_message(self, captured_output):
        bad_migration = ["checkmigrations", "--migration-path", MIGRATIONS_DIR]
        with patch("argparse._sys.argv", bad_migration):
            try:
                check_migration_name()
            except SystemExit:
                message = "must be renamed to something more descriptive"
                self.assertIn(message, captured_output.getvalue())
            else:
                self.fail("SystemExit not raised")

    def test_qa_call_check_commit_message_pass(self):
        options = [
            ["commitcheck", "--quiet", "--message", "[qa] Minor clean up operations"],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Updated more file and fix problem #20\n\n"
                "Added more files Fixes #20",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Improved Y #2\n\nRelated to #2",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Finished task #2\n\nCloses #2\nRelated to #1",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Finished task #2\n\nRelated to #2\nCloses #1",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Finished task #2\n\nRelated to #2\nRelated to #1",
            ],
            # noqa
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Improved Y #20\n\n"
                "Simulation of a special unplanned case\n\n#noqa",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[fix] Fixed extensibility of openwisp-users and added sample_users test app #377\n\n"
                "Closes #377\r\n\r\nCo-authored-by: Ajay Tripathi <ajay39in@gmail.com>",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[feature] Allow device name to be configured as not unique #443\n\n"
                "Unique device names can now be turned off.\n\nCloses #443.",
            ],
        ]
        for option in options:
            with patch("argparse._sys.argv", option), self.subTest(option):
                try:
                    check_commit_message()
                except (SystemExit, Exception) as e:
                    msg = "Check failed:\n\n{}\n\nOutput:{}".format(option[-1], e)
                    self.fail(msg)

    @capture_stderr()
    def test_qa_call_check_commit_message_failure(self):
        options = [
            ["commitcheck"],
            ["commitcheck", "--quiet", "--message", "Hello World"],
            ["commitcheck", "--quiet", "--message", "[qa] hello World"],
            ["commitcheck", "--quiet", "--message", "[qa] Hello World."],
            ["commitcheck", "--quiet", "--message", "[qa] Hello World.\nFixes #20"],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Fixed problem #20\n\nFixed problem X #20",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Finished task #2\n\nResolves problem described in #2",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Fixed problem\n\nFailure #2\nRelated to #1",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Updated file and fixed problem\n\nAdded more files. Fixes #20",
            ],
            ["commitcheck", "--quiet", "--message", "[qa] Improved Y\n\nRelated to #2"],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Improved Y #2\n\nUpdated files",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "[qa] Improved Y #20\n\nRelated to #32 Fixes #30 Fix #40",
            ],
            # issue 136
            ["commitcheck", "--quiet", "--message", "[qa] Fixed issue #20"],
        ]
        for option in options:
            with patch("argparse._sys.argv", option), self.subTest(option):
                with self.assertRaises(SystemExit):
                    check_commit_message()

    @capture_stdout()
    def test_commit_failure_message(self, captured_output):
        bad_commit = [
            "commitcheck",
            "--message",
            "[qa] Updated file and fixed problem\n\nAdded more files. Fixes #20",
        ]
        with patch("argparse._sys.argv", bad_commit):
            try:
                check_commit_message()
            except SystemExit:
                message = "Your commit message does not follow our commit message style guidelines"
                self.assertIn(message, captured_output.getvalue())
            else:
                self.fail("SystemExit not raised")

    def test_qa_call_check_commit_message_merge(self):
        options = [
            [
                "commitcheck",
                "--quiet",
                "--message",
                "Merge pull request #17 from TheOneAboveAllTitan/issues/16\n\n"
                "[monitoring] Added migration to create ping for existing devices. #16",
            ],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "Merge branch 'issue-21' into master",
            ],
        ]
        for option in options:
            with patch("argparse._sys.argv", option), self.subTest(option):
                try:
                    check_commit_message()
                except (SystemExit, Exception) as e:
                    msg = "Check failed:\n\n{}\n\nOutput:{}".format(option[-1], e)
                    self.fail(msg)

    def test_qa_call_check_commit_message_bump_version(self):
        options = [
            ["commitcheck", "--quiet", "--message", "Bumped VERSION to 0.4.0"],
            ["commitcheck", "--quiet", "--message", "Bumped VERSION to 1.4.3 beta"],
            [
                "commitcheck",
                "--quiet",
                "--message",
                "Bump style-loader from 1.3.0 to 2.0.0",
            ],
        ]
        for option in options:
            with patch("argparse._sys.argv", option), self.subTest(option):
                try:
                    check_commit_message()
                except (SystemExit, Exception) as e:
                    msg = "Check failed:\n\n{}\n\nOutput:{}".format(option[-1], e)
                    self.fail(msg)

    def test_checkrst_excludes_node_modules(self):
        script_path = path.abspath(path.join(path.dirname(__file__), "../../.."))
        script_path = path.join(script_path, "openwisp-qa-check")
        with tempfile.TemporaryDirectory() as temp_dir:
            bin_dir = path.join(temp_dir, "bin")
            os.mkdir(bin_dir)
            args_path = path.join(temp_dir, "docstrfmt-args.txt")
            docstrfmt_path = path.join(bin_dir, "docstrfmt")
            with open(docstrfmt_path, "w") as f:
                f.write(
                    "#!/bin/sh\n"
                    'for arg in "$@"; do\n'
                    '    printf "%s\\n" "$arg" >> "$DOCSTRFMT_ARGS"\n'
                    "done\n"
                )
            os.chmod(docstrfmt_path, 0o755)
            # Create a normal Python file
            work_file = path.join(temp_dir, "work.py")
            with open(work_file, "w") as f:
                f.write("x = 1\n")
            spaced_file = path.join(temp_dir, "work with spaces.rst")
            with open(spaced_file, "w") as f:
                f.write("Test\n====\n")
            # Create files inside node_modules (should be excluded)
            node_module_py = path.join(temp_dir, "node_modules", "pkg", "file.py")
            os.makedirs(path.dirname(node_module_py))
            with open(node_module_py, "w") as f:
                f.write("y = 2\n")
            node_module_rst = path.join(temp_dir, "node_modules", "other", "doc.rst")
            os.makedirs(path.dirname(node_module_rst))
            with open(node_module_rst, "w") as f:
                f.write("Test\n====\n")
            venv_rst = path.join(temp_dir, ".venv", "package", "doc.rst")
            os.makedirs(path.dirname(venv_rst))
            with open(venv_rst, "w") as f:
                f.write("Test\n====\n")
            hidden_py = path.join(temp_dir, ".github", "actions", "script.py")
            os.makedirs(path.dirname(hidden_py))
            with open(hidden_py, "w") as f:
                f.write("z = 3\n")
            env = os.environ.copy()
            env["DOCSTRFMT_ARGS"] = args_path
            env["PATH"] = f'{bin_dir}:{env["PATH"]}'
            result = subprocess.run(
                [
                    script_path,
                    "--skip-checkmigrations",
                    "--skip-checkendline",
                    "--skip-flake8",
                    "--skip-isort",
                    "--skip-black",
                    "--skip-checkcommit",
                    "--skip-checkmakemigrations",
                ],
                cwd=temp_dir,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                result.stdout.count("SUCCESS: ReStructuredText check successful!"),
                1,
            )
            with open(args_path) as f:
                args = f.read().splitlines()
            quiet_index = args.index("--quiet")
            self.assertIn("./work.py", args)
            self.assertIn("./work with spaces.rst", args)
            self.assertLess(quiet_index, args.index("./work.py"))
            self.assertLess(quiet_index, args.index("./work with spaces.rst"))
            self.assertNotIn("./node_modules/pkg/file.py", args)
            self.assertNotIn("./node_modules/other/doc.rst", args)
            self.assertNotIn("./.venv/package/doc.rst", args)
            self.assertNotIn("./.github/actions/script.py", args)

    def test_format_excludes_virtual_environments(self):
        script_path = path.abspath(path.join(path.dirname(__file__), "../../.."))
        script_path = path.join(script_path, "openwisp-qa-format")
        with tempfile.TemporaryDirectory() as temp_dir:
            bin_dir = path.join(temp_dir, "bin")
            os.mkdir(bin_dir)
            args_paths = {
                command: path.join(temp_dir, f"{command}-args.txt")
                for command in ("isort", "black", "prettier", "docstrfmt")
            }
            for command in ("isort", "black", "prettier"):
                command_path = path.join(bin_dir, command)
                with open(command_path, "w") as f:
                    f.write(
                        "#!/bin/sh\n"
                        'for arg in "$@"; do\n'
                        f'    printf "%s\\n" "$arg" >> "${{{command.upper()}_ARGS}}"\n'
                        "done\n"
                    )
                os.chmod(command_path, 0o755)
            docstrfmt_path = path.join(bin_dir, "docstrfmt")
            with open(docstrfmt_path, "w") as f:
                f.write(
                    "#!/bin/sh\n"
                    'for arg in "$@"; do\n'
                    '    printf "%s\\n" "$arg" >> "$DOCSTRFMT_ARGS"\n'
                    "done\n"
                )
            os.chmod(docstrfmt_path, 0o755)
            work_file = path.join(temp_dir, "work.rst")
            with open(work_file, "w") as f:
                f.write("Test\n====\n")
            prettier_file = path.join(temp_dir, "work.css")
            with open(prettier_file, "w") as f:
                f.write("body {}\n")
            excluded_prettier_files = []
            for directory in (".venv", "venv", "env", ".tox"):
                prettier_file = path.join(temp_dir, directory, "package", "file.css")
                os.makedirs(path.dirname(prettier_file))
                with open(prettier_file, "w") as f:
                    f.write("body {}\n")
                excluded_prettier_files.append(
                    path.join(".", directory, "package", "file.css")
                )
            env = os.environ.copy()
            for command, args_path in args_paths.items():
                env[f"{command.upper()}_ARGS"] = args_path
            env["PATH"] = f'{bin_dir}:{env["PATH"]}'
            result = subprocess.run(
                [script_path], cwd=temp_dir, env=env, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(args_paths["docstrfmt"]) as f:
                args = f.read().splitlines()
            self.assertIn("./work.rst", args)
            self.assertNotIn("./.venv/package/doc.rst", args)
            with open(args_paths["isort"]) as f:
                isort_args = f.read().splitlines()
            self.assertEqual(
                isort_args,
                [
                    "--extend-skip",
                    ".venv",
                    "--extend-skip",
                    "venv",
                    "--extend-skip",
                    "env",
                    "--extend-skip",
                    ".tox",
                    ".",
                ],
            )
            with open(args_paths["black"]) as f:
                black_args = f.read().splitlines()
            self.assertEqual(black_args, ["--extend-exclude", "/(env|ENV)/", "."])
            with open(args_paths["prettier"]) as f:
                prettier_args = f.read().splitlines()
            self.assertIn("./work.css", prettier_args)
            for prettier_file in excluded_prettier_files:
                self.assertNotIn(prettier_file, prettier_args)

    def test_format_skips_docstrfmt_without_eligible_files(self):
        script_path = path.abspath(path.join(path.dirname(__file__), "../../.."))
        script_path = path.join(script_path, "openwisp-qa-format")
        with tempfile.TemporaryDirectory() as temp_dir:
            bin_dir = path.join(temp_dir, "bin")
            os.mkdir(bin_dir)
            docstrfmt_called_path = path.join(temp_dir, "docstrfmt-called")
            for command in ("isort", "black", "prettier"):
                command_path = path.join(bin_dir, command)
                with open(command_path, "w") as f:
                    f.write("#!/bin/sh\n")
                os.chmod(command_path, 0o755)
            docstrfmt_path = path.join(bin_dir, "docstrfmt")
            with open(docstrfmt_path, "w") as f:
                f.write('#!/bin/sh\ntouch "$DOCSTRFMT_CALLED"\n')
            os.chmod(docstrfmt_path, 0o755)
            venv_file = path.join(temp_dir, ".venv", "package", "doc.rst")
            os.makedirs(path.dirname(venv_file))
            with open(venv_file, "w") as f:
                f.write("Test\n====\n")
            env = os.environ.copy()
            env["DOCSTRFMT_CALLED"] = docstrfmt_called_path
            env["PATH"] = f'{bin_dir}:{env["PATH"]}'
            result = subprocess.run(
                [script_path], cwd=temp_dir, env=env, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(path.exists(docstrfmt_called_path))

    def test_checkendline_excludes_coverage_artifacts(self):
        script_path = path.abspath(path.join(path.dirname(__file__), "../../.."))
        script_path = path.join(script_path, "openwisp-qa-check")
        with tempfile.TemporaryDirectory() as temp_dir:
            for filename in (
                ".coverage",
                "coverage.xml",
                path.join("htmlcov", "index.html"),
            ):
                file_path = path.join(temp_dir, filename)
                os.makedirs(path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write("coverage artifact")
            result = subprocess.run(
                [
                    script_path,
                    "--skip-checkmigrations",
                    "--skip-flake8",
                    "--skip-isort",
                    "--skip-black",
                    "--skip-checkrst",
                    "--skip-checkcommit",
                    "--skip-checkmakemigrations",
                ],
                cwd=temp_dir,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_checkendline_handles_filenames_with_spaces(self):
        script_path = path.abspath(path.join(path.dirname(__file__), "../../.."))
        script_path = path.join(script_path, "openwisp-qa-check")
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = path.join(temp_dir, "file with spaces.py")
            with open(file_path, "w") as f:
                f.write("x = 1")
            result = subprocess.run(
                [
                    script_path,
                    "--skip-checkmigrations",
                    "--skip-flake8",
                    "--skip-isort",
                    "--skip-black",
                    "--skip-checkrst",
                    "--skip-checkcommit",
                    "--skip-checkmakemigrations",
                ],
                cwd=temp_dir,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "./file with spaces.py needs newline at the end", result.stdout
            )

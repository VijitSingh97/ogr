import contextlib
import io
import platform
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
OGR = ROOT / "bin" / "ogr"


class OgrTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.repo = Path(self.tempdir.name) / "repo with spaces"
        self.git("init", "-q", "-b", "main", str(self.repo), cwd=ROOT)

    def git(self, *args, cwd=None):
        return subprocess.run(
            ["git", *args], cwd=cwd, text=True, capture_output=True, check=True
        )

    def add_remote(self, url, name="origin"):
        self.git("-C", str(self.repo), "remote", "add", name, url)

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, str(OGR), *map(str, args)],
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    def run_mocked(self, remote, *args, branch="main", system="Darwin", opener="/usr/bin/xdg-open"):
        calls = []

        def fake_run(command, *positional, **kwargs):
            command = list(command)
            calls.append((command, positional, kwargs))
            self.assertFalse(kwargs.get("shell"), command)
            if command[-4:-1] == ["remote", "get-url", "--"]:
                return subprocess.CompletedProcess(command, 0, remote + "\n", "")
            if command[-4:] == ["symbolic-ref", "--quiet", "--short", "HEAD"]:
                return subprocess.CompletedProcess(command, 0, branch + "\n", "")
            if command[0] in ("/usr/bin/open", "/usr/bin/xdg-open"):
                return subprocess.CompletedProcess(command, 0, "", "")
            self.fail(f"unexpected process call: {command!r}")

        stdout, stderr = io.StringIO(), io.StringIO()
        forbidden = mock.Mock(side_effect=AssertionError("unmocked process call"))
        patches = (
            mock.patch.object(sys, "argv", [str(OGR), *map(str, args)]),
            mock.patch.object(sys, "platform", "darwin" if system == "Darwin" else "linux"),
            mock.patch.object(platform, "system", return_value=system),
            mock.patch.object(
                shutil, "which",
                side_effect=lambda command: "/usr/bin/git" if command == "git" else opener,
            ),
            mock.patch.object(subprocess, "run", side_effect=fake_run),
            mock.patch.object(subprocess, "call", forbidden),
            mock.patch.object(subprocess, "check_call", forbidden),
            mock.patch.object(subprocess, "check_output", forbidden),
            mock.patch.object(subprocess, "Popen", forbidden),
        )
        with contextlib.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    runpy.run_path(str(OGR), run_name="__main__")
                    code = 0
                except SystemExit as error:
                    code = error.code or 0
        return code, stdout.getvalue(), stderr.getvalue(), calls

    def test_print_normalizes_supported_remote_forms(self):
        cases = {
            "http://user:secret@example.com:8080/team/repo.git?x=1#part":
                "http://example.com:8080/team/repo",
            "git@github.com:team/repo.git": "https://github.com/team/repo",
            "dev@gitlab.com:group/sub group/répô.git":
                "https://gitlab.com/group/sub%20group/r%C3%A9p%C3%B4",
            "ssh://git@github.com:2222/team/already%20encoded.git":
                "https://github.com/team/already%20encoded",
            "git://bitbucket.org:9418/team/repo.git":
                "https://bitbucket.org/team/repo",
        }
        for remote, expected in cases.items():
            with self.subTest(remote=remote):
                if "origin" in self.git("-C", str(self.repo), "remote").stdout.split():
                    self.git("-C", str(self.repo), "remote", "set-url", "origin", remote)
                else:
                    self.add_remote(remote)
                result = self.cli("--print", self.repo)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)
                self.assertEqual(result.stderr, "")

    def test_old_branch_flag_and_new_remote_directory_arguments(self):
        self.add_remote("git@github.com:owner/origin.git")
        self.add_remote("ssh://git@gitlab.com:2222/group/project.git", "upstream")
        self.git("-C", str(self.repo), "symbolic-ref", "HEAD", "refs/heads/feature/foo+bar")
        result = self.cli("-b", "-p", "--remote", "upstream", self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "https://gitlab.com/group/project/-/tree/feature%2Ffoo%2Bbar",
        )

    def test_unborn_branch_works_and_detached_head_fails(self):
        self.add_remote("https://github.com/owner/repo.git")
        result = self.cli("--branch", "--print", self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "https://github.com/owner/repo/tree/main")

        self.git(
            "-C", str(self.repo), "-c", "user.name=Test", "-c",
            "user.email=test@example.invalid", "commit", "--allow-empty", "-qm", "init",
        )
        self.git("-C", str(self.repo), "checkout", "-q", "--detach")
        result = self.cli("--branch", "--print", self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("detached", result.stderr.lower())

    def test_branch_host_rules(self):
        self.add_remote("https://bitbucket.org/owner/repo.git")
        self.git("-C", str(self.repo), "symbolic-ref", "HEAD", "refs/heads/topic/one")
        result = self.cli("--branch", "--print", self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Bitbucket", result.stderr)

        self.git("-C", str(self.repo), "symbolic-ref", "HEAD", "refs/heads/main")
        result = self.cli("--branch", "--print", self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "https://bitbucket.org/owner/repo/src/main")

        self.git("-C", str(self.repo), "remote", "set-url", "origin", "https://code.example/owner/repo.git")
        base = self.cli("--print", self.repo)
        branch = self.cli("--branch", "--print", self.repo)
        self.assertEqual(base.stdout.strip(), "https://code.example/owner/repo")
        self.assertNotEqual(branch.returncode, 0)
        self.assertIn("branch", branch.stderr.lower())

    def test_rejects_unsafe_and_malformed_remotes_without_leaking_them(self):
        remotes = (
            "/tmp/repo", "../repo", "file:///tmp/repo", "ext::sh -c evil",
            "ftp://user:supersecret@example.com/repo", "https://", "git@github.com",
            "https://github.com/team/repo\x01bad",
        )
        for remote in remotes:
            with self.subTest(remote=remote):
                code, stdout, stderr, calls = self.run_mocked(
                    remote, "--print", str(self.repo)
                )
                self.assertNotEqual(code, 0)
                self.assertEqual(stdout, "")
                self.assertTrue(stderr.startswith("ogr:"), stderr)
                self.assertNotIn(remote, stderr)
                self.assertNotIn("supersecret", stderr)
                self.assertEqual(len(calls), 1)

    def test_missing_remote_hides_git_stderr(self):
        result = self.cli("--print", "--remote", "missing", self.repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("ogr:"), result.stderr)
        self.assertNotIn("No such remote", result.stderr)
        self.assertNotIn("error:", result.stderr.lower())

    def test_browser_commands_are_argument_lists(self):
        code, _, stderr, calls = self.run_mocked(
            "git@github.com:owner/repo.git", system="Darwin"
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(calls[0][0], ["git", "-C", ".", "remote", "get-url", "--", "origin"])
        self.assertEqual(calls[-1][0], ["/usr/bin/open", "https://github.com/owner/repo"])

        code, _, stderr, calls = self.run_mocked(
            "https://gitlab.com/group/repo.git", "--branch", str(self.repo),
            branch="topic/one", system="Linux",
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(
            calls[-1][0],
            ["/usr/bin/xdg-open", "https://gitlab.com/group/repo/-/tree/topic%2Fone"],
        )

        code, _, stderr, calls = self.run_mocked(
            "https://github.com/owner/repo", system="Linux", opener=None
        )
        self.assertNotEqual(code, 0)
        self.assertIn("xdg-open", stderr)
        self.assertEqual(len(calls), 1)

    def test_help_and_version_do_not_run_git_or_browser(self):
        for option, expected in (("--help", "usage:"), ("--version", "0.0.1")):
            with self.subTest(option=option):
                code, stdout, stderr, calls = self.run_mocked("unused", option)
                self.assertEqual(code, 0, stderr)
                self.assertIn(expected, stdout)
                self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()

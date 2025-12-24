import unittest
import subprocess
import shutil
import os
import sys
import toml
from pathlib import Path
import time

# Add project root to path
PROJECT_ROOT = Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT))


class TestWtIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 'tmp/memo' is relative to PROJECT_ROOT in the workspace
        cls.source_repo = PROJECT_ROOT / "tmp" / "memo"
        if not cls.source_repo.exists():
            raise RuntimeError(
                f"Source repo not found at {cls.source_repo}. Please clone it first."
            )

        # Create a playground directory for tests
        cls.test_dir = PROJECT_ROOT / "tests" / "playground"
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
        cls.test_dir.mkdir(parents=True)

        print(f"Test Workspace: {cls.test_dir}")
        print(f"Source Repo: {cls.source_repo}")

    def run_wt(self, args, cwd=None, input_str=None):
        """Run wt command via subprocess to simulate real CLI usage"""
        # Run __init__.py directly
        script_path = PROJECT_ROOT / "easy_worktree" / "__init__.py"
        cmd = [sys.executable, str(script_path)] + args
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        # Mocking LANG etc to ensure english output and consistent message matching
        env["LANG"] = "en"
        env["LC_ALL"] = "C"
        env["LANGUAGE"] = "en"
        # Ensure test isolation from host environment
        if "WT_SESSION_NAME" in env:
            del env["WT_SESSION_NAME"]

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.test_dir,
                env=env,
                capture_output=True,
                text=True,
                input=input_str,
            )
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to run wt: {e}")

    def test_01_clone(self):
        """Test 'wt clone'"""
        repo_url = str(self.source_repo)
        repo_name = "memo-project"

        print(f"\nTesting clone {repo_url} -> {repo_name}...")
        result = self.run_wt(["clone", repo_url, repo_name])

        self.assertEqual(result.returncode, 0, f"Clone failed: {result.stderr}")
        self.assertIn("Cloning:", result.stderr)

        # Verify directory structure
        project_dir = self.test_dir / repo_name
        self.assertTrue(project_dir.exists(), "Project directory not created")

        # Verify .wt directory and config created
        self.assertTrue((project_dir / ".wt").exists(), ".wt directory not created")
        self.assertTrue(
            (project_dir / ".wt" / "config.toml").exists(), "config.toml not created"
        )

    def test_02_add_and_config(self):
        """Test 'wt add' and Verify Config Customization"""
        project_dir = self.test_dir / "memo-project"

        # Modify config.toml to change worktrees_dir
        config_file = project_dir / ".wt" / "config.toml"
        with open(config_file, "r") as f:
            config = toml.load(f)

        config["worktrees_dir"] = ".custom_worktrees"

        with open(config_file, "w") as f:
            toml.dump(config, f)

        print("\nTesting add feature-custom with custom config...")
        # wt add feature-custom
        result = self.run_wt(["add", "feature-custom"], cwd=project_dir)

        self.assertEqual(result.returncode, 0, f"Add failed: {result.stderr}")

        # Check if .custom_worktrees/feature-custom exists
        wt_dir = project_dir / ".custom_worktrees" / "feature-custom"
        self.assertTrue(wt_dir.exists(), "Custom Worktree directory not created")

    def test_04_setup(self):
        """Test 'wt setup'"""
        project_dir = self.test_dir / "memo-project"
        wt_dir = project_dir / ".custom_worktrees" / "feature-custom"

        # Create a dummy file in base to sync
        # First ensure it's in config
        config_file = project_dir / ".wt" / "config.toml"
        with open(config_file, "r") as f:
            config = toml.load(f)

        config["setup_files"] = ["test_setup.txt"]

        with open(config_file, "w") as f:
            toml.dump(config, f)

        # Create the file in base
        (project_dir / "test_setup.txt").write_text("setup me")

        print("\nTesting setup...")
        # Ensure it doesn't exist in worktree yet
        self.assertFalse((wt_dir / "test_setup.txt").exists())

        # Run setup
        result = self.run_wt(["setup"], cwd=wt_dir)
        self.assertEqual(result.returncode, 0, f"Setup failed: {result.stderr}")
        self.assertEqual(result.returncode, 0)

        # Verify it exists in worktree now
        self.assertTrue((wt_dir / "test_setup.txt").exists())
        self.assertEqual((wt_dir / "test_setup.txt").read_text(), "setup me")

        # Cleanup: Remove the file to make worktree clean for test_08_rm
        subprocess.run(["git", "clean", "-fd"], cwd=wt_dir)
        subprocess.run(["git", "checkout", "."], cwd=wt_dir)

    def test_06_clean(self):
        """Test 'wt clean'"""
        project_dir = self.test_dir / "memo-project"

        # Create another worktree to clean
        self.run_wt(["add", "temp-cleanup"], cwd=project_dir)

        # Verify creation
        wt_dir = project_dir / ".custom_worktrees" / "temp-cleanup"
        self.assertTrue(wt_dir.exists())

        # Ensure temp-cleanup is clean (hooks might have created untracked files)
        subprocess.run(["git", "clean", "-fdx"], cwd=wt_dir)
        subprocess.run(["git", "checkout", "."], cwd=wt_dir)

        # Make feature-custom dirty so it doesn't get cleaned
        feature_custom_dir = project_dir / ".custom_worktrees" / "feature-custom"
        if feature_custom_dir.exists():
            (feature_custom_dir / "dirty_file").write_text("dirty")

        print("\nTesting clean --all...")
        # wt clean --all still asks for confirmation
        # We need to simulate merged or old worktrees to fully test clean logic, or force clean clean ones manually.
        # But 'clean' in `easy-worktree` implementation checks for 'is_clean' (git status).
        # We assume newly created worktree is clean.

        # Note: In our current implementation, `wt clean --all` asks confirmation.
        result = self.run_wt(["clean", "--all"], cwd=project_dir, input_str="y\n")

        self.assertEqual(result.returncode, 0, f"Clean failed: {result.stderr}")
        # Verify deletion

        # Verify removal
        self.assertFalse(wt_dir.exists())

    def test_07_init(self):
        """Test 'wt init' on a bare repo"""
        # Create a new bare git repo to test init
        init_test_dir = self.test_dir / "init-test"
        init_test_dir.mkdir()
        subprocess.run(["git", "init"], cwd=init_test_dir)

        print("\nTesting init...")
        result = self.run_wt(["init"], cwd=init_test_dir)
        self.assertEqual(result.returncode, 0, f"Init failed: {result.stderr}")
        self.assertEqual(result.returncode, 0)

        # Verify .wt created
        self.assertTrue((init_test_dir / ".wt").exists())

    def test_08_rm(self):
        """Test 'wt rm'"""
        project_dir = self.test_dir / "memo-project"

        # We used 'feature-custom' in previous tests
        print("\nTesting rm feature-custom...")

        wt_dir = project_dir / ".custom_worktrees" / "feature-custom"
        subprocess.run(["git", "clean", "-fdx"], cwd=wt_dir)
        subprocess.run(["git", "checkout", "."], cwd=wt_dir)

        result = self.run_wt(["rm", "feature-custom"], cwd=project_dir)

        self.assertEqual(result.returncode, 0, f"Rm failed: {result.stderr}")
        self.assertEqual(result.returncode, 0)

        wt_dir = project_dir / ".custom_worktrees" / "feature-custom"
        self.assertFalse(wt_dir.exists(), "Worktree directory still exists")

    def test_09_gitignore(self):
        """Test if .gitignore is updated"""
        # Create a clean repo
        test_dir = self.test_dir / "gitignore-test"
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()

        # Init git repo
        subprocess.run(["git", "init"], cwd=test_dir)

        # Create .gitignore
        (test_dir / ".gitignore").write_text("*.log\n")

        print("\nTesting .gitignore update...")
        # Run wt init
        result = self.run_wt(["init"], cwd=test_dir)
        self.assertEqual(result.returncode, 0)

        # Check .gitignore
        content = (test_dir / ".gitignore").read_text()
        self.assertIn(".worktrees/", content)
        self.assertNotIn(".wt/", content)
        self.assertIn("*.log", content)

    def test_10_list_pr(self):
        """Test 'wt list --pr'"""
        project_dir = self.test_dir / "memo-project"

        # Create a mock 'gh' command
        # This is a bit tricky since we run subprocess.
        # We can add a fake 'gh' script to the PATH.

        bin_dir = self.test_dir / "bin"
        bin_dir.mkdir(exist_ok=True)
        gh_path = bin_dir / "gh"

        script = """#!/bin/sh
case "$*" in
    *"--head feature-with-pr"*)
        echo '[{"state": "OPEN", "isDraft": false, "url": "https://github.com/example/repo/pull/123", "createdAt": "2025-12-20T10:00:00Z", "number": 123}]'
        ;;
    *"--head feature-merged"*)
        echo '[{"state": "MERGED", "isDraft": false, "url": "https://github.com/example/repo/pull/124", "createdAt": "2025-12-20T11:00:00Z", "number": 124}]'
        ;;
    *"--head feature-closed"*)
        echo '[{"state": "CLOSED", "isDraft": false, "url": "https://github.com/example/repo/pull/125", "createdAt": "2025-12-20T12:00:00Z", "number": 125}]'
        ;;
    *"pr list"*"--state merged"*)
        echo '[{"headRefName": "feature-merged"}]'
        ;;
    *"pr view"*)
        echo '{"number": 999}'
        ;;
    *)
        echo "[]"
        ;;
esac
"""
        gh_path.write_text(script)
        gh_path.chmod(0o755)

        # Add bin_dir to PATH
        original_env = os.environ.copy()
        os.environ["PATH"] = f"{bin_dir}:{os.environ['PATH']}"

        try:
            # Ensure a clean state for the root so that auto-copied files don't make worktrees dirty
            for filename in ["test_sync.txt", "untracked.txt"]:
                f = project_dir / filename
                if f.exists():
                    f.unlink()

            print("\nTesting list --pr (enhanced with multiple states)...")
            # Create three worktrees with different PR states
            self.run_wt(["add", "feature-with-pr"], cwd=project_dir)
            self.run_wt(["add", "feature-merged"], cwd=project_dir)
            self.run_wt(["add", "feature-closed"], cwd=project_dir)

            # Add a commit to each to make them "not merged" according to git
            for name in ["feature-with-pr", "feature-merged", "feature-closed"]:
                wt_dir = project_dir / ".custom_worktrees" / name
                if not wt_dir.exists():
                    raise RuntimeError(f"Worktree dir {wt_dir} does not exist.")

                (wt_dir / "commit.txt").write_text(f"commit for {name}")
                subprocess.run(["git", "add", "commit.txt"], cwd=wt_dir, check=True)
                subprocess.run(
                    ["git", "commit", "-m", f"Commit for {name}"],
                    cwd=wt_dir,
                    check=True,
                )
                # Ensure it's clean (no untracked files from hooks etc)
                subprocess.run(["git", "clean", "-fdx"], cwd=wt_dir, check=True)

            result = self.run_wt(["list", "--pr"], cwd=project_dir)
            print(f"DEBUG: wt list --pr output:\n{result.stdout}")

            # Check for symbols: ● (Open), ✔ (Merged), ✘ (Closed)
            self.assertIn("●", result.stdout, "Open PR symbol missing")
            self.assertIn("✔", result.stdout, "Merged PR symbol missing")
            self.assertIn("✘", result.stdout, "Closed PR symbol missing")

            self.assertIn("#123", result.stdout)
            self.assertIn("#124", result.stdout)
            self.assertIn("#125", result.stdout)

            print("Testing wt clean --merged using PR status...")
            # feature-merged should be removed, but feature-with-pr and feature-closed should stay
            # (feature-closed is not merged, just closed)

            # Use 'n' to verify targets without deleting
            clean_res = self.run_wt(
                ["clean", "--merged"], cwd=project_dir, input_str="n\n"
            )
            self.assertIn("feature-merged (reason: merged", clean_res.stderr)
            self.assertNotIn("feature-with-pr", clean_res.stderr)

        finally:
            # Restore ENV
            os.environ.clear()
            os.environ.update(original_env)

    def test_11_stash(self):
        """Test 'wt stash'"""
        test_dir = self.test_dir / "stash-test"
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir()

        # Init git repo
        subprocess.run(["git", "init"], cwd=test_dir)
        (test_dir / "README.md").write_text("Hello")
        subprocess.run(["git", "add", "."], cwd=test_dir)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=test_dir)

        # Make it a wt-ready repo
        self.run_wt(["init"], cwd=test_dir)

        # Commit .gitignore to avoid it being stashed
        subprocess.run(["git", "add", ".gitignore"], cwd=test_dir)
        subprocess.run(["git", "commit", "-m", "Add .gitignore"], cwd=test_dir)

        # Add some changes
        (test_dir / "README.md").write_text("Modified")
        (test_dir / "untracked.txt").write_text("Untracked")

        print("\nTesting wt stash...")
        result = self.run_wt(["stash", "feature-stash"], cwd=test_dir)
        if result.returncode != 0:
            print(f"Stash stdout: {result.stdout}")
        self.assertEqual(result.returncode, 0, f"Stash failed: {result.stderr}")
        self.assertEqual(result.returncode, 0)

        # Check if new worktree exists
        stash_wt_dir = test_dir / ".worktrees" / "feature-stash"
        self.assertTrue(stash_wt_dir.exists())

        # Check if changes are there
        self.assertEqual((stash_wt_dir / "README.md").read_text(), "Modified")
        self.assertEqual((stash_wt_dir / "untracked.txt").read_text(), "Untracked")

        # Check if original is clean
        orig_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=test_dir,
            capture_output=True,
            text=True,
        )
        self.assertEqual(orig_status.stdout.strip(), "")

    def test_13_pr(self):
        """Test 'wt pr add' and 'wt pr co'"""
        project_dir = self.test_dir / "memo-project"

        # Prepare mock gh
        bin_dir = self.test_dir / "bin"
        bin_dir.mkdir(exist_ok=True)
        gh_path = bin_dir / "gh"

        script = """#!/bin/sh
if [ "$1" = "pr" ] && [ "$2" = "view" ]; then
    echo '{"number": 999}'
fi
"""
        gh_path.write_text(script)
        gh_path.chmod(0o755)

        # Prepare origin for fetch
        subprocess.run(
            ["git", "update-ref", "refs/pull/999/head", "HEAD"], cwd=project_dir
        )
        subprocess.run(
            ["git", "remote", "set-url", "origin", str(project_dir)], cwd=project_dir
        )

        # Add bin_dir to PATH
        original_env = os.environ.copy()
        os.environ["PATH"] = f"{bin_dir}:{os.environ['PATH']}"

        try:
            print("\nTesting wt pr add 999...")
            result = self.run_wt(["pr", "add", "999"], cwd=project_dir)
            if result.returncode != 0:
                print(f"PR Add STDOUT: {result.stdout}")
                print(f"PR Add STDERR: {result.stderr}")
            self.assertEqual(result.returncode, 0)

            # Check if pr@999 exists
            pr_wt_dir = project_dir / ".custom_worktrees" / "pr@999"
            self.assertTrue(pr_wt_dir.exists())

        finally:
            # Restore ENV
            os.environ.clear()
            os.environ.update(original_env)

    def test_06_clean_merged_logic(self):
        """Test 'wt clean --merged' safeguard for fresh branches"""
        clean_dir = self.test_dir / "clean-logic-test"
        if clean_dir.exists():
            import shutil

            shutil.rmtree(clean_dir)
        clean_dir.mkdir()

        # Init main repo
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=clean_dir,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=clean_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=clean_dir, check=True
        )
        with open(clean_dir / "README.md", "w") as f:
            f.write("# Main")
        subprocess.run(
            ["git", "add", "."], cwd=clean_dir, check=True, stdout=subprocess.DEVNULL
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=clean_dir,
            check=True,
            stdout=subprocess.DEVNULL,
        )

        # Init easy-worktree
        self.run_wt(["init"], cwd=clean_dir)

        # 2. Add 'feature-merged' (merged into main)
        # Create branch, commit, merge
        subprocess.run(
            ["git", "checkout", "-b", "feature-merged"],
            cwd=clean_dir,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        with open(clean_dir / "merged.txt", "w") as f:
            f.write("merged")
        subprocess.run(
            ["git", "add", "."], cwd=clean_dir, check=True, stdout=subprocess.DEVNULL
        )
        subprocess.run(
            ["git", "commit", "-m", "Feature merged"],
            cwd=clean_dir,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=clean_dir,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "merge", "--no-ff", "feature-merged"],
            cwd=clean_dir,
            check=True,
            stdout=subprocess.DEVNULL,
        )

        # Add worktree for it
        self.run_wt(["add", "feature-merged", "feature-merged"], cwd=clean_dir)

        # 3. Add 'feature-fresh' (new branch from main, no commits)
        self.run_wt(["add", "feature-fresh", "main"], cwd=clean_dir)

        # 4. Clean with --merged
        # Expectation: feature-merged is listed (merged), feature-fresh is NOT (safeguard)
        # Using input_str="n\n" to cancel deletion, acting as check
        result = self.run_wt(["clean", "--merged"], cwd=clean_dir, input_str="n\n")

        print(f"\nClean Output:\n{result.stderr}")

        self.assertIn("feature-merged", result.stderr)
        self.assertNotIn("feature-fresh", result.stderr)

    @classmethod
    def tearDownClass(cls):
        # Cleanup
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
            pass

    def test_14_list_default_sort(self):
        """Test 'wt list' default sort (created desc)"""
        project_dir = self.test_dir / "sort-test"
        if project_dir.exists():
            shutil.rmtree(project_dir)
        project_dir.mkdir()
        subprocess.run(["git", "init"], cwd=project_dir)
        (project_dir / "README.md").write_text("Hello")
        subprocess.run(["git", "add", "."], cwd=project_dir)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_dir)
        self.run_wt(["init"], cwd=project_dir)

        # Create worktrees with delay
        print("\nTesting wt list default sort...")
        self.run_wt(["add", "wt-old"], cwd=project_dir)
        time.sleep(1.1)  # Ensure different st_ctime
        self.run_wt(["add", "wt-new"], cwd=project_dir)

        result = self.run_wt(["list"], cwd=project_dir)

        # Check order: wt-new should appear before wt-old
        lines = result.stdout.splitlines()
        # Find lines starting with worktree names
        names = []
        for line in lines:
            if "wt-new" in line:
                names.append("wt-new")
            elif "wt-old" in line:
                names.append("wt-old")

        self.assertEqual(
            names, ["wt-new", "wt-old"], f"Expected order [wt-new, wt-old], got {names}"
        )

    def test_15_rm_force(self):
        """Test 'wt rm --force' with dirty worktree"""
        project_dir = self.test_dir / "force-rm-test"
        if project_dir.exists():
            shutil.rmtree(project_dir)
        project_dir.mkdir()
        subprocess.run(["git", "init"], cwd=project_dir)
        (project_dir / "README.md").write_text("Hello")
        subprocess.run(["git", "add", "."], cwd=project_dir)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_dir)
        self.run_wt(["init"], cwd=project_dir)

        # Add worktree
        print("\nTesting wt rm --force...")
        self.run_wt(["add", "dirty-wt"], cwd=project_dir)
        wt_dir = project_dir / ".worktrees" / "dirty-wt"

        # Make it dirty
        (wt_dir / "untracked.txt").write_text("untracked")

        # Try rm without force (should fail)
        result = self.run_wt(["rm", "dirty-wt"], cwd=project_dir)
        self.assertNotEqual(
            result.returncode, 0, "Remove should fail for dirty worktree"
        )
        self.assertTrue(wt_dir.exists(), "Worktree should still exist")

        # Try rm with force (should succeed)
        result = self.run_wt(["rm", "dirty-wt", "--force"], cwd=project_dir)
        self.assertEqual(
            result.returncode, 0, f"Remove with --force failed: {result.stderr}"
        )
        self.assertFalse(wt_dir.exists(), "Worktree should be removed")

        # Try another worktree with -f at the beginning
        self.run_wt(["add", "dirty-wt-2"], cwd=project_dir)
        wt_dir_2 = project_dir / ".worktrees" / "dirty-wt-2"
        (wt_dir_2 / "modified.txt").write_text("modified")

        result = self.run_wt(["rm", "-f", "dirty-wt-2"], cwd=project_dir)
        self.assertEqual(
            result.returncode, 0, f"Remove with -f failed: {result.stderr}"
        )
        self.assertFalse(wt_dir_2.exists(), "Worktree 2 should be removed")

    def test_16_current(self):
        """Test 'wt current'"""
        project_dir = self.test_dir / "current-test"
        if project_dir.exists():
            shutil.rmtree(project_dir)
        project_dir.mkdir()
        subprocess.run(["git", "init"], cwd=project_dir)
        (project_dir / "README.md").write_text("Hello")
        subprocess.run(["git", "add", "."], cwd=project_dir)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_dir)
        self.run_wt(["init"], cwd=project_dir)

        # 1. Test in main project root
        result = self.run_wt(["current"], cwd=project_dir)
        self.assertEqual(result.stdout.strip(), "main", f"Stderr: {result.stderr}")

        # 2. Test in a worktree
        self.run_wt(["add", "feature-curr"], cwd=project_dir)
        wt_dir = project_dir / ".worktrees" / "feature-curr"
        
        result = self.run_wt(["current"], cwd=wt_dir)
        self.assertEqual(result.stdout.strip(), "feature-curr")

        # 3. Test with environment variable (simulated subshell)
        env = os.environ.copy()
        env["WT_SESSION_NAME"] = "env-session"
        script_path = PROJECT_ROOT / "easy_worktree" / "__init__.py"
        cmd = [sys.executable, str(script_path), "current"]
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        res = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True, env=env)
        self.assertEqual(res.stdout.strip(), "env-session")


    def test_17_skip_setup(self):
        """Test 'wt add --skip-setup'"""
        project_dir = self.test_dir / "skip-setup-test"
        if project_dir.exists():
            shutil.rmtree(project_dir)
        project_dir.mkdir()
        subprocess.run(["git", "init"], cwd=project_dir)
        (project_dir / "README.md").write_text("Hello")
        subprocess.run(["git", "add", "."], cwd=project_dir)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_dir)
        self.run_wt(["init"], cwd=project_dir)

        # Config setup files
        config_file = project_dir / ".wt" / "config.toml"
        # We need to make sure config exists (init creates it)
        with open(config_file, "r") as f:
            config = toml.load(f)
        config["setup_files"] = ["setup_me.txt"]
        with open(config_file, "w") as f:
            toml.dump(config, f)

        # Create the setup file
        (project_dir / "setup_me.txt").write_text("setup content")

        # Create post-add hook that creates a file
        hook_path = project_dir / ".wt" / "post-add"
        hook_path.write_text("""#!/bin/sh
touch hook_ran.txt
""")
        hook_path.chmod(0o755)

        print("\nTesting wt add --skip-setup...")
        self.run_wt(["add", "wt-skipped", "--skip-setup"], cwd=project_dir)
        
        wt_dir = project_dir / ".worktrees" / "wt-skipped"
        
        # Verify setup file NOT copied
        self.assertFalse((wt_dir / "setup_me.txt").exists(), "Setup file should NOT be copied")
        
        # Verify hook NOT ran
        self.assertFalse((wt_dir / "hook_ran.txt").exists(), "Hook should NOT run")

        print("\nTesting wt add WITHOUT --skip-setup (control)...")
        self.run_wt(["add", "wt-normal"], cwd=project_dir)
        wt_normal_dir = project_dir / ".worktrees" / "wt-normal"
        
        # Verify setup file copied
        self.assertTrue((wt_normal_dir / "setup_me.txt").exists(), "Setup file SHOULD be copied")
        
        # Verify hook ran
        self.assertTrue((wt_normal_dir / "hook_ran.txt").exists(), "Hook SHOULD run")


    def test_18_config_local(self):
        """Test 'config.local.toml' priority and .gitignore update"""
        project_dir = self.test_dir / "local-config-test"
        if project_dir.exists():
            shutil.rmtree(project_dir)
        project_dir.mkdir()
        subprocess.run(["git", "init"], cwd=project_dir)
        (project_dir / "README.md").write_text("Hello")
        subprocess.run(["git", "add", "."], cwd=project_dir)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_dir)
        self.run_wt(["init"], cwd=project_dir)

        # 1. Verify .wt/.gitignore contains config.local.toml
        wt_gitignore = project_dir / ".wt" / ".gitignore"
        self.assertTrue(wt_gitignore.exists())
        self.assertIn("config.local.toml", wt_gitignore.read_text())

        # 2. Config setup files basic
        config_file = project_dir / ".wt" / "config.toml"
        with open(config_file, "r") as f:
            config = toml.load(f)
        config["setup_files"] = ["base.txt"]
        with open(config_file, "w") as f:
            toml.dump(config, f)

        # 3. Create overrides in config.local.toml
        local_config_file = project_dir / ".wt" / "config.local.toml"
        local_config_data = {
            "setup_files": ["local.txt"]
        }
        with open(local_config_file, "w") as f:
            toml.dump(local_config_data, f)
            
        # Create files
        (project_dir / "base.txt").write_text("base")
        (project_dir / "local.txt").write_text("local")

        # 4. Run add (should use local.txt, NOT base.txt due to override)
        print("\nTesting wt add with config.local.toml override...")
        self.run_wt(["add", "wt-local"], cwd=project_dir)
        
        wt_dir = project_dir / ".worktrees" / "wt-local"
        
        self.assertTrue((wt_dir / "local.txt").exists(), "Should have copied local.txt from config.local.toml")
        self.assertFalse((wt_dir / "base.txt").exists(), "Should NOT have copied base.txt (overridden)")


    def test_19_wt_gitignore_last_selection(self):
        """Test if .wt/.gitignore contains last_selection after wt select"""
        project_dir = self.test_dir / "wt-gitignore-test"
        if project_dir.exists():
            shutil.rmtree(project_dir)
        project_dir.mkdir()
        subprocess.run(["git", "init"], cwd=project_dir)
        (project_dir / "README.md").write_text("Hello")
        subprocess.run(["git", "add", "."], cwd=project_dir)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_dir)
        
        # wt init
        self.run_wt(["init"], cwd=project_dir)
        
        # Verify .wt/.gitignore exists and contains last_selection
        wt_gitignore = project_dir / ".wt" / ".gitignore"
        self.assertTrue(wt_gitignore.exists())
        self.assertIn("last_selection", wt_gitignore.read_text())
        
        # Test wt select also triggers it (though init already does)
        # Remove .wt to test re-creation/initialization by select
        shutil.rmtree(project_dir / ".wt")
        self.assertFalse((project_dir / ".wt").exists())
        
        # Run wt select main
        self.run_wt(["select", "main"], cwd=project_dir)
        
        self.assertTrue(wt_gitignore.exists())
        self.assertIn("last_selection", wt_gitignore.read_text())

if __name__ == "__main__":
    unittest.main()

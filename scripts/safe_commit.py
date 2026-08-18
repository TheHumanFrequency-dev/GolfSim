#!/usr/bin/env python3
"""scripts/safe_commit.py - pre-flight lock check + commit + honest push-state report.

The structural fix for a recurring interruption across the THF repo fleet:
stale `.git/index.lock` / `.git/HEAD.lock` files have blocked commits
repeatedly (11 stale locks were cleared in one 2026-07-29 sweep across THF
repos; thehumanfrequency.net alone hit it 5 times across 3 sessions), and
separately, a green local commit has been mistaken for "done" more than
once - commits have sat unpushed while a session reported the work
finished, on repos where "committed" and "pushed" are two very different
states.

Two jobs, always both:

  1. Before touching git: detect a STALE lock (no git process anywhere on
     the system currently holding it) and clear it. Refuse to touch a lock
     if any git-family process is running - that's the one case a wrong
     "stale" read could actually corrupt an in-flight operation. Fail safe:
     if process enumeration itself fails, treat it as unsafe and stop.

  2. After a commit: report the TRUE `git status -sb` ahead/behind state
     against the tracked upstream. A successful `git commit` is never
     printed as the end of the story - if the branch is ahead of its
     upstream, that is stated loudly, every time. (Whether "ahead of
     origin" also means "not live" depends on this repo's own deploy
     trigger - the fact this script can actually verify is "not pushed.")

Usage:
    python scripts/safe_commit.py --check
        Lock check + push-state report only. No add, no commit.

    python scripts/safe_commit.py -m "commit message" [file ...]
        Pre-flight, `git add` the given files (explicit paths only - this
        script will not run `git add -A` or `git add .`), commit, then
        report the true ahead/pushed state.

    python scripts/safe_commit.py -m "commit message" --staged
        Same, but commits whatever is already staged instead of adding
        new files.

Never pushes. Deploying (and pushing) stays a deliberate, separate step.
"""
import argparse
import os
import platform
import re
import subprocess
import sys
import time

LOCK_NAMES = ("index.lock", "HEAD.lock")
MIN_LOCK_AGE_SECONDS = 5  # light guard against a same-instant TOCTOU race


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, **kw)


def repo_root():
    r = run(["git", "rev-parse", "--show-toplevel"])
    if r.returncode != 0:
        sys.exit("Not inside a git repository (git rev-parse --show-toplevel failed).")
    return r.stdout.strip()


def find_locks(root):
    found = []
    for name in LOCK_NAMES:
        p = os.path.join(root, ".git", name)
        if os.path.exists(p):
            found.append(p)
    return found


def list_git_processes():
    """Return matching process-list lines system-wide, or None if enumeration failed."""
    system = platform.system()
    try:
        if system == "Windows":
            out = run(["tasklist"]).stdout
        else:
            out = run(["ps", "aux"]).stdout
    except Exception:
        return None
    if not out:
        return None
    # \bgit\b matches git.exe / git-lfs.exe / git-remote-https.exe / "git commit ..."
    # but not gitleaks.exe (no word boundary between "git" and "leaks").
    return [line for line in out.splitlines() if re.search(r"\bgit\b", line, re.IGNORECASE)]


def clear_stale_locks(root):
    """Returns True if it's safe to proceed with git operations."""
    locks = find_locks(root)
    if not locks:
        return True

    print(f"Found {len(locks)} lock file(s): {', '.join(os.path.basename(l) for l in locks)}")

    procs = list_git_processes()
    if procs is None:
        print("  ! could not enumerate running processes - treating as UNSAFE, not touching any lock.")
        print("  Diagnose manually: check for a live git process, then delete the lock by hand if it's clear.")
        return False
    if procs:
        print("  A git-family process is running - NOT touching the lock(s). This may be a real in-flight operation.")
        for line in procs[:5]:
            print(f"    {line.strip()}")
        return False

    now = time.time()
    for lock in locks:
        age = now - os.path.getmtime(lock)
        if age < MIN_LOCK_AGE_SECONDS:
            print(f"  {os.path.basename(lock)} is only {age:.1f}s old and no git process is currently visible - "
                  f"could be a same-instant race. Not touching it; re-run in a few seconds.")
            return False

    for lock in locks:
        age = now - os.path.getmtime(lock)
        os.remove(lock)
        print(f"  Removed stale {os.path.basename(lock)} (age {age:.0f}s, no git process running).")
    return True


def ahead_behind_status(root):
    """Returns (ahead, behind, has_upstream, branch, raw_first_line)."""
    r = run(["git", "status", "-sb"], cwd=root)
    first_line = r.stdout.splitlines()[0] if r.stdout else ""
    m = re.search(r"\[ahead (\d+)(?:, behind (\d+))?\]", first_line)
    ahead = int(m.group(1)) if m else 0
    behind = int(m.group(2)) if (m and m.group(2)) else 0
    has_upstream = "..." in first_line
    # "## branch...origin/branch [ahead N]" -> "branch"
    branch_match = re.match(r"##\s+([^.\s]+)", first_line)
    branch = branch_match.group(1) if branch_match else "HEAD"
    return ahead, behind, has_upstream, branch, first_line


def report_push_state(root):
    ahead, behind, has_upstream, branch, raw = ahead_behind_status(root)
    print(f"\n{raw}")
    if not has_upstream:
        print("  ! No upstream tracking branch configured - cannot determine push state.")
        return
    if ahead == 0:
        print(f"  In sync with origin/{branch}. If this includes a commit you just made, it has reached"
              " the remote (whether that's 'live' depends on this repo's own deploy trigger).")
    else:
        plural = "commit" if ahead == 1 else "commits"
        print(f"  *** NOT PUSHED *** - {branch} is {ahead} {plural} ahead of origin/{branch}.")
        print(f"  Nothing has reached the remote yet. Run `git push origin {branch}` when ready.")
    if behind:
        print(f"  Also {behind} behind origin/{branch} - consider `git pull` / `git fetch` before pushing.")


def do_commit(root, message, files, use_staged):
    if use_staged:
        staged = run(["git", "diff", "--cached", "--name-only"], cwd=root).stdout.strip()
        if not staged:
            sys.exit("--staged was given but nothing is staged. Stage files first, or pass explicit file paths.")
    elif files:
        r = run(["git", "add", *files], cwd=root)
        if r.returncode != 0:
            sys.exit(f"git add failed:\n{r.stderr}")
    else:
        sys.exit("No files given and --staged not set. Pass explicit file paths "
                 "(this script won't run git add -A / git add .).")

    r = run(["git", "commit", "-m", message], cwd=root)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip(), file=sys.stderr)
        sys.exit(r.returncode)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-m", "--message", help="Commit message. Omit for --check-only mode.")
    ap.add_argument("--staged", action="store_true", help="Commit what's already staged instead of adding files.")
    ap.add_argument("--check", action="store_true", help="Lock check + push-state report only. No commit.")
    ap.add_argument("files", nargs="*", help="Explicit file paths to add before committing.")
    args = ap.parse_args()

    if not args.check and not args.message:
        ap.error("pass -m \"message\" to commit, or --check to only run the lock/push-state check.")

    root = repo_root()

    if not clear_stale_locks(root):
        sys.exit(1)

    if args.check:
        report_push_state(root)
        return

    do_commit(root, args.message, args.files, args.staged)
    report_push_state(root)


if __name__ == "__main__":
    main()

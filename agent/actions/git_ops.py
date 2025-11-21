"""
Git repository operations.

PHASE 8.3: Git integration for repository management with safety controls.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

from agent.core_logging import log_event


class GitOps:
    """
    Git repository operations.

    Features:
    - Initialize repositories
    - Commit changes
    - Branch management
    - Push/pull
    - Status and diff
    - Safety checks

    Example:
        git = GitOps(repo_path="/path/to/repo")

        # Initialize
        await git.init()

        # Commit
        await git.add(".")
        await git.commit("Initial commit")

        # Create branch
        await git.create_branch("feature/new-feature")

        # Push
        await git.push("origin", "main")
    """

    def __init__(self, repo_path: str):
        """
        Initialize git operations.

        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path).resolve()

    async def _run_command(
        self,
        command: List[str],
        check: bool = True
    ) -> tuple[int, str, str]:
        """
        Run git command.

        Args:
            command: Command and arguments
            check: Raise exception on non-zero return code

        Returns:
            (return_code, stdout, stderr)
        """
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=self.repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        return_code = process.returncode

        stdout_str = stdout.decode('utf-8', errors='replace')
        stderr_str = stderr.decode('utf-8', errors='replace')

        if check and return_code != 0:
            raise RuntimeError(
                f"Git command failed: {' '.join(command)}\n"
                f"Error: {stderr_str}"
            )

        return return_code, stdout_str, stderr_str

    async def init(self):
        """Initialize git repository"""
        await self._run_command(['git', 'init'])

        log_event("git_init", {
            "repo_path": str(self.repo_path)
        })

    async def clone(self, url: str, destination: Optional[str] = None):
        """
        Clone repository.

        Args:
            url: Repository URL
            destination: Destination directory (relative to repo_path)
        """
        command = ['git', 'clone', url]
        if destination:
            command.append(destination)

        await self._run_command(command)

        log_event("git_clone", {
            "url": url,
            "destination": destination
        })

    async def add(self, path: str = "."):
        """
        Add files to staging.

        Args:
            path: Path to add (default "." for all)
        """
        await self._run_command(['git', 'add', path])

        log_event("git_add", {
            "path": path
        })

    async def commit(
        self,
        message: str,
        author: Optional[str] = None,
        email: Optional[str] = None
    ):
        """
        Commit changes.

        Args:
            message: Commit message
            author: Author name (optional)
            email: Author email (optional)
        """
        command = ['git', 'commit', '-m', message]

        if author and email:
            command.extend(['--author', f'{author} <{email}>'])

        await self._run_command(command)

        log_event("git_commit", {
            "message": message[:100]
        })

    async def push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False
    ):
        """
        Push to remote.

        Args:
            remote: Remote name (default "origin")
            branch: Branch name (default current branch)
            force: Force push
        """
        command = ['git', 'push']

        if force:
            command.append('--force')

        command.append(remote)

        if branch:
            command.append(branch)

        await self._run_command(command)

        log_event("git_push", {
            "remote": remote,
            "branch": branch or "current",
            "force": force
        })

    async def pull(
        self,
        remote: str = "origin",
        branch: Optional[str] = None
    ):
        """
        Pull from remote.

        Args:
            remote: Remote name
            branch: Branch name
        """
        command = ['git', 'pull', remote]

        if branch:
            command.append(branch)

        await self._run_command(command)

        log_event("git_pull", {
            "remote": remote,
            "branch": branch or "current"
        })

    async def create_branch(self, branch_name: str, checkout: bool = True):
        """
        Create new branch.

        Args:
            branch_name: Branch name
            checkout: Switch to new branch
        """
        if checkout:
            await self._run_command(['git', 'checkout', '-b', branch_name])
        else:
            await self._run_command(['git', 'branch', branch_name])

        log_event("git_create_branch", {
            "branch": branch_name,
            "checkout": checkout
        })

    async def checkout(self, branch_name: str):
        """
        Checkout branch.

        Args:
            branch_name: Branch name
        """
        await self._run_command(['git', 'checkout', branch_name])

        log_event("git_checkout", {
            "branch": branch_name
        })

    async def delete_branch(self, branch_name: str, force: bool = False):
        """
        Delete branch.

        Args:
            branch_name: Branch name
            force: Force delete
        """
        flag = '-D' if force else '-d'
        await self._run_command(['git', 'branch', flag, branch_name])

        log_event("git_delete_branch", {
            "branch": branch_name,
            "force": force
        })

    async def get_status(self) -> Dict[str, Any]:
        """
        Get repository status.

        Returns:
            Dict with status information
        """
        # Get status
        _, status_output, _ = await self._run_command(
            ['git', 'status', '--porcelain'],
            check=False
        )

        # Get current branch
        _, branch_output, _ = await self._run_command(
            ['git', 'branch', '--show-current'],
            check=False
        )

        # Parse status
        modified = []
        added = []
        deleted = []
        untracked = []

        for line in status_output.strip().split('\n'):
            if not line:
                continue

            status = line[:2]
            file_path = line[3:]

            if status.strip() == 'M':
                modified.append(file_path)
            elif status.strip() == 'A':
                added.append(file_path)
            elif status.strip() == 'D':
                deleted.append(file_path)
            elif status.strip() == '??':
                untracked.append(file_path)

        return {
            "branch": branch_output.strip(),
            "modified": modified,
            "added": added,
            "deleted": deleted,
            "untracked": untracked,
            "clean": len(status_output.strip()) == 0
        }

    async def get_diff(self, cached: bool = False) -> str:
        """
        Get diff of changes.

        Args:
            cached: Show staged changes

        Returns:
            Diff output
        """
        command = ['git', 'diff']
        if cached:
            command.append('--cached')

        _, output, _ = await self._run_command(command, check=False)
        return output

    async def get_log(
        self,
        max_count: int = 10,
        oneline: bool = True
    ) -> List[str]:
        """
        Get commit log.

        Args:
            max_count: Maximum number of commits
            oneline: One line per commit

        Returns:
            List of log entries
        """
        command = ['git', 'log', f'--max-count={max_count}']

        if oneline:
            command.append('--oneline')

        _, output, _ = await self._run_command(command, check=False)

        return output.strip().split('\n') if output.strip() else []

    async def get_branches(self) -> List[str]:
        """
        Get list of branches.

        Returns:
            List of branch names
        """
        _, output, _ = await self._run_command(['git', 'branch'], check=False)

        branches = []
        for line in output.strip().split('\n'):
            if line:
                # Remove * and whitespace
                branch = line.strip().lstrip('* ')
                branches.append(branch)

        return branches

    async def get_remotes(self) -> Dict[str, str]:
        """
        Get configured remotes.

        Returns:
            Dict of remote name to URL
        """
        _, output, _ = await self._run_command(
            ['git', 'remote', '-v'],
            check=False
        )

        remotes = {}
        for line in output.strip().split('\n'):
            if line and '(fetch)' in line:
                parts = line.split()
                if len(parts) >= 2:
                    remotes[parts[0]] = parts[1]

        return remotes

    async def add_remote(self, name: str, url: str):
        """
        Add remote.

        Args:
            name: Remote name
            url: Remote URL
        """
        await self._run_command(['git', 'remote', 'add', name, url])

        log_event("git_add_remote", {
            "name": name,
            "url": url
        })

    async def remove_remote(self, name: str):
        """
        Remove remote.

        Args:
            name: Remote name
        """
        await self._run_command(['git', 'remote', 'remove', name])

        log_event("git_remove_remote", {
            "name": name
        })

    async def is_repo(self) -> bool:
        """Check if directory is a git repository"""
        return_code, _, _ = await self._run_command(
            ['git', 'rev-parse', '--git-dir'],
            check=False
        )
        return return_code == 0

    async def get_current_branch(self) -> str:
        """Get current branch name"""
        _, output, _ = await self._run_command(
            ['git', 'branch', '--show-current'],
            check=False
        )
        return output.strip()

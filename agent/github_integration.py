"""
GitHub Integration for Self-Modification Workflow

Provides GitHub API integration for:
- Pull request creation and management
- Branch operations
- Repository analysis
- Self-modification workflow automation

This enables JARVIS to autonomously propose code changes via PRs.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

class PRState(Enum):
    """Pull request state"""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class MergeStrategy(Enum):
    """PR merge strategy"""
    MERGE = "merge"  # Create merge commit
    SQUASH = "squash"  # Squash and merge
    REBASE = "rebase"  # Rebase and merge


@dataclass
class GitHubConfig:
    """GitHub API configuration"""
    token: str
    api_base: str = "https://api.github.com"
    timeout: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> GitHubConfig:
        """Load configuration from environment"""
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if not token:
            raise ValueError(
                "GitHub token not found. Set GITHUB_TOKEN or GH_TOKEN environment variable."
            )
        return cls(token=token)


@dataclass
class PullRequest:
    """Pull request data"""
    number: int
    title: str
    body: str
    state: PRState
    head_branch: str
    base_branch: str
    author: str
    url: str
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime] = None
    mergeable: bool = True
    draft: bool = False

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> PullRequest:
        """Parse PR from GitHub API response"""
        return cls(
            number=data["number"],
            title=data["title"],
            body=data["body"] or "",
            state=PRState(data["state"]),
            head_branch=data["head"]["ref"],
            base_branch=data["base"]["ref"],
            author=data["user"]["login"],
            url=data["html_url"],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            merged_at=(
                datetime.fromisoformat(data["merged_at"].replace("Z", "+00:00"))
                if data.get("merged_at")
                else None
            ),
            mergeable=data.get("mergeable", True),
            draft=data.get("draft", False),
        )


@dataclass
class Branch:
    """Git branch information"""
    name: str
    commit_sha: str
    protected: bool = False


@dataclass
class SelfModificationRequest:
    """Request for JARVIS to modify its own code"""
    analysis: str  # What needs to change and why
    target_files: List[str]  # Files to modify
    changes_description: str  # Detailed change description
    test_plan: str  # How to validate changes
    priority: str = "medium"  # low, medium, high, critical
    auto_merge: bool = False  # Auto-merge if checks pass
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# GitHub API Client
# =============================================================================

class GitHubClient:
    """
    GitHub API client with PR and branch management.

    Usage:
        config = GitHubConfig.from_env()
        client = GitHubClient(config, owner="myorg", repo="myrepo")

        # Create PR
        pr = await client.create_pull_request(
            title="Add new feature",
            body="Description",
            head_branch="feature/new-feature",
            base_branch="main"
        )
    """

    def __init__(self, config: GitHubConfig, owner: str, repo: str):
        """
        Initialize GitHub client.

        Args:
            config: GitHub configuration
            owner: Repository owner (username or org)
            repo: Repository name
        """
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for GitHub integration. Install with: pip install httpx"
            )

        self.config = config
        self.owner = owner
        self.repo = repo
        self.base_url = f"{config.api_base}/repos/{owner}/{repo}"

        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"token {config.token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=config.timeout,
        )

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # -------------------------------------------------------------------------
    # Branch Operations
    # -------------------------------------------------------------------------

    async def get_branch(self, branch_name: str) -> Optional[Branch]:
        """
        Get branch information.

        Args:
            branch_name: Branch name

        Returns:
            Branch object or None if not found
        """
        try:
            response = await self.client.get(f"{self.base_url}/branches/{branch_name}")
            if response.status_code == 404:
                return None
            response.raise_for_status()

            data = response.json()
            return Branch(
                name=data["name"],
                commit_sha=data["commit"]["sha"],
                protected=data.get("protected", False),
            )
        except Exception as e:
            print(f"[GitHub] Error fetching branch {branch_name}: {e}")
            return None

    async def create_branch(
        self,
        branch_name: str,
        base_branch: str = "main"
    ) -> Optional[Branch]:
        """
        Create a new branch from base branch.

        Args:
            branch_name: New branch name
            base_branch: Base branch to branch from

        Returns:
            Branch object or None on failure
        """
        try:
            # Get base branch SHA
            base = await self.get_branch(base_branch)
            if not base:
                print(f"[GitHub] Base branch {base_branch} not found")
                return None

            # Create reference
            response = await self.client.post(
                f"{self.base_url}/git/refs",
                json={
                    "ref": f"refs/heads/{branch_name}",
                    "sha": base.commit_sha,
                },
            )

            if response.status_code == 422:  # Branch already exists
                print(f"[GitHub] Branch {branch_name} already exists")
                return await self.get_branch(branch_name)

            response.raise_for_status()
            print(f"[GitHub] Created branch: {branch_name}")

            return Branch(
                name=branch_name,
                commit_sha=base.commit_sha,
                protected=False,
            )
        except Exception as e:
            print(f"[GitHub] Error creating branch {branch_name}: {e}")
            return None

    async def delete_branch(self, branch_name: str) -> bool:
        """
        Delete a branch.

        Args:
            branch_name: Branch to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            response = await self.client.delete(
                f"{self.base_url}/git/refs/heads/{branch_name}"
            )
            response.raise_for_status()
            print(f"[GitHub] Deleted branch: {branch_name}")
            return True
        except Exception as e:
            print(f"[GitHub] Error deleting branch {branch_name}: {e}")
            return False

    # -------------------------------------------------------------------------
    # Pull Request Operations
    # -------------------------------------------------------------------------

    async def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False,
        labels: Optional[List[str]] = None,
    ) -> Optional[PullRequest]:
        """
        Create a pull request.

        Args:
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch
            draft: Create as draft PR
            labels: Labels to add

        Returns:
            PullRequest object or None on failure
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/pulls",
                json={
                    "title": title,
                    "body": body,
                    "head": head_branch,
                    "base": base_branch,
                    "draft": draft,
                },
            )
            response.raise_for_status()

            pr_data = response.json()
            pr = PullRequest.from_api_response(pr_data)

            # Add labels if provided
            if labels:
                await self.add_labels_to_pr(pr.number, labels)

            print(f"[GitHub] Created PR #{pr.number}: {title}")
            print(f"[GitHub] PR URL: {pr.url}")

            return pr
        except Exception as e:
            print(f"[GitHub] Error creating pull request: {e}")
            return None

    async def get_pull_request(self, pr_number: int) -> Optional[PullRequest]:
        """
        Get pull request by number.

        Args:
            pr_number: PR number

        Returns:
            PullRequest object or None if not found
        """
        try:
            response = await self.client.get(f"{self.base_url}/pulls/{pr_number}")
            if response.status_code == 404:
                return None
            response.raise_for_status()

            return PullRequest.from_api_response(response.json())
        except Exception as e:
            print(f"[GitHub] Error fetching PR #{pr_number}: {e}")
            return None

    async def list_pull_requests(
        self,
        state: PRState = PRState.OPEN,
        base_branch: Optional[str] = None,
    ) -> List[PullRequest]:
        """
        List pull requests.

        Args:
            state: Filter by state (open, closed, all)
            base_branch: Filter by base branch

        Returns:
            List of PullRequest objects
        """
        try:
            params = {"state": state.value if state != "all" else "all"}
            if base_branch:
                params["base"] = base_branch

            response = await self.client.get(
                f"{self.base_url}/pulls",
                params=params,
            )
            response.raise_for_status()

            return [
                PullRequest.from_api_response(pr_data)
                for pr_data in response.json()
            ]
        except Exception as e:
            print(f"[GitHub] Error listing pull requests: {e}")
            return []

    async def update_pull_request(
        self,
        pr_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[PRState] = None,
    ) -> Optional[PullRequest]:
        """
        Update pull request metadata.

        Args:
            pr_number: PR number
            title: New title
            body: New description
            state: New state

        Returns:
            Updated PullRequest or None on failure
        """
        try:
            update_data = {}
            if title:
                update_data["title"] = title
            if body:
                update_data["body"] = body
            if state:
                update_data["state"] = state.value

            response = await self.client.patch(
                f"{self.base_url}/pulls/{pr_number}",
                json=update_data,
            )
            response.raise_for_status()

            return PullRequest.from_api_response(response.json())
        except Exception as e:
            print(f"[GitHub] Error updating PR #{pr_number}: {e}")
            return None

    async def merge_pull_request(
        self,
        pr_number: int,
        strategy: MergeStrategy = MergeStrategy.SQUASH,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> bool:
        """
        Merge a pull request.

        Args:
            pr_number: PR number
            strategy: Merge strategy
            commit_title: Custom commit title
            commit_message: Custom commit message

        Returns:
            True if merged successfully, False otherwise
        """
        try:
            merge_data = {"merge_method": strategy.value}
            if commit_title:
                merge_data["commit_title"] = commit_title
            if commit_message:
                merge_data["commit_message"] = commit_message

            response = await self.client.put(
                f"{self.base_url}/pulls/{pr_number}/merge",
                json=merge_data,
            )

            if response.status_code == 405:
                print(f"[GitHub] PR #{pr_number} cannot be merged (checks failing or conflicts)")
                return False

            response.raise_for_status()
            print(f"[GitHub] Merged PR #{pr_number}")
            return True
        except Exception as e:
            print(f"[GitHub] Error merging PR #{pr_number}: {e}")
            return False

    async def add_labels_to_pr(self, pr_number: int, labels: List[str]) -> bool:
        """Add labels to a PR"""
        try:
            response = await self.client.post(
                f"{self.base_url}/issues/{pr_number}/labels",
                json={"labels": labels},
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"[GitHub] Error adding labels to PR #{pr_number}: {e}")
            return False

    async def add_comment_to_pr(self, pr_number: int, comment: str) -> bool:
        """Add a comment to a PR"""
        try:
            response = await self.client.post(
                f"{self.base_url}/issues/{pr_number}/comments",
                json={"body": comment},
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"[GitHub] Error adding comment to PR #{pr_number}: {e}")
            return False


# =============================================================================
# Self-Modification Workflow
# =============================================================================

class SelfModificationWorkflow:
    """
    Automated workflow for JARVIS self-modification via PRs.

    This implements the self-evolution pipeline:
    1. Analyze what needs to change
    2. Create feature branch
    3. Make code changes
    4. Run tests
    5. Create PR
    6. Monitor checks
    7. Auto-merge if approved

    Usage:
        workflow = SelfModificationWorkflow(github_client, repo_path)

        request = SelfModificationRequest(
            analysis="Need to optimize model routing for cost",
            target_files=["agent/model_router.py"],
            changes_description="Add caching layer to reduce API calls",
            test_plan="Run cost tracking tests",
        )

        pr = await workflow.execute(request)
    """

    def __init__(
        self,
        github_client: GitHubClient,
        repo_path: Path,
        base_branch: str = "main",
    ):
        """
        Initialize self-modification workflow.

        Args:
            github_client: GitHub API client
            repo_path: Local repository path
            base_branch: Base branch for PRs
        """
        self.github = github_client
        self.repo_path = Path(repo_path)
        self.base_branch = base_branch

    def _generate_branch_name(self, request: SelfModificationRequest) -> str:
        """Generate unique branch name for modification"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        # Create slug from analysis
        slug = request.analysis[:30].lower()
        slug = "".join(c if c.isalnum() or c == "-" else "-" for c in slug)
        slug = "-".join(filter(None, slug.split("-")))  # Remove consecutive dashes
        return f"jarvis/self-mod/{slug}-{timestamp}"

    def _generate_pr_body(self, request: SelfModificationRequest) -> str:
        """Generate PR description"""
        return f"""## 🤖 JARVIS Self-Modification Request

### Analysis
{request.analysis}

### Changes
{request.changes_description}

### Files Modified
{chr(10).join(f"- `{f}`" for f in request.target_files)}

### Test Plan
{request.test_plan}

### Priority
**{request.priority.upper()}**

---

*This PR was automatically generated by JARVIS self-modification workflow.*
*Review carefully before merging.*
"""

    def _run_local_git(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run git command in repo directory"""
        return subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )

    async def execute(
        self,
        request: SelfModificationRequest,
        make_changes_callback: Optional[callable] = None,
    ) -> Optional[PullRequest]:
        """
        Execute self-modification workflow.

        Args:
            request: Modification request
            make_changes_callback: Function to make actual code changes
                                  Should accept (repo_path, request) and return success bool

        Returns:
            Created PullRequest or None on failure
        """
        print(f"[SelfMod] Starting self-modification workflow")
        print(f"[SelfMod] Analysis: {request.analysis}")

        # Step 1: Generate branch name
        branch_name = self._generate_branch_name(request)
        print(f"[SelfMod] Branch: {branch_name}")

        # Step 2: Create branch on GitHub
        branch = await self.github.create_branch(branch_name, self.base_branch)
        if not branch:
            print(f"[SelfMod] Failed to create branch")
            return None

        # Step 3: Checkout branch locally
        result = self._run_local_git(["fetch", "origin"])
        if result.returncode != 0:
            print(f"[SelfMod] Git fetch failed: {result.stderr}")
            return None

        result = self._run_local_git(["checkout", "-b", branch_name, f"origin/{self.base_branch}"])
        if result.returncode != 0:
            # Branch might exist, try checking it out
            result = self._run_local_git(["checkout", branch_name])
            if result.returncode != 0:
                print(f"[SelfMod] Git checkout failed: {result.stderr}")
                return None

        # Step 4: Make code changes
        if make_changes_callback:
            print(f"[SelfMod] Making code changes...")
            success = await make_changes_callback(self.repo_path, request)
            if not success:
                print(f"[SelfMod] Code changes failed")
                self._run_local_git(["checkout", self.base_branch])
                return None
        else:
            print(f"[SelfMod] Warning: No change callback provided, creating empty PR")

        # Step 5: Commit changes
        self._run_local_git(["add", "."])
        commit_msg = f"jarvis: {request.analysis}\n\n{request.changes_description}"
        result = self._run_local_git(["commit", "-m", commit_msg])
        if result.returncode != 0:
            if "nothing to commit" in result.stdout:
                print(f"[SelfMod] No changes to commit")
            else:
                print(f"[SelfMod] Git commit failed: {result.stderr}")
            self._run_local_git(["checkout", self.base_branch])
            return None

        # Step 6: Push changes
        result = self._run_local_git(["push", "-u", "origin", branch_name])
        if result.returncode != 0:
            print(f"[SelfMod] Git push failed: {result.stderr}")
            self._run_local_git(["checkout", self.base_branch])
            return None

        # Step 7: Create PR
        pr_title = f"[JARVIS] {request.analysis}"
        pr_body = self._generate_pr_body(request)

        labels = ["jarvis-auto", f"priority-{request.priority}"]

        pr = await self.github.create_pull_request(
            title=pr_title,
            body=pr_body,
            head_branch=branch_name,
            base_branch=self.base_branch,
            draft=not request.auto_merge,
            labels=labels,
        )

        # Step 8: Return to base branch
        self._run_local_git(["checkout", self.base_branch])

        if pr:
            print(f"[SelfMod] ✅ Successfully created PR #{pr.number}")
            print(f"[SelfMod] URL: {pr.url}")

        return pr


# =============================================================================
# Utility Functions
# =============================================================================

async def create_github_client(
    owner: str,
    repo: str,
    token: Optional[str] = None,
) -> GitHubClient:
    """
    Create GitHub client with automatic configuration.

    Args:
        owner: Repository owner
        repo: Repository name
        token: GitHub token (or None to use environment)

    Returns:
        Configured GitHubClient
    """
    if token:
        config = GitHubConfig(token=token)
    else:
        config = GitHubConfig.from_env()

    return GitHubClient(config, owner=owner, repo=repo)


async def quick_pr_create(
    owner: str,
    repo: str,
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main",
) -> Optional[str]:
    """
    Quick helper to create a PR and return URL.

    Args:
        owner: Repository owner
        repo: Repository name
        title: PR title
        body: PR description
        head_branch: Source branch
        base_branch: Target branch

    Returns:
        PR URL or None on failure
    """
    async with await create_github_client(owner, repo) as client:
        pr = await client.create_pull_request(
            title=title,
            body=body,
            head_branch=head_branch,
            base_branch=base_branch,
        )
        return pr.url if pr else None

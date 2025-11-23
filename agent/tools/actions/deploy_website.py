"""
Deploy website to Vercel.

PHASE 7.4: Deploy websites to Vercel with custom domains.

Takes local project, pushes to GitHub, deploys to Vercel.

Requires environment variables:
- VERCEL_TOKEN: Your Vercel API token
- GITHUB_TOKEN: Your GitHub personal access token

Setup:
- Vercel: https://vercel.com/account/tokens
- GitHub: https://github.com/settings/tokens
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict

import agent.core_logging as core_logging
from agent.tools.actions.base import ActionTool, ActionRisk
from agent.tools.base import ToolExecutionContext, ToolManifest, ToolResult

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class DeployWebsiteTool(ActionTool):
    """Deploy website to Vercel"""

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="deploy_website",
            version="1.0.0",
            description="Deploy website to Vercel with optional custom domain",
            domains=["web", "infrastructure"],
            roles=["admin", "developer", "devops"],
            required_permissions=["deploy"],
            input_schema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Local path to project (absolute or relative to project root)"
                    },
                    "custom_domain": {
                        "type": "string",
                        "description": "Custom domain (optional, e.g., example.com)"
                    },
                    "framework": {
                        "type": "string",
                        "enum": ["nextjs", "react", "vue", "static", "gatsby", "nuxt"],
                        "default": "static",
                        "description": "Project framework"
                    },
                    "env_vars": {
                        "type": "object",
                        "description": "Environment variables (optional)"
                    },
                    "github_repo_name": {
                        "type": "string",
                        "description": "GitHub repository name (optional, auto-generated if not provided)"
                    },
                    "github_private": {
                        "type": "boolean",
                        "default": False,
                        "description": "Make GitHub repo private"
                    }
                },
                "required": ["project_path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "deployment_id": {"type": "string"},
                    "github_repo": {"type": "string"},
                    "custom_domain": {"type": "string"},
                    "framework": {"type": "string"}
                }
            },
            cost_estimate=0.0,  # Free tier available
            timeout_seconds=300,
            requires_network=True,
            examples=[
                {
                    "input": {
                        "project_path": "/output/my-website",
                        "custom_domain": "example.com",
                        "framework": "react"
                    },
                    "output": {
                        "url": "https://my-website-abc123.vercel.app",
                        "deployment_id": "dpl_abc123",
                        "github_repo": "https://github.com/user/my-website",
                        "custom_domain": "example.com",
                        "framework": "react"
                    }
                }
            ],
            tags=["deployment", "web", "vercel", "github"]
        )

    async def estimate_cost(self, params: Dict[str, Any]) -> float:
        """Vercel has free tier - cost is $0"""
        # Vercel free tier includes:
        # - Unlimited deployments
        # - 100 GB bandwidth
        # - Custom domains
        return 0.0

    async def execute_action(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Deploy to Vercel"""
        if not REQUESTS_AVAILABLE:
            return ToolResult(
                success=False,
                error="requests library not installed. Install with: pip install requests"
            )

        project_path = params["project_path"]
        custom_domain = params.get("custom_domain")
        framework = params.get("framework", "static")
        env_vars = params.get("env_vars", {})
        github_repo_name = params.get("github_repo_name")
        github_private = params.get("github_private", False)

        # Resolve project path
        if not os.path.isabs(project_path):
            project_path = os.path.join(context.project_path, project_path)

        project_path = Path(project_path).resolve()

        if not project_path.exists():
            return ToolResult(
                success=False,
                error=f"Project path does not exist: {project_path}"
            )

        # Validate path is within project
        if not context.validate_path(project_path):
            return ToolResult(
                success=False,
                error=f"Project path is outside project directory: {project_path}"
            )

        try:
            # Step 1: Initialize git if not already
            git_result = await self._initialize_git(project_path)

            if not git_result["success"]:
                return ToolResult(
                    success=False,
                    error=f"Git initialization failed: {git_result['error']}"
                )

            # Step 2: Create GitHub repo and push
            github_result = await self._create_and_push_to_github(
                project_path,
                github_repo_name or project_path.name,
                github_private
            )

            if not github_result["success"]:
                return ToolResult(
                    success=False,
                    error=f"GitHub push failed: {github_result['error']}"
                )

            repo_url = github_result["repo_url"]

            # Step 3: Deploy to Vercel
            deployment_result = await self._deploy_to_vercel(
                repo_url,
                project_path.name,
                framework,
                env_vars,
                custom_domain
            )

            if not deployment_result["success"]:
                return ToolResult(
                    success=False,
                    error=f"Vercel deployment failed: {deployment_result['error']}"
                )

            core_logging.log_event("website_deployed", {
                "project": project_path.name,
                "url": deployment_result["url"],
                "deployment_id": deployment_result["deployment_id"],
                "github_repo": repo_url
            })

            return ToolResult(
                success=True,
                data={
                    "url": deployment_result["url"],
                    "deployment_id": deployment_result["deployment_id"],
                    "github_repo": repo_url,
                    "custom_domain": custom_domain,
                    "framework": framework
                },
                metadata={
                    "project_path": str(project_path),
                    "git_initialized": git_result.get("initialized", False)
                }
            )

        except Exception as e:
            core_logging.log_event("deployment_failed", {
                "project": project_path.name,
                "error": str(e)
            })
            return ToolResult(
                success=False,
                error=f"Deployment failed: {str(e)}"
            )

    async def rollback(
        self,
        execution_id: str,
        context: ToolExecutionContext
    ) -> bool:
        """Delete Vercel deployment"""
        execution = self.get_execution_history(execution_id)

        if not execution or "result" not in execution:
            return False

        deployment_id = execution["result"].get("deployment_id")

        if not deployment_id:
            return False

        try:
            vercel_token = os.getenv("VERCEL_TOKEN")
            if not vercel_token:
                return False

            # Delete deployment via Vercel API
            response = requests.delete(
                f"https://api.vercel.com/v13/deployments/{deployment_id}",
                headers={"Authorization": f"Bearer {vercel_token}"},
                timeout=30
            )

            success = response.status_code == 200

            core_logging.log_event("deployment_rollback", {
                "execution_id": execution_id,
                "deployment_id": deployment_id,
                "success": success
            })

            return success

        except Exception as e:
            core_logging.log_event("rollback_failed", {
                "execution_id": execution_id,
                "error": str(e)
            })
            return False

    async def _initialize_git(self, project_path: Path) -> Dict[str, Any]:
        """Initialize git repository"""
        git_dir = project_path / ".git"

        if git_dir.exists():
            return {"success": True, "initialized": False, "message": "Already initialized"}

        try:
            # Initialize git
            subprocess.run(
                ["git", "init"],
                cwd=project_path,
                check=True,
                capture_output=True
            )

            # Configure git if needed
            try:
                subprocess.run(
                    ["git", "config", "user.email", "agent@system-1-2.ai"],
                    cwd=project_path,
                    check=True,
                    capture_output=True
                )
                subprocess.run(
                    ["git", "config", "user.name", "System-1.2 Agent"],
                    cwd=project_path,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                pass  # Use global git config

            # Add all files
            subprocess.run(
                ["git", "add", "."],
                cwd=project_path,
                check=True,
                capture_output=True
            )

            # Initial commit
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=project_path,
                check=True,
                capture_output=True
            )

            # Rename to main branch
            try:
                subprocess.run(
                    ["git", "branch", "-M", "main"],
                    cwd=project_path,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                pass  # Already on main

            return {"success": True, "initialized": True}

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Git command failed: {e.stderr.decode() if e.stderr else str(e)}"
            }

    async def _create_and_push_to_github(
        self,
        project_path: Path,
        repo_name: str,
        private: bool = False
    ) -> Dict[str, Any]:
        """Create GitHub repository and push code"""
        github_token = os.getenv("GITHUB_TOKEN")

        if not github_token:
            return {
                "success": False,
                "error": "GITHUB_TOKEN not set in environment"
            }

        try:
            # Get GitHub username
            user_response = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                timeout=30
            )
            user_response.raise_for_status()
            github_user = user_response.json()["login"]

            # Create repository
            create_response = requests.post(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={
                    "name": repo_name,
                    "private": private,
                    "auto_init": False
                },
                timeout=30
            )

            # 422 means repo already exists - that's okay
            if create_response.status_code not in [201, 422]:
                create_response.raise_for_status()

            repo_url = f"https://github.com/{github_user}/{repo_name}.git"

            # Add remote
            try:
                subprocess.run(
                    ["git", "remote", "add", "origin", repo_url],
                    cwd=project_path,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                # Remote already exists - update it
                subprocess.run(
                    ["git", "remote", "set-url", "origin", repo_url],
                    cwd=project_path,
                    check=True,
                    capture_output=True
                )

            # Push to GitHub using token authentication
            auth_repo_url = repo_url.replace("https://", f"https://{github_token}@")

            subprocess.run(
                ["git", "push", "-u", auth_repo_url, "main", "--force"],
                cwd=project_path,
                check=True,
                capture_output=True
            )

            return {
                "success": True,
                "repo_url": repo_url
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"GitHub API error: {str(e)}"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Git push failed: {e.stderr.decode() if e.stderr else str(e)}"
            }

    async def _deploy_to_vercel(
        self,
        repo_url: str,
        project_name: str,
        framework: str,
        env_vars: Dict[str, str],
        custom_domain: str = None
    ) -> Dict[str, Any]:
        """Deploy via Vercel API"""
        vercel_token = os.getenv("VERCEL_TOKEN")

        if not vercel_token:
            return {
                "success": False,
                "error": "VERCEL_TOKEN not set in environment"
            }

        try:
            # Extract repo info
            # Format: https://github.com/user/repo.git
            repo_parts = repo_url.replace(".git", "").split("/")
            repo_owner = repo_parts[-2]
            repo_name = repo_parts[-1]

            # Create deployment
            deployment_data = {
                "name": project_name,
                "gitSource": {
                    "type": "github",
                    "repo": f"{repo_owner}/{repo_name}",
                    "ref": "main"
                }
            }

            # Add environment variables if provided
            if env_vars:
                deployment_data["env"] = [
                    {"key": k, "value": v, "target": ["production"]}
                    for k, v in env_vars.items()
                ]

            # Framework detection
            if framework != "static":
                deployment_data["framework"] = framework

            response = requests.post(
                "https://api.vercel.com/v13/deployments",
                headers={
                    "Authorization": f"Bearer {vercel_token}",
                    "Content-Type": "application/json"
                },
                json=deployment_data,
                timeout=120
            )

            response.raise_for_status()
            deployment = response.json()

            deployment_url = deployment.get("url", "")
            if deployment_url and not deployment_url.startswith("http"):
                deployment_url = f"https://{deployment_url}"

            # Add custom domain if provided
            if custom_domain:
                await self._add_custom_domain(
                    deployment["id"],
                    custom_domain,
                    vercel_token
                )

            return {
                "success": True,
                "url": deployment_url,
                "deployment_id": deployment["id"]
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Vercel API error: {str(e)}"
            }

    async def _add_custom_domain(
        self,
        deployment_id: str,
        domain: str,
        vercel_token: str
    ):
        """Add custom domain to Vercel project"""
        try:
            requests.post(
                f"https://api.vercel.com/v9/projects/{deployment_id}/domains",
                headers={
                    "Authorization": f"Bearer {vercel_token}",
                    "Content-Type": "application/json"
                },
                json={"name": domain},
                timeout=30
            )
        except requests.RequestException:
            # Non-critical - deployment succeeded even if domain addition failed
            core_logging.log_event("custom_domain_failed", {
                "domain": domain,
                "deployment_id": deployment_id
            })

    def _format_action_description(self, params: Dict[str, Any]) -> str:
        """Format action description for approval"""
        project = Path(params["project_path"]).name
        domain = params.get("custom_domain")

        if domain:
            return f"Deploy '{project}' to Vercel with custom domain '{domain}'"
        else:
            return f"Deploy '{project}' to Vercel"

    def _assess_risk(self, params: Dict[str, Any], cost: float) -> ActionRisk:
        """Deployments are low risk (free, easily reversible)"""
        return ActionRisk.LOW

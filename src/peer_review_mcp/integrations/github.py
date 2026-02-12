"""
GitHub integration for pull request management and webhook handling.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import aiohttp
from github import Github, PullRequest as GitHubPR, Repository as GitHubRepo
from datetime import datetime

from ..config import GitHubConfig

logger = logging.getLogger(__name__)


class GitHubIntegration:
    """GitHub integration for managing pull requests and repositories."""
    
    def __init__(self, config: GitHubConfig):
        """Initialize GitHub integration."""
        self.config = config
        self.github = None
        
        if config.access_token:
            self.github = Github(
                config.access_token,
                base_url=config.base_url
            )
            logger.info("GitHub integration initialized")
        else:
            logger.warning("GitHub access token not provided")
    
    async def get_repository(self, full_name: str) -> Optional[Dict[str, Any]]:
        """Get repository information from GitHub."""
        if not self.github:
            return None
        
        try:
            repo = self.github.get_repo(full_name)
            return {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "default_branch": repo.default_branch,
                "owner": repo.owner.login,
                "is_private": repo.private,
                "description": repo.description,
                "language": repo.language,
                "created_at": repo.created_at,
                "updated_at": repo.updated_at
            }
        except Exception as e:
            logger.error(f"Error getting repository {full_name}: {str(e)}")
            return None
    
    async def get_pull_request(
        self, repository: str, pr_number: int
    ) -> Optional[Dict[str, Any]]:
        """Get pull request information from GitHub."""
        if not self.github:
            return None
        
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            return {
                "id": pr.id,
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "user": {
                    "login": pr.user.login,
                    "id": pr.user.id
                },
                "head": {
                    "ref": pr.head.ref,
                    "sha": pr.head.sha,
                    "repo": {
                        "full_name": pr.head.repo.full_name if pr.head.repo else None
                    }
                },
                "base": {
                    "ref": pr.base.ref,
                    "sha": pr.base.sha,
                    "repo": {
                        "full_name": pr.base.repo.full_name
                    }
                },
                "html_url": pr.html_url,
                "diff_url": pr.diff_url,
                "patch_url": pr.patch_url,
                "labels": [
                    {"name": label.name, "color": label.color}
                    for label in pr.labels
                ],
                "assignees": [
                    {"login": assignee.login, "id": assignee.id}
                    for assignee in pr.assignees
                ],
                "requested_reviewers": [
                    {"login": reviewer.login, "id": reviewer.id}
                    for reviewer in pr.requested_reviewers
                ],
                "draft": pr.draft,
                "mergeable": pr.mergeable,
                "mergeable_state": pr.mergeable_state,
                "merged": pr.merged,
                "merge_commit_sha": pr.merge_commit_sha,
                "created_at": pr.created_at,
                "updated_at": pr.updated_at,
                "closed_at": pr.closed_at,
                "merged_at": pr.merged_at
            }
        except Exception as e:
            logger.error(f"Error getting pull request {pr_number} from {repository}: {str(e)}")
            return None
    
    async def get_pull_request_files(
        self, repository: str, pr_number: int
    ) -> List[Dict[str, Any]]:
        """Get list of files changed in a pull request."""
        if not self.github:
            return []
        
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            files = []
            for file in pr.get_files():
                files.append({
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "blob_url": file.blob_url,
                    "raw_url": file.raw_url,
                    "patch": file.patch
                })
            
            return files
        except Exception as e:
            logger.error(f"Error getting PR files for {pr_number} in {repository}: {str(e)}")
            return []
    
    async def get_pull_request_reviews(
        self, repository: str, pr_number: int
    ) -> List[Dict[str, Any]]:
        """Get reviews for a pull request."""
        if not self.github:
            return []
        
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            reviews = []
            for review in pr.get_reviews():
                reviews.append({
                    "id": review.id,
                    "user": {
                        "login": review.user.login,
                        "id": review.user.id
                    },
                    "body": review.body,
                    "state": review.state,
                    "html_url": review.html_url,
                    "submitted_at": review.submitted_at
                })
            
            return reviews
        except Exception as e:
            logger.error(f"Error getting reviews for PR {pr_number} in {repository}: {str(e)}")
            return []
    
    async def get_pull_request_comments(
        self, repository: str, pr_number: int
    ) -> List[Dict[str, Any]]:
        """Get comments for a pull request."""
        if not self.github:
            return []
        
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            # Get issue comments (general PR comments)
            issue_comments = []
            for comment in pr.get_issue_comments():
                issue_comments.append({
                    "id": comment.id,
                    "user": {
                        "login": comment.user.login,
                        "id": comment.user.id
                    },
                    "body": comment.body,
                    "html_url": comment.html_url,
                    "created_at": comment.created_at,
                    "updated_at": comment.updated_at,
                    "type": "issue_comment"
                })
            
            # Get review comments (line-specific comments)
            review_comments = []
            for comment in pr.get_review_comments():
                review_comments.append({
                    "id": comment.id,
                    "user": {
                        "login": comment.user.login,
                        "id": comment.user.id
                    },
                    "body": comment.body,
                    "path": comment.path,
                    "position": comment.position,
                    "line": comment.line,
                    "html_url": comment.html_url,
                    "created_at": comment.created_at,
                    "updated_at": comment.updated_at,
                    "type": "review_comment"
                })
            
            return issue_comments + review_comments
        except Exception as e:
            logger.error(f"Error getting comments for PR {pr_number} in {repository}: {str(e)}")
            return []
    
    async def get_pull_request_commits(
        self, repository: str, pr_number: int
    ) -> List[Dict[str, Any]]:
        """Get commits for a pull request."""
        if not self.github:
            return []
        
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            commits = []
            for commit in pr.get_commits():
                commits.append({
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name,
                        "email": commit.commit.author.email,
                        "date": commit.commit.author.date
                    },
                    "committer": {
                        "name": commit.commit.committer.name,
                        "email": commit.commit.committer.email,
                        "date": commit.commit.committer.date
                    },
                    "html_url": commit.html_url,
                    "stats": {
                        "additions": commit.stats.additions,
                        "deletions": commit.stats.deletions,
                        "total": commit.stats.total
                    } if commit.stats else None
                })
            
            return commits
        except Exception as e:
            logger.error(f"Error getting commits for PR {pr_number} in {repository}: {str(e)}")
            return []
    
    async def trigger_checks(
        self, repository: str, pr_number: int, check_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Trigger GitHub Actions or other checks for a pull request."""
        if not self.github:
            return []
        
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            results = []
            
            # Get existing check runs
            check_runs = pr.head.get_check_runs()
            
            for check_run in check_runs:
                if any(check_type in check_run.name.lower() for check_type in check_types):
                    results.append({
                        "id": check_run.id,
                        "name": check_run.name,
                        "status": check_run.status,
                        "conclusion": check_run.conclusion,
                        "html_url": check_run.html_url,
                        "started_at": check_run.started_at,
                        "completed_at": check_run.completed_at
                    })
            
            # Note: Actually triggering new checks would require workflow dispatch
            # or re-running existing checks via the GitHub API
            
            return results
        except Exception as e:
            logger.error(f"Error triggering checks for PR {pr_number} in {repository}: {str(e)}")
            return []
    
    async def add_comment_to_pull_request(
        self, repository: str, pr_number: int, comment: str
    ) -> Optional[Dict[str, Any]]:
        """Add a comment to a pull request."""
        if not self.github:
            return None
        
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            comment_obj = pr.create_issue_comment(comment)
            
            return {
                "id": comment_obj.id,
                "body": comment_obj.body,
                "html_url": comment_obj.html_url,
                "created_at": comment_obj.created_at
            }
        except Exception as e:
            logger.error(f"Error adding comment to PR {pr_number} in {repository}: {str(e)}")
            return None
    
    async def add_label_to_pull_request(
        self, repository: str, pr_number: int, labels: List[str]
    ) -> bool:
        """Add labels to a pull request."""
        if not self.github:
            return False
        
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            issue = repo.get_issue(pr_number)  # PR is an issue for labeling
            issue.add_to_labels(*labels)
            
            return True
        except Exception as e:
            logger.error(f"Error adding labels to PR {pr_number} in {repository}: {str(e)}")
            return False
    
    async def request_reviewers(
        self, repository: str, pr_number: int, reviewers: List[str]
    ) -> bool:
        """Request reviewers for a pull request."""
        if not self.github:
            return False
        
        try:
            repo = self.github.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            pr.create_review_request(reviewers=reviewers)
            
            return True
        except Exception as e:
            logger.error(f"Error requesting reviewers for PR {pr_number} in {repository}: {str(e)}")
            return False
    
    async def get_repository_pull_requests(
        self, repository: str, state: str = "open", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get pull requests for a repository."""
        if not self.github:
            return []
        
        try:
            repo = self.github.get_repo(repository)
            pull_requests = []
            
            for pr in repo.get_pulls(state=state)[:limit]:
                pull_requests.append({
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "user": pr.user.login,
                    "created_at": pr.created_at,
                    "updated_at": pr.updated_at,
                    "html_url": pr.html_url
                })
            
            return pull_requests
        except Exception as e:
            logger.error(f"Error getting pull requests for {repository}: {str(e)}")
            return []
    
    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Validate GitHub webhook signature."""
        if not self.config.webhook_secret:
            return True  # Skip validation if no secret is configured
        
        import hmac
        import hashlib
        
        expected_signature = "sha256=" + hmac.new(
            self.config.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def handle_webhook_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub webhook events."""
        logger.info(f"Handling GitHub webhook event: {event_type}")
        
        if event_type == "pull_request":
            action = payload.get("action")
            pr_data = payload.get("pull_request")
            
            if action in ["opened", "synchronize", "reopened"]:
                # PR opened or updated
                return {
                    "action": "pr_updated",
                    "repository": payload["repository"]["full_name"],
                    "pr_number": pr_data["number"],
                    "pr_data": pr_data
                }
            elif action == "closed":
                # PR closed
                return {
                    "action": "pr_closed",
                    "repository": payload["repository"]["full_name"],
                    "pr_number": pr_data["number"],
                    "merged": pr_data.get("merged", False)
                }
        
        elif event_type == "pull_request_review":
            action = payload.get("action")
            review_data = payload.get("review")
            pr_data = payload.get("pull_request")
            
            if action == "submitted":
                return {
                    "action": "review_submitted",
                    "repository": payload["repository"]["full_name"],
                    "pr_number": pr_data["number"],
                    "review_data": review_data
                }
        
        elif event_type == "check_run":
            action = payload.get("action")
            check_run_data = payload.get("check_run")
            
            if action == "completed":
                # Find associated PRs
                pull_requests = check_run_data.get("pull_requests", [])
                return {
                    "action": "check_completed",
                    "repository": payload["repository"]["full_name"],
                    "check_run": check_run_data,
                    "pull_requests": pull_requests
                }
        
        return {"action": "no_action", "event_type": event_type}
"""
Governance validation agent for enforcing organizational policies and standards.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import re
import asyncio

from ..models import ReviewStatus, PriorityLevel, CheckStatus
from ..services.database import DatabaseManager

logger = logging.getLogger(__name__)


class GovernanceAgent:
    """AI agent for governance policy validation and enforcement."""
    
    def __init__(self, db_manager: DatabaseManager, config: Optional[Dict] = None):
        """Initialize governance agent."""
        self.db_manager = db_manager
        self.config = config or {}
        self._policy_rules = self._load_governance_policies()
        logger.info("Governance Agent initialized")
    
    def _load_governance_policies(self) -> Dict[str, Any]:
        """Load governance policies and validation rules."""
        return {
            "branch_naming": {
                "enabled": True,
                "patterns": {
                    "feature": r"^feature/[a-z0-9-]+$",
                    "bugfix": r"^bugfix/[a-z0-9-]+$",
                    "hotfix": r"^hotfix/[a-z0-9-]+$",
                    "release": r"^release/v\d+\.\d+\.\d+$"
                },
                "description": "Branch names must follow naming conventions"
            },
            "commit_message": {
                "enabled": True,
                "min_length": 10,
                "max_length": 72,
                "patterns": {
                    "conventional": r"^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+",
                    "jira_ticket": r"[A-Z]+-\d+"
                },
                "description": "Commit messages must follow conventional commit format"
            },
            "pr_size_limits": {
                "enabled": True,
                "max_files_changed": 50,
                "max_lines_changed": 500,
                "exclude_patterns": ["*.md", "*.txt", "*.json"],
                "description": "PR should not change too many files or lines"
            },
            "required_files": {
                "enabled": True,
                "files": {
                    "README.md": "Root level README required",
                    "CHANGELOG.md": "Changelog required for releases",
                    ".gitignore": "Gitignore file required",
                    "requirements.txt": "Python dependencies file required",
                    "pyproject.toml": "Python project configuration required"
                },
                "conditional": {
                    "Dockerfile": ["docker", "container"],  # Required if contains these keywords
                    "docker-compose.yml": ["docker", "compose"],
                    "terraform/": ["terraform", "infrastructure"],
                    "k8s/": ["kubernetes", "k8s"]
                }
            },
            "security_requirements": {
                "enabled": True,
                "forbidden_patterns": [
                    r"password\s*=\s*['\"][^'\"]+['\"]",
                    r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
                    r"secret\s*=\s*['\"][^'\"]+['\"]",
                    r"token\s*=\s*['\"][^'\"]+['\"]"
                ],
                "required_checks": [
                    "security-scan",
                    "dependency-check",
                    "secret-scan"
                ],
                "description": "Security scans and secret detection required"
            },
            "documentation_requirements": {
                "enabled": True,
                "min_coverage": 0.8,
                "required_sections": {
                    "README.md": ["Installation", "Usage", "Contributing"],
                    "API_DOCS.md": ["Endpoints", "Authentication", "Examples"]
                },
                "code_comment_ratio": 0.15,
                "description": "Adequate documentation required"
            },
            "testing_requirements": {
                "enabled": True,
                "min_test_coverage": 80.0,
                "required_test_types": ["unit", "integration"],
                "test_file_patterns": [
                    r"test_.+\.py$",
                    r".+_test\.py$",
                    r"tests/.+\.py$"
                ],
                "description": "Comprehensive testing required"
            },
            "code_quality_standards": {
                "enabled": True,
                "max_complexity": 10,
                "max_function_length": 50,
                "max_class_length": 200,
                "naming_conventions": {
                    "functions": r"^[a-z_][a-z0-9_]*$",
                    "classes": r"^[A-Z][a-zA-Z0-9]*$",
                    "constants": r"^[A-Z][A-Z0-9_]*$"
                },
                "description": "Code must meet quality standards"
            },
            "approval_requirements": {
                "enabled": True,
                "min_reviewers": 2,
                "required_reviewer_roles": ["senior-developer", "tech-lead"],
                "approval_timeout_hours": 48,
                "auto_approval_conditions": {
                    "authors": ["dependabot", "renovate"],
                    "file_patterns": ["*.md", "*.txt"],
                    "max_lines_changed": 10
                },
                "description": "Proper approval workflow required"
            },
            "deployment_policies": {
                "enabled": True,
                "environments": {
                    "production": {
                        "required_approvals": 3,
                        "required_checks": ["security", "performance", "integration"],
                        "deployment_window": ["09:00", "17:00"],
                        "emergency_contacts": ["on-call-engineer"]
                    },
                    "staging": {
                        "required_approvals": 1,
                        "required_checks": ["build", "unit-tests"],
                        "auto_deploy": True
                    }
                },
                "description": "Deployment policies must be followed"
            }
        }
    
    async def validate_pull_request(
        self, pr_data: Dict[str, Any], pr_files: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Comprehensive governance validation for a pull request."""
        logger.info(f"Validating governance for PR {pr_data.get('pr_number')}")
        
        validation_results = {
            "pr_id": pr_data.get("id"),
            "pr_number": pr_data.get("pr_number"),
            "repository": pr_data.get("repository", {}).get("full_name"),
            "timestamp": datetime.utcnow().isoformat(),
            "overall_compliance": True,
            "compliance_score": 0.0,
            "policy_results": {},
            "violations": [],
            "warnings": [],
            "recommendations": [],
            "action_items": []
        }
        
        # Validate each policy
        policy_scores = []
        
        # 1. Branch naming validation
        branch_result = await self._validate_branch_naming(pr_data)
        validation_results["policy_results"]["branch_naming"] = branch_result
        policy_scores.append(branch_result["score"])
        
        # 2. Commit message validation
        commit_result = await self._validate_commit_messages(pr_data)
        validation_results["policy_results"]["commit_messages"] = commit_result
        policy_scores.append(commit_result["score"])
        
        # 3. PR size validation
        size_result = await self._validate_pr_size(pr_data, pr_files or [])
        validation_results["policy_results"]["pr_size"] = size_result
        policy_scores.append(size_result["score"])
        
        # 4. Required files validation
        files_result = await self._validate_required_files(pr_data, pr_files or [])
        validation_results["policy_results"]["required_files"] = files_result
        policy_scores.append(files_result["score"])
        
        # 5. Security requirements validation
        security_result = await self._validate_security_requirements(pr_data, pr_files or [])
        validation_results["policy_results"]["security"] = security_result
        policy_scores.append(security_result["score"])
        
        # 6. Testing requirements validation
        testing_result = await self._validate_testing_requirements(pr_data, pr_files or [])
        validation_results["policy_results"]["testing"] = testing_result
        policy_scores.append(testing_result["score"])
        
        # 7. Approval requirements validation
        approval_result = await self._validate_approval_requirements(pr_data)
        validation_results["policy_results"]["approvals"] = approval_result
        policy_scores.append(approval_result["score"])
        
        # Calculate overall compliance
        validation_results["compliance_score"] = sum(policy_scores) / len(policy_scores)
        validation_results["overall_compliance"] = validation_results["compliance_score"] >= 80.0
        
        # Collect all violations, warnings, and recommendations
        for policy_name, policy_result in validation_results["policy_results"].items():
            validation_results["violations"].extend(policy_result.get("violations", []))
            validation_results["warnings"].extend(policy_result.get("warnings", []))
            validation_results["recommendations"].extend(policy_result.get("recommendations", []))
        
        # Generate action items
        validation_results["action_items"] = self._generate_action_items(validation_results)
        
        logger.info(f"Governance validation completed with score {validation_results['compliance_score']}")
        return validation_results
    
    async def _validate_branch_naming(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate branch naming conventions."""
        policy = self._policy_rules["branch_naming"]
        if not policy["enabled"]:
            return {"score": 100.0, "compliant": True, "violations": [], "warnings": []}
        
        source_branch = pr_data.get("source_branch", "")
        target_branch = pr_data.get("target_branch", "")
        
        result = {
            "score": 100.0,
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check source branch naming
        valid_pattern = False
        for branch_type, pattern in policy["patterns"].items():
            if re.match(pattern, source_branch):
                valid_pattern = True
                break
        
        if not valid_pattern:
            result["violations"].append(
                f"Branch name '{source_branch}' does not follow naming conventions"
            )
            result["compliant"] = False
            result["score"] = 0.0
            result["recommendations"].append(
                "Use branch naming patterns: feature/, bugfix/, hotfix/, release/"
            )
        
        return result
    
    async def _validate_commit_messages(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate commit message conventions."""
        policy = self._policy_rules["commit_message"]
        if not policy["enabled"]:
            return {"score": 100.0, "compliant": True, "violations": [], "warnings": []}
        
        # Mock commit messages - in real implementation, would fetch from Git
        commits = pr_data.get("commits", [
            {"message": "feat: add new feature"},
            {"message": "fix: resolve bug PROJ-123"}
        ])
        
        result = {
            "score": 100.0,
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        violation_count = 0
        
        for commit in commits:
            message = commit.get("message", "").split('\n')[0]  # First line only
            
            # Check length
            if len(message) < policy["min_length"]:
                result["violations"].append(
                    f"Commit message too short: '{message}' (min {policy['min_length']} chars)"
                )
                violation_count += 1
            
            if len(message) > policy["max_length"]:
                result["violations"].append(
                    f"Commit message too long: '{message}' (max {policy['max_length']} chars)"
                )
                violation_count += 1
            
            # Check conventional commit format
            if not re.match(policy["patterns"]["conventional"], message):
                result["violations"].append(
                    f"Commit message doesn't follow conventional format: '{message}'"
                )
                violation_count += 1
        
        if violation_count > 0:
            result["compliant"] = False
            result["score"] = max(0, 100 - (violation_count * 20))
            result["recommendations"].append(
                "Use conventional commit format: type(scope): description"
            )
        
        return result
    
    async def _validate_pr_size(
        self, pr_data: Dict[str, Any], pr_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate pull request size limits."""
        policy = self._policy_rules["pr_size_limits"]
        if not policy["enabled"]:
            return {"score": 100.0, "compliant": True, "violations": [], "warnings": []}
        
        files_changed = len(pr_files)
        lines_changed = sum(
            file.get("additions", 0) + file.get("deletions", 0) 
            for file in pr_files
        )
        
        result = {
            "score": 100.0,
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": [],
            "metrics": {
                "files_changed": files_changed,
                "lines_changed": lines_changed,
                "max_files_allowed": policy["max_files_changed"],
                "max_lines_allowed": policy["max_lines_changed"]
            }
        }
        
        # Check file count limit
        if files_changed > policy["max_files_changed"]:
            result["violations"].append(
                f"Too many files changed: {files_changed} > {policy['max_files_changed']}"
            )
            result["compliant"] = False
            result["score"] -= 30
        
        # Check lines changed limit
        if lines_changed > policy["max_lines_changed"]:
            result["violations"].append(
                f"Too many lines changed: {lines_changed} > {policy['max_lines_changed']}"
            )
            result["compliant"] = False
            result["score"] -= 30
        
        # Warnings for large PRs
        if files_changed > policy["max_files_changed"] * 0.8:
            result["warnings"].append(
                f"Large PR detected: {files_changed} files changed"
            )
            result["recommendations"].append("Consider splitting into smaller PRs")
        
        result["score"] = max(0, result["score"])
        return result
    
    async def _validate_required_files(
        self, pr_data: Dict[str, Any], pr_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate required files are present."""
        policy = self._policy_rules["required_files"]
        if not policy["enabled"]:
            return {"score": 100.0, "compliant": True, "violations": [], "warnings": []}
        
        # Get list of files in the repository (mock implementation)
        repo_files = {file.get("filename", "") for file in pr_files}
        
        result = {
            "score": 100.0,
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check required files
        missing_files = []
        for required_file, description in policy["files"].items():
            if required_file not in repo_files:
                missing_files.append(required_file)
                result["violations"].append(f"Required file missing: {required_file}")
        
        if missing_files:
            result["compliant"] = False
            result["score"] = max(0, 100 - len(missing_files) * 20)
            result["recommendations"].append(f"Add missing files: {', '.join(missing_files)}")
        
        return result
    
    async def _validate_security_requirements(
        self, pr_data: Dict[str, Any], pr_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate security requirements."""
        policy = self._policy_rules["security_requirements"]
        if not policy["enabled"]:
            return {"score": 100.0, "compliant": True, "violations": [], "warnings": []}
        
        result = {
            "score": 100.0,
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check for forbidden patterns (secrets in code)
        for file in pr_files:
            file_content = file.get("patch", "")
            filename = file.get("filename", "")
            
            for pattern in policy["forbidden_patterns"]:
                if re.search(pattern, file_content, re.IGNORECASE):
                    result["violations"].append(
                        f"Potential secret detected in {filename}"
                    )
                    result["compliant"] = False
                    result["score"] -= 50  # Severe penalty for secrets
        
        # Mock check for security scans
        security_checks_passed = True  # Would check actual scan results
        
        if not security_checks_passed:
            result["violations"].append("Security scans not completed")
            result["compliant"] = False
            result["score"] -= 30
        
        if not result["compliant"]:
            result["recommendations"].append("Run security scans and remove any secrets")
        
        return result
    
    async def _validate_testing_requirements(
        self, pr_data: Dict[str, Any], pr_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate testing requirements."""
        policy = self._policy_rules["testing_requirements"]
        if not policy["enabled"]:
            return {"score": 100.0, "compliant": True, "violations": [], "warnings": []}
        
        result = {
            "score": 100.0,
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check for test files
        test_files = []
        code_files = []
        
        for file in pr_files:
            filename = file.get("filename", "")
            
            # Check if it's a test file
            is_test_file = any(
                re.search(pattern, filename) for pattern in policy["test_file_patterns"]
            )
            
            if is_test_file:
                test_files.append(filename)
            elif filename.endswith(('.py', '.js', '.ts', '.java', '.go')):
                code_files.append(filename)
        
        # Calculate test coverage ratio
        if code_files:
            test_ratio = len(test_files) / len(code_files)
            
            if test_ratio < 0.3:  # Should have at least 30% test files relative to code files
                result["warnings"].append(
                    f"Low test file coverage: {len(test_files)} test files for {len(code_files)} code files"
                )
                result["score"] -= 20
                result["recommendations"].append("Add more test files")
        
        # Mock test coverage check
        test_coverage = 85.0  # Would get from actual coverage reports
        
        if test_coverage < policy["min_test_coverage"]:
            result["violations"].append(
                f"Test coverage too low: {test_coverage}% < {policy['min_test_coverage']}%"
            )
            result["compliant"] = False
            result["score"] -= 30
        
        return result
    
    async def _validate_approval_requirements(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate approval requirements."""
        policy = self._policy_rules["approval_requirements"]
        if not policy["enabled"]:
            return {"score": 100.0, "compliant": True, "violations": [], "warnings": []}
        
        reviews = pr_data.get("reviews", [])
        approved_reviews = [r for r in reviews if r.get("status") == "approved"]
        
        result = {
            "score": 100.0,
            "compliant": True,
            "violations": [],
            "warnings": [],
            "recommendations": [],
            "metrics": {
                "total_reviews": len(reviews),
                "approved_reviews": len(approved_reviews),
                "min_required": policy["min_reviewers"]
            }
        }
        
        # Check minimum reviewers
        if len(approved_reviews) < policy["min_reviewers"]:
            result["violations"].append(
                f"Insufficient approvals: {len(approved_reviews)} < {policy['min_reviewers']}"
            )
            result["compliant"] = False
            result["score"] = (len(approved_reviews) / policy["min_reviewers"]) * 100
        
        # Check for required reviewer roles (mock)
        has_senior_approval = True  # Would check actual reviewer roles
        
        if not has_senior_approval:
            result["warnings"].append("No senior developer approval found")
            result["score"] -= 10
            result["recommendations"].append("Get approval from a senior developer")
        
        return result
    
    def _generate_action_items(self, validation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable items based on validation results."""
        action_items = []
        
        # High priority items from violations
        for violation in validation_results["violations"]:
            action_items.append({
                "priority": "high",
                "type": "violation",
                "description": violation,
                "required": True
            })
        
        # Medium priority items from recommendations
        for recommendation in validation_results["recommendations"]:
            action_items.append({
                "priority": "medium",
                "type": "recommendation",
                "description": recommendation,
                "required": False
            })
        
        # Low priority items from warnings
        for warning in validation_results["warnings"]:
            action_items.append({
                "priority": "low",
                "type": "warning",
                "description": warning,
                "required": False
            })
        
        return action_items
    
    async def generate_governance_report(self, repository: str, days: int = 30) -> Dict[str, Any]:
        """Generate governance compliance report for a repository."""
        # This would aggregate governance data over time
        # Mock implementation for now
        
        return {
            "repository": repository,
            "period_days": days,
            "overall_compliance_rate": 0.85,
            "policy_compliance": {
                "branch_naming": {"rate": 0.95, "violations": 2},
                "commit_messages": {"rate": 0.80, "violations": 8},
                "pr_size": {"rate": 0.90, "violations": 4},
                "security": {"rate": 0.98, "violations": 1},
                "testing": {"rate": 0.75, "violations": 10}
            },
            "trends": {
                "improving": ["security", "testing"],
                "declining": ["commit_messages"],
                "stable": ["branch_naming", "pr_size"]
            },
            "recommendations": [
                "Improve commit message conventions",
                "Increase test coverage requirements",
                "Implement automated policy validation"
            ]
        }
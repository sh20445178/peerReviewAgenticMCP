"""
Peer Review Engine for analyzing pull requests and enforcing governance policies.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio

from ..models import (
    ReviewSummary, ReviewMetrics, PullRequestResponse, ReviewResponse,
    GovernanceValidationResponse, ReviewStatus, PriorityLevel, CheckStatus
)
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class PeerReviewEngine:
    """Core engine for peer review analysis and governance enforcement."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize peer review engine."""
        self.db_manager = db_manager
        self._governance_rules = self._load_default_governance_rules()
        logger.info("Peer Review Engine initialized")
    
    def _load_default_governance_rules(self) -> Dict[str, Any]:
        """Load default governance rules."""
        return {
            "minimum_reviewers": {
                "required": True,
                "value": 2,
                "description": "Minimum number of required reviewers"
            },
            "required_labels": {
                "required": True,
                "value": ["code-review", "ready-for-review"],
                "description": "Required labels for PR review"
            },
            "blocked_labels": {
                "required": True,
                "value": ["wip", "do-not-merge", "draft"],
                "description": "Labels that block PR from being merged"
            },
            "automated_checks": {
                "required": True,
                "value": ["build", "tests", "code-quality"],
                "description": "Required automated checks that must pass"
            },
            "review_timeout_hours": {
                "required": False,
                "value": 48,
                "description": "Maximum hours to wait for review before escalation"
            },
            "code_coverage_threshold": {
                "required": False,
                "value": 80.0,
                "description": "Minimum code coverage percentage required"
            },
            "max_file_changes": {
                "required": False,
                "value": 50,
                "description": "Maximum number of files that can be changed in one PR"
            },
            "max_lines_changed": {
                "required": False,
                "value": 500,
                "description": "Maximum number of lines that can be changed in one PR"
            },
            "security_scan_required": {
                "required": True,
                "value": True,
                "description": "Security scanning must be completed"
            },
            "quality_gate_status": {
                "required": True,
                "value": "PASSED",
                "description": "SonarQube quality gate must pass"
            }
        }
    
    async def analyze_pull_request(self, pr_id: int) -> Dict[str, Any]:
        """Analyze a pull request for compliance and quality."""
        logger.info(f"Starting analysis for PR ID: {pr_id}")
        
        try:
            # Get PR details
            pr = await self._get_pull_request_with_details(pr_id)
            if not pr:
                raise ValueError(f"Pull request {pr_id} not found")
            
            # Perform various analyses
            analysis_results = {
                "pr_id": pr_id,
                "repository": pr["repository"]["full_name"],
                "pr_number": pr["pr_number"],
                "title": pr["title"],
                "author": pr["author"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 1. Review compliance analysis
            review_compliance = await self._analyze_review_compliance(pr)
            
            # 2. Automated checks analysis
            automated_checks = await self._analyze_automated_checks(pr_id)
            
            # 3. Code quality analysis
            code_quality = await self._analyze_code_quality(pr)
            
            # 4. Security compliance analysis
            security_compliance = await self._analyze_security_compliance(pr_id)
            
            # 5. Governance policy compliance
            governance_compliance = await self._analyze_governance_compliance(pr, pr_id)
            
            # Calculate overall compliance score
            compliance_score = self._calculate_compliance_score(
                review_compliance, automated_checks, code_quality,
                security_compliance, governance_compliance
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                pr, review_compliance, automated_checks, code_quality,
                security_compliance, governance_compliance
            )
            
            # Determine status and priority
            status, priority = self._determine_status_and_priority(
                compliance_score, review_compliance, automated_checks
            )
            
            analysis_results.update({
                "compliance_score": compliance_score,
                "status": status,
                "priority": priority,
                "review_compliance": review_compliance,
                "automated_checks": automated_checks,
                "code_quality": code_quality,
                "security_compliance": security_compliance,
                "governance_compliance": governance_compliance,
                "recommendations": recommendations,
                "analysis_summary": self._create_analysis_summary(
                    compliance_score, recommendations
                )
            })
            
            logger.info(f"Completed analysis for PR {pr_id} with score {compliance_score}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing PR {pr_id}: {str(e)}")
            return {
                "pr_id": pr_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_pull_request_with_details(self, pr_id: int) -> Optional[Dict[str, Any]]:
        """Get pull request with all related details."""
        # This would normally fetch from database with joins
        # For now, return a mock structure
        return {
            "id": pr_id,
            "pr_number": 123,
            "title": "Sample PR",
            "author": "developer",
            "repository": {"full_name": "org/repo"},
            "labels": ["feature", "ready-for-review"],
            "reviews": [],
            "automated_checks": [],
            "files_changed": 5,
            "lines_added": 150,
            "lines_deleted": 50
        }
    
    async def _analyze_review_compliance(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze review compliance for a pull request."""
        reviews = pr.get("reviews", [])
        
        # Count approved reviews
        approved_reviews = [r for r in reviews if r.get("status") == "approved"]
        changes_requested = [r for r in reviews if r.get("status") == "changes_requested"]
        
        min_reviewers = self._governance_rules["minimum_reviewers"]["value"]
        
        compliance = {
            "total_reviews": len(reviews),
            "approved_reviews": len(approved_reviews),
            "changes_requested": len(changes_requested),
            "min_reviewers_required": min_reviewers,
            "min_reviewers_met": len(approved_reviews) >= min_reviewers,
            "blocking_reviews": len(changes_requested) > 0,
            "compliance_score": 0.0,
            "issues": []
        }
        
        # Calculate review compliance score
        if len(approved_reviews) >= min_reviewers:
            compliance["compliance_score"] = 100.0
        elif len(approved_reviews) > 0:
            compliance["compliance_score"] = (len(approved_reviews) / min_reviewers) * 100.0
        
        # Check for issues
        if not compliance["min_reviewers_met"]:
            compliance["issues"].append(
                f"Needs {min_reviewers - len(approved_reviews)} more approving review(s)"
            )
        
        if compliance["blocking_reviews"]:
            compliance["issues"].append("Has reviews requesting changes")
        
        return compliance
    
    async def _analyze_automated_checks(self, pr_id: int) -> Dict[str, Any]:
        """Analyze automated checks for a pull request."""
        checks = await self.db_manager.get_checks_by_pull_request(pr_id)
        
        required_checks = self._governance_rules["automated_checks"]["value"]
        
        compliance = {
            "total_checks": len(checks),
            "passed_checks": 0,
            "failed_checks": 0,
            "pending_checks": 0,
            "required_checks": required_checks,
            "required_checks_passed": [],
            "required_checks_missing": [],
            "compliance_score": 0.0,
            "issues": []
        }
        
        # Analyze check results
        check_types_found = set()
        for check in checks:
            check_types_found.add(check.check_type)
            
            if check.status == CheckStatus.SUCCESS:
                compliance["passed_checks"] += 1
            elif check.status == CheckStatus.FAILURE:
                compliance["failed_checks"] += 1
            else:
                compliance["pending_checks"] += 1
        
        # Check required checks
        for required_check in required_checks:
            if required_check in check_types_found:
                # Find the specific check
                matching_checks = [c for c in checks if c.check_type == required_check]
                if any(c.status == CheckStatus.SUCCESS for c in matching_checks):
                    compliance["required_checks_passed"].append(required_check)
                else:
                    compliance["issues"].append(f"Required check '{required_check}' failed")
            else:
                compliance["required_checks_missing"].append(required_check)
                compliance["issues"].append(f"Required check '{required_check}' not found")
        
        # Calculate compliance score
        if len(compliance["required_checks_passed"]) == len(required_checks):
            compliance["compliance_score"] = 100.0
        else:
            compliance["compliance_score"] = (
                len(compliance["required_checks_passed"]) / len(required_checks)
            ) * 100.0
        
        return compliance
    
    async def _analyze_code_quality(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code quality metrics."""
        # This would integrate with SonarQube results
        # For now, return mock analysis
        
        files_changed = pr.get("files_changed", 0)
        lines_changed = pr.get("lines_added", 0) + pr.get("lines_deleted", 0)
        
        max_files = self._governance_rules["max_file_changes"]["value"]
        max_lines = self._governance_rules["max_lines_changed"]["value"]
        
        compliance = {
            "files_changed": files_changed,
            "lines_changed": lines_changed,
            "max_files_allowed": max_files,
            "max_lines_allowed": max_lines,
            "size_compliance": files_changed <= max_files and lines_changed <= max_lines,
            "code_coverage": 85.0,  # Mock value
            "coverage_threshold": self._governance_rules["code_coverage_threshold"]["value"],
            "coverage_compliance": True,  # Mock
            "quality_gate_status": "PASSED",  # Mock
            "compliance_score": 90.0,  # Mock
            "issues": []
        }
        
        if not compliance["size_compliance"]:
            if files_changed > max_files:
                compliance["issues"].append(f"Too many files changed ({files_changed} > {max_files})")
            if lines_changed > max_lines:
                compliance["issues"].append(f"Too many lines changed ({lines_changed} > {max_lines})")
        
        if compliance["code_coverage"] < compliance["coverage_threshold"]:
            compliance["issues"].append(
                f"Code coverage too low ({compliance['code_coverage']}% < {compliance['coverage_threshold']}%)"
            )
            compliance["coverage_compliance"] = False
        
        return compliance
    
    async def _analyze_security_compliance(self, pr_id: int) -> Dict[str, Any]:
        """Analyze security compliance."""
        # This would integrate with security scanning tools
        # For now, return mock analysis
        
        return {
            "security_scan_completed": True,
            "vulnerabilities_found": 0,
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 0,
            "compliance_score": 100.0,
            "issues": []
        }
    
    async def _analyze_governance_compliance(
        self, pr: Dict[str, Any], pr_id: int
    ) -> Dict[str, Any]:
        """Analyze governance policy compliance."""
        labels = pr.get("labels", [])
        
        required_labels = self._governance_rules["required_labels"]["value"]
        blocked_labels = self._governance_rules["blocked_labels"]["value"]
        
        compliance = {
            "required_labels_present": [],
            "required_labels_missing": [],
            "blocked_labels_present": [],
            "labels_compliance": True,
            "policy_violations": [],
            "compliance_score": 100.0,
            "issues": []
        }
        
        # Check required labels
        for required_label in required_labels:
            if required_label in labels:
                compliance["required_labels_present"].append(required_label)
            else:
                compliance["required_labels_missing"].append(required_label)
                compliance["issues"].append(f"Missing required label: {required_label}")
                compliance["labels_compliance"] = False
        
        # Check blocked labels
        for blocked_label in blocked_labels:
            if blocked_label in labels:
                compliance["blocked_labels_present"].append(blocked_label)
                compliance["issues"].append(f"Blocked label present: {blocked_label}")
                compliance["labels_compliance"] = False
        
        # Calculate compliance score
        if not compliance["labels_compliance"]:
            compliance["compliance_score"] = 0.0
        
        return compliance
    
    def _calculate_compliance_score(
        self, review_compliance: Dict, automated_checks: Dict,
        code_quality: Dict, security_compliance: Dict,
        governance_compliance: Dict
    ) -> float:
        """Calculate overall compliance score."""
        weights = {
            "review": 0.25,
            "automated": 0.25,
            "quality": 0.20,
            "security": 0.15,
            "governance": 0.15
        }
        
        score = (
            review_compliance["compliance_score"] * weights["review"] +
            automated_checks["compliance_score"] * weights["automated"] +
            code_quality["compliance_score"] * weights["quality"] +
            security_compliance["compliance_score"] * weights["security"] +
            governance_compliance["compliance_score"] * weights["governance"]
        )
        
        return round(score, 2)
    
    def _generate_recommendations(
        self, pr: Dict, review_compliance: Dict, automated_checks: Dict,
        code_quality: Dict, security_compliance: Dict, governance_compliance: Dict
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Review recommendations
        for issue in review_compliance.get("issues", []):
            recommendations.append(f"Review: {issue}")
        
        # Automated check recommendations
        for issue in automated_checks.get("issues", []):
            recommendations.append(f"Automated Checks: {issue}")
        
        # Code quality recommendations
        for issue in code_quality.get("issues", []):
            recommendations.append(f"Code Quality: {issue}")
        
        # Security recommendations
        for issue in security_compliance.get("issues", []):
            recommendations.append(f"Security: {issue}")
        
        # Governance recommendations
        for issue in governance_compliance.get("issues", []):
            recommendations.append(f"Governance: {issue}")
        
        # Add general recommendations if no specific issues
        if not recommendations:
            recommendations.append("All compliance checks passed - ready for merge!")
        
        return recommendations
    
    def _determine_status_and_priority(
        self, compliance_score: float, review_compliance: Dict, automated_checks: Dict
    ) -> tuple[ReviewStatus, PriorityLevel]:
        """Determine PR status and priority based on analysis."""
        # Determine status
        if compliance_score >= 90:
            status = ReviewStatus.APPROVED
        elif compliance_score >= 70:
            if review_compliance.get("blocking_reviews", False):
                status = ReviewStatus.CHANGES_REQUESTED
            else:
                status = ReviewStatus.IN_PROGRESS
        else:
            status = ReviewStatus.CHANGES_REQUESTED
        
        # Determine priority
        if compliance_score < 50:
            priority = PriorityLevel.CRITICAL
        elif compliance_score < 70:
            priority = PriorityLevel.HIGH
        elif compliance_score < 85:
            priority = PriorityLevel.MEDIUM
        else:
            priority = PriorityLevel.LOW
        
        return status, priority
    
    def _create_analysis_summary(
        self, compliance_score: float, recommendations: List[str]
    ) -> str:
        """Create a human-readable analysis summary."""
        if compliance_score >= 90:
            summary = "✅ Excellent! This PR meets all governance standards and is ready for merge."
        elif compliance_score >= 70:
            summary = "⚠️ Good progress, but some improvements are needed before merge."
        elif compliance_score >= 50:
            summary = "❌ Several issues need to be addressed before this PR can be approved."
        else:
            summary = "🚨 Critical issues found. Significant changes required."
        
        if recommendations:
            summary += f"\n\nKey actions: {len(recommendations)} recommendation(s) to address."
        
        return summary
    
    async def get_review_summary(
        self, repository: str, pr_number: int
    ) -> ReviewSummary:
        """Get a summary of the review status."""
        pr = await self.db_manager.get_pull_request_by_repo_and_number(repository, pr_number)
        if not pr:
            raise ValueError(f"PR {pr_number} not found in {repository}")
        
        reviews = await self.db_manager.get_reviews_by_pull_request(pr.id)
        checks = await self.db_manager.get_checks_by_pull_request(pr.id)
        
        # Mock analysis for now
        compliance_score = 85.0
        recommendations = ["Increase test coverage", "Fix SonarQube issues"]
        
        return ReviewSummary(
            pull_request_id=pr.id,
            pr_number=pr.pr_number,
            title=pr.title,
            author=pr.author,
            status=ReviewStatus(pr.status),
            priority=PriorityLevel(pr.priority),
            reviews_count=len(reviews),
            automated_checks_passed=len([c for c in checks if c.status == "success"]),
            automated_checks_total=len(checks),
            compliance_score=compliance_score,
            recommendations=recommendations
        )
    
    async def validate_governance(
        self, repository: str, pr_number: int
    ) -> GovernanceValidationResponse:
        """Validate governance policies for a PR."""
        pr = await self.db_manager.get_pull_request_by_repo_and_number(repository, pr_number)
        if not pr:
            raise ValueError(f"PR {pr_number} not found in {repository}")
        
        # Perform governance validation
        validation_data = {
            "pull_request_id": pr.id,
            "validation_type": "comprehensive",
            "is_compliant": True,  # Mock
            "violations": [],
            "recommendations": ["All governance policies met"]
        }
        
        return await self.db_manager.create_governance_validation(validation_data)
    
    async def get_repository_metrics(
        self, repository: str, days: int = 30
    ) -> ReviewMetrics:
        """Get review metrics for a repository."""
        repo = await self.db_manager.get_repository_by_full_name(repository)
        if not repo:
            raise ValueError(f"Repository {repository} not found")
        
        metrics_data = await self.db_manager.get_repository_metrics(repo.id, days)
        
        return ReviewMetrics(
            total_pull_requests=metrics_data["total_pull_requests"],
            avg_review_time_hours=metrics_data["avg_review_time_hours"],
            compliance_rate=metrics_data["compliance_rate"],
            automation_success_rate=metrics_data["automation_success_rate"],
            top_violation_types=metrics_data["top_violation_types"]
        )
    
    async def update_review_criteria(
        self, repository: str, criteria_name: str, criteria_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update review criteria for a repository."""
        repo = await self.db_manager.get_repository_by_full_name(repository)
        if not repo:
            raise ValueError(f"Repository {repository} not found")
        
        # Find existing criteria
        criteria_list = await self.db_manager.get_review_criteria_by_repository(repo.id)
        existing_criteria = next(
            (c for c in criteria_list if c.name == criteria_name), None
        )
        
        if existing_criteria:
            # Update existing criteria
            updated = await self.db_manager.update_review_criteria(
                existing_criteria.id, criteria_rules
            )
            return {"status": "updated", "criteria": updated.model_dump()}
        else:
            # Create new criteria
            criteria_data = {
                "repository_id": repo.id,
                "name": criteria_name,
                "description": f"Custom criteria: {criteria_name}",
                "criteria_type": "custom",
                "rules": criteria_rules,
                "is_required": True,
                "weight": 1
            }
            
            new_criteria = await self.db_manager.create_review_criteria(criteria_data)
            return {"status": "created", "criteria": new_criteria.model_dump()}
    
    async def get_global_metrics(self) -> ReviewMetrics:
        """Get global review metrics across all repositories."""
        # Mock implementation
        return ReviewMetrics(
            total_pull_requests=150,
            avg_review_time_hours=24.5,
            compliance_rate=0.85,
            automation_success_rate=0.92,
            top_violation_types=[
                {"type": "Missing tests", "count": 25},
                {"type": "Code coverage low", "count": 18},
                {"type": "Security issues", "count": 12}
            ]
        )
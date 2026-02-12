"""
Jira integration for issue tracking and project management.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from jira import JIRA, JIRAError

from ..config import JiraConfig
from ..models import ReviewSummary, PriorityLevel

logger = logging.getLogger(__name__)


class JiraIntegration:
    """Jira integration for issue tracking and project management."""
    
    def __init__(self, config: JiraConfig):
        """Initialize Jira integration."""
        self.config = config
        self.jira = None
        
        if not config.url or not config.username or not config.api_token:
            logger.warning("Jira configuration incomplete")
            return
        
        try:
            self.jira = JIRA(
                server=config.url,
                basic_auth=(config.username, config.api_token)
            )
            
            # Test connection
            self.jira.myself()
            logger.info("Jira integration initialized successfully")
            
        except JIRAError as e:
            logger.error(f"Failed to initialize Jira integration: {str(e)}")
            self.jira = None
        except Exception as e:
            logger.error(f"Unexpected error initializing Jira: {str(e)}")
            self.jira = None
    
    def is_enabled(self) -> bool:
        """Check if Jira integration is enabled and working."""
        return self.jira is not None
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get list of available Jira projects."""
        if not self.jira:
            return []
        
        try:
            projects = self.jira.projects()
            
            return [
                {
                    "id": project.id,
                    "key": project.key,
                    "name": project.name,
                    "description": getattr(project, 'description', ''),
                    "lead": getattr(project, 'lead', {}).get('displayName', ''),
                    "projectTypeKey": getattr(project, 'projectTypeKey', ''),
                    "url": getattr(project, 'self', '')
                }
                for project in projects
            ]
        except JIRAError as e:
            logger.error(f"Error fetching Jira projects: {str(e)}")
            return []
    
    async def get_issue_types(self, project_key: str) -> List[Dict[str, Any]]:
        """Get available issue types for a project."""
        if not self.jira:
            return []
        
        try:
            project = self.jira.project(project_key)
            issue_types = self.jira.issue_types_for_project(project.id)
            
            return [
                {
                    "id": issue_type.id,
                    "name": issue_type.name,
                    "description": getattr(issue_type, 'description', ''),
                    "subtask": getattr(issue_type, 'subtask', False),
                    "iconUrl": getattr(issue_type, 'iconUrl', '')
                }
                for issue_type in issue_types
            ]
        except JIRAError as e:
            logger.error(f"Error fetching issue types for project {project_key}: {str(e)}")
            return []
    
    async def create_issue_for_review(
        self, repository: str, pr_number: int, review_summary: ReviewSummary,
        issue_type: str = "Task", priority: str = "Medium",
        project_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a Jira issue for a peer review."""
        if not self.jira:
            return None
        
        # Determine project key
        if not project_key:
            # Try to infer project key from repository name
            project_key = repository.split('/')[-1].upper()[:10]
        
        try:
            # Prepare issue summary and description
            summary = f"Code Review: {repository} PR #{pr_number} - {review_summary.title}"
            
            description = self._create_review_issue_description(
                repository, pr_number, review_summary
            )
            
            # Map priority levels
            priority_mapping = {
                "low": "Low",
                "medium": "Medium", 
                "high": "High",
                "critical": "Highest"
            }
            jira_priority = priority_mapping.get(priority.lower(), "Medium")
            
            # Create issue
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
                'priority': {'name': jira_priority},
                'labels': ['code-review', 'peer-review', f'repo-{repository.replace("/", "-")}'],
                'components': [],
                'customfield_10000': f"PR #{pr_number}",  # May need adjustment based on Jira setup
            }
            
            # Add additional fields based on review summary
            if review_summary.compliance_score < 70:
                issue_dict['labels'].append('compliance-issue')
            
            if review_summary.automated_checks_passed < review_summary.automated_checks_total:
                issue_dict['labels'].append('automated-checks-failed')
            
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            # Create subtasks for specific recommendations
            await self._create_recommendation_subtasks(new_issue, review_summary.recommendations)
            
            logger.info(f"Created Jira issue {new_issue.key} for PR {pr_number}")
            
            return {
                "key": new_issue.key,
                "id": new_issue.id,
                "summary": new_issue.fields.summary,
                "status": new_issue.fields.status.name,
                "priority": new_issue.fields.priority.name,
                "url": f"{self.config.url}/browse/{new_issue.key}",
                "created": new_issue.fields.created
            }
            
        except JIRAError as e:
            logger.error(f"Error creating Jira issue: {str(e)}")
            return None
    
    def _create_review_issue_description(
        self, repository: str, pr_number: int, review_summary: ReviewSummary
    ) -> str:
        """Create detailed description for review issue."""
        description_parts = [
            f"*Pull Request Review Summary*",
            f"",
            f"*Repository:* {repository}",
            f"*Pull Request:* #{pr_number} - {review_summary.title}",
            f"*Author:* {review_summary.author}",
            f"*Status:* {review_summary.status}",
            f"*Priority:* {review_summary.priority}",
            f"",
            f"*Review Metrics:*",
            f"• Reviews Completed: {review_summary.reviews_count}",
            f"• Automated Checks: {review_summary.automated_checks_passed}/{review_summary.automated_checks_total}",
            f"• Compliance Score: {review_summary.compliance_score}%",
            f"",
            f"*Recommendations:*"
        ]
        
        if review_summary.recommendations:
            for i, recommendation in enumerate(review_summary.recommendations, 1):
                description_parts.append(f"{i}. {recommendation}")
        else:
            description_parts.append("No specific recommendations at this time.")
        
        description_parts.extend([
            f"",
            f"*Action Items:*",
            f"• Review and address all recommendations",
            f"• Ensure all automated checks pass",
            f"• Obtain required approvals",
            f"• Update documentation if needed",
            f"",
            f"_This issue was automatically created by the Peer Review MCP Server._"
        ])
        
        return "\n".join(description_parts)
    
    async def _create_recommendation_subtasks(
        self, parent_issue, recommendations: List[str]
    ) -> List[Dict[str, Any]]:
        """Create subtasks for specific recommendations."""
        if not recommendations or not self.jira:
            return []
        
        subtasks = []
        
        try:
            for i, recommendation in enumerate(recommendations[:5], 1):  # Limit to 5 subtasks
                subtask_dict = {
                    'project': {'key': parent_issue.fields.project.key},
                    'summary': f"Recommendation {i}: {recommendation[:100]}{'...' if len(recommendation) > 100 else ''}",
                    'description': recommendation,
                    'issuetype': {'name': 'Sub-task'},
                    'parent': {'key': parent_issue.key}
                }
                
                subtask = self.jira.create_issue(fields=subtask_dict)
                
                subtasks.append({
                    "key": subtask.key,
                    "summary": subtask.fields.summary,
                    "status": subtask.fields.status.name
                })
                
        except JIRAError as e:
            logger.error(f"Error creating subtasks: {str(e)}")
        
        return subtasks
    
    async def update_issue_status(
        self, issue_key: str, status: str, comment: Optional[str] = None
    ) -> bool:
        """Update Jira issue status."""
        if not self.jira:
            return False
        
        try:
            issue = self.jira.issue(issue_key)
            
            # Get available transitions
            transitions = self.jira.transitions(issue)
            
            # Find the transition that moves to the desired status
            transition_id = None
            for transition in transitions:
                if transition['to']['name'].lower() == status.lower():
                    transition_id = transition['id']
                    break
            
            if transition_id:
                self.jira.transition_issue(issue, transition_id)
                
                if comment:
                    self.jira.add_comment(issue, comment)
                
                logger.info(f"Updated issue {issue_key} status to {status}")
                return True
            else:
                logger.warning(f"No transition found to status '{status}' for issue {issue_key}")
                return False
                
        except JIRAError as e:
            logger.error(f"Error updating issue {issue_key}: {str(e)}")
            return False
    
    async def add_comment_to_issue(
        self, issue_key: str, comment: str, author: Optional[str] = None
    ) -> bool:
        """Add comment to a Jira issue."""
        if not self.jira:
            return False
        
        try:
            issue = self.jira.issue(issue_key)
            
            if author:
                comment = f"*Comment from {author}:*\n\n{comment}"
            
            self.jira.add_comment(issue, comment)
            logger.info(f"Added comment to issue {issue_key}")
            return True
            
        except JIRAError as e:
            logger.error(f"Error adding comment to issue {issue_key}: {str(e)}")
            return False
    
    async def create_code_quality_issue(
        self, repository: str, sonarqube_analysis: Dict[str, Any],
        project_key: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create Jira issue for SonarQube code quality findings."""
        if not self.jira:
            return None
        
        if not project_key:
            project_key = repository.split('/')[-1].upper()[:10]
        
        try:
            quality_score = sonarqube_analysis.get('quality_score', 0)
            issues_summary = sonarqube_analysis.get('issues_summary', {})
            recommendations = sonarqube_analysis.get('recommendations', [])
            
            # Determine priority based on quality score and issues
            if quality_score < 50 or issues_summary.get('by_severity', {}).get('BLOCKER', 0) > 0:
                priority = "Highest"
            elif quality_score < 70 or issues_summary.get('by_severity', {}).get('CRITICAL', 0) > 0:
                priority = "High"
            elif quality_score < 85:
                priority = "Medium"
            else:
                priority = "Low"
            
            summary = f"Code Quality: {repository} - Quality Score {quality_score}%"
            
            description = self._create_quality_issue_description(repository, sonarqube_analysis)
            
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Bug'},
                'priority': {'name': priority},
                'labels': ['code-quality', 'sonarqube', f'repo-{repository.replace("/", "-")}'],
            }
            
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            logger.info(f"Created code quality issue {new_issue.key}")
            
            return {
                "key": new_issue.key,
                "id": new_issue.id,
                "summary": new_issue.fields.summary,
                "status": new_issue.fields.status.name,
                "priority": new_issue.fields.priority.name,
                "url": f"{self.config.url}/browse/{new_issue.key}"
            }
            
        except JIRAError as e:
            logger.error(f"Error creating code quality issue: {str(e)}")
            return None
    
    def _create_quality_issue_description(
        self, repository: str, sonarqube_analysis: Dict[str, Any]
    ) -> str:
        """Create description for code quality issue."""
        quality_score = sonarqube_analysis.get('quality_score', 0)
        measures = sonarqube_analysis.get('measures', {})
        issues_summary = sonarqube_analysis.get('issues_summary', {})
        recommendations = sonarqube_analysis.get('recommendations', [])
        sonarqube_url = sonarqube_analysis.get('sonarqube_url', '')
        
        description_parts = [
            f"*Code Quality Analysis Report*",
            f"",
            f"*Repository:* {repository}",
            f"*Quality Score:* {quality_score}%",
            f"*Analysis Date:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"",
            f"*Key Metrics:*",
            f"• Lines of Code: {measures.get('ncloc', 'N/A')}",
            f"• Coverage: {measures.get('coverage', 'N/A')}%",
            f"• Duplicated Lines: {measures.get('duplicated_lines_density', 'N/A')}%",
            f"• Bugs: {measures.get('bugs', 'N/A')}",
            f"• Vulnerabilities: {measures.get('vulnerabilities', 'N/A')}",
            f"• Code Smells: {measures.get('code_smells', 'N/A')}",
            f"",
            f"*Issue Breakdown by Severity:*"
        ]
        
        by_severity = issues_summary.get('by_severity', {})
        for severity, count in by_severity.items():
            if count > 0:
                description_parts.append(f"• {severity}: {count}")
        
        if recommendations:
            description_parts.extend([
                f"",
                f"*Recommendations:*"
            ])
            for i, recommendation in enumerate(recommendations, 1):
                description_parts.append(f"{i}. {recommendation}")
        
        if sonarqube_url:
            description_parts.extend([
                f"",
                f"*SonarQube Report:* [{sonarqube_url}|{sonarqube_url}]"
            ])
        
        description_parts.extend([
            f"",
            f"*Action Required:*",
            f"• Review and fix critical and high-priority issues",
            f"• Improve test coverage if below 80%",
            f"• Reduce code duplication",
            f"• Address security vulnerabilities immediately",
            f"",
            f"_This issue was automatically created from SonarQube analysis._"
        ])
        
        return "\n".join(description_parts)
    
    async def search_issues(
        self, jql: str, max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for Jira issues using JQL."""
        if not self.jira:
            return []
        
        try:
            issues = self.jira.search_issues(jql, maxResults=max_results)
            
            return [
                {
                    "key": issue.key,
                    "id": issue.id,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "priority": issue.fields.priority.name if issue.fields.priority else 'None',
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                    "created": issue.fields.created,
                    "updated": issue.fields.updated,
                    "url": f"{self.config.url}/browse/{issue.key}"
                }
                for issue in issues
            ]
            
        except JIRAError as e:
            logger.error(f"Error searching issues with JQL '{jql}': {str(e)}")
            return []
    
    async def get_issue_details(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a Jira issue."""
        if not self.jira:
            return None
        
        try:
            issue = self.jira.issue(issue_key)
            
            return {
                "key": issue.key,
                "id": issue.id,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "priority": issue.fields.priority.name if issue.fields.priority else 'None',
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "labels": issue.fields.labels,
                "components": [comp.name for comp in issue.fields.components],
                "url": f"{self.config.url}/browse/{issue.key}"
            }
            
        except JIRAError as e:
            logger.error(f"Error getting issue details for {issue_key}: {str(e)}")
            return None
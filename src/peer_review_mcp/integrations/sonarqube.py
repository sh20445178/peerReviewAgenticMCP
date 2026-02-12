"""
SonarQube integration for code quality analysis and metrics.
"""

import logging
import base64
from typing import Dict, List, Optional, Any
import aiohttp
import asyncio
from datetime import datetime

from ..config import SonarQubeConfig

logger = logging.getLogger(__name__)


class SonarQubeIntegration:
    """SonarQube integration for code quality analysis."""
    
    def __init__(self, config: SonarQubeConfig):
        """Initialize SonarQube integration."""
        self.config = config
        self.base_url = config.url.rstrip('/') if config.url else None
        self.session = None
        
        if not self.base_url:
            logger.warning("SonarQube URL not configured")
            return
        
        # Prepare authentication
        self.auth = None
        if config.token:
            # Token-based authentication
            self.auth = aiohttp.BasicAuth(config.token, '')
        elif config.username and config.password:
            # Username/password authentication
            self.auth = aiohttp.BasicAuth(config.username, config.password)
        else:
            logger.warning("SonarQube authentication not configured")
        
        logger.info("SonarQube integration initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(auth=self.auth)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self, method: str, endpoint: str, params: Optional[Dict] = None, 
        data: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to SonarQube API."""
        if not self.base_url or not self.auth:
            return None
        
        url = f"{self.base_url}/api/{endpoint}"
        
        async with aiohttp.ClientSession(auth=self.auth) as session:
            try:
                async with session.request(
                    method, url, params=params, json=data
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"SonarQube API error: {response.status} - {await response.text()}")
                        return None
            except Exception as e:
                logger.error(f"Error making request to SonarQube: {str(e)}")
                return None
    
    async def get_project_info(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Get project information from SonarQube."""
        response = await self._make_request(
            'GET', 
            'projects/search',
            params={'projects': project_key}
        )
        
        if response and response.get('components'):
            project = response['components'][0]
            return {
                "key": project.get("key"),
                "name": project.get("name"),
                "qualifier": project.get("qualifier"),
                "lastAnalysisDate": project.get("lastAnalysisDate"),
                "visibility": project.get("visibility")
            }
        
        return None
    
    async def get_project_measures(
        self, project_key: str, metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Get project measures from SonarQube."""
        if not metrics:
            metrics = [
                'bugs', 'vulnerabilities', 'code_smells', 'coverage',
                'duplicated_lines_density', 'ncloc', 'sqale_rating',
                'reliability_rating', 'security_rating', 'alert_status',
                'quality_gate_status'
            ]
        
        response = await self._make_request(
            'GET',
            'measures/component',
            params={
                'component': project_key,
                'metricKeys': ','.join(metrics)
            }
        )
        
        if not response or not response.get('component'):
            return {}
        
        measures = {}
        for measure in response['component'].get('measures', []):
            metric_key = measure.get('metric')
            value = measure.get('value')
            
            # Convert string values to appropriate types
            if metric_key in ['bugs', 'vulnerabilities', 'code_smells', 'ncloc']:
                measures[metric_key] = int(value) if value else 0
            elif metric_key in ['coverage', 'duplicated_lines_density']:
                measures[metric_key] = float(value) if value else 0.0
            else:
                measures[metric_key] = value
        
        return measures
    
    async def get_project_issues(
        self, project_key: str, severity: Optional[str] = None,
        types: Optional[List[str]] = None, statuses: Optional[List[str]] = None,
        page_size: int = 500
    ) -> List[Dict[str, Any]]:
        """Get project issues from SonarQube."""
        params = {
            'componentKeys': project_key,
            'ps': page_size,
            'p': 1
        }
        
        if severity:
            params['severities'] = severity
        if types:
            params['types'] = ','.join(types)
        if statuses:
            params['statuses'] = ','.join(statuses)
        
        response = await self._make_request('GET', 'issues/search', params=params)
        
        if not response:
            return []
        
        issues = []
        for issue in response.get('issues', []):
            issues.append({
                "key": issue.get("key"),
                "rule": issue.get("rule"),
                "severity": issue.get("severity"),
                "component": issue.get("component"),
                "line": issue.get("line"),
                "message": issue.get("message"),
                "type": issue.get("type"),
                "status": issue.get("status"),
                "author": issue.get("author"),
                "creationDate": issue.get("creationDate"),
                "updateDate": issue.get("updateDate"),
                "tags": issue.get("tags", []),
                "effort": issue.get("effort"),
                "debt": issue.get("debt")
            })
        
        return issues
    
    async def get_quality_gate_status(self, project_key: str) -> Optional[Dict[str, Any]]:
        """Get quality gate status for a project."""
        response = await self._make_request(
            'GET',
            'qualitygates/project_status',
            params={'projectKey': project_key}
        )
        
        if response and response.get('projectStatus'):
            status = response['projectStatus']
            return {
                "status": status.get("status"),
                "conditions": [
                    {
                        "status": condition.get("status"),
                        "metricKey": condition.get("metricKey"),
                        "actualValue": condition.get("actualValue"),
                        "errorThreshold": condition.get("errorThreshold"),
                        "warningThreshold": condition.get("warningThreshold"),
                        "comparator": condition.get("comparator")
                    }
                    for condition in status.get("conditions", [])
                ]
            }
        
        return None
    
    async def get_project_branches(self, project_key: str) -> List[Dict[str, Any]]:
        """Get project branches from SonarQube."""
        response = await self._make_request(
            'GET',
            'project_branches/list',
            params={'project': project_key}
        )
        
        if response and response.get('branches'):
            return [
                {
                    "name": branch.get("name"),
                    "isMain": branch.get("isMain", False),
                    "lastActivityDate": branch.get("lastActivityDate"),
                    "status": branch.get("status", {})
                }
                for branch in response['branches']
            ]
        
        return []
    
    async def analyze_pull_request(
        self, repository: str, pr_number: int, branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a pull request using SonarQube."""
        # Convert repository name to project key (simple conversion)
        project_key = repository.replace('/', '_').replace('-', '_')
        
        logger.info(f"Analyzing PR {pr_number} for project {project_key}")
        
        # Get project info first
        project_info = await self.get_project_info(project_key)
        if not project_info:
            return {
                "status": "error",
                "message": f"Project {project_key} not found in SonarQube",
                "project_key": project_key
            }
        
        # Get measures
        measures = await self.get_project_measures(project_key)
        
        # Get issues
        issues = await self.get_project_issues(
            project_key,
            types=['BUG', 'VULNERABILITY', 'CODE_SMELL']
        )
        
        # Get quality gate status
        quality_gate = await self.get_quality_gate_status(project_key)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(measures, quality_gate)
        
        # Categorize issues by severity
        issue_summary = self._summarize_issues(issues)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(measures, issues, quality_gate)
        
        analysis_result = {
            "status": "completed",
            "project_key": project_key,
            "repository": repository,
            "pr_number": pr_number,
            "timestamp": datetime.utcnow().isoformat(),
            "quality_score": quality_score,
            "measures": measures,
            "quality_gate": quality_gate,
            "issues_summary": issue_summary,
            "total_issues": len(issues),
            "recommendations": recommendations,
            "sonarqube_url": f"{self.base_url}/dashboard?id={project_key}"
        }
        
        return analysis_result
    
    def _calculate_quality_score(
        self, measures: Dict[str, Any], quality_gate: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate overall quality score based on measures and quality gate."""
        score = 100.0
        
        # Deduct points for bugs, vulnerabilities, code smells
        bugs = measures.get('bugs', 0)
        vulnerabilities = measures.get('vulnerabilities', 0)
        code_smells = measures.get('code_smells', 0)
        
        # Severe deductions for critical issues
        score -= bugs * 5
        score -= vulnerabilities * 10
        score -= code_smells * 1
        
        # Deduct points for low coverage
        coverage = measures.get('coverage', 0)
        if coverage < 80:
            score -= (80 - coverage) * 0.5
        
        # Deduct points for high duplication
        duplication = measures.get('duplicated_lines_density', 0)
        if duplication > 5:
            score -= (duplication - 5) * 2
        
        # Quality gate status
        if quality_gate and quality_gate.get('status') == 'ERROR':
            score -= 20
        elif quality_gate and quality_gate.get('status') == 'WARNING':
            score -= 10
        
        return max(0.0, min(100.0, score))
    
    def _summarize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize issues by type and severity."""
        summary = {
            "by_type": {"BUG": 0, "VULNERABILITY": 0, "CODE_SMELL": 0},
            "by_severity": {
                "BLOCKER": 0, "CRITICAL": 0, "MAJOR": 0, "MINOR": 0, "INFO": 0
            },
            "by_status": {},
            "new_issues": 0
        }
        
        for issue in issues:
            issue_type = issue.get("type", "UNKNOWN")
            severity = issue.get("severity", "INFO")
            status = issue.get("status", "OPEN")
            
            if issue_type in summary["by_type"]:
                summary["by_type"][issue_type] += 1
            
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1
            
            if status in summary["by_status"]:
                summary["by_status"][status] += 1
            else:
                summary["by_status"][status] = 1
            
            # Count new issues (created recently)
            creation_date = issue.get("creationDate")
            if creation_date:
                # Simple check - could be made more sophisticated
                summary["new_issues"] += 1
        
        return summary
    
    def _generate_recommendations(
        self, measures: Dict[str, Any], issues: List[Dict[str, Any]],
        quality_gate: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Coverage recommendations
        coverage = measures.get('coverage', 0)
        if coverage < 80:
            recommendations.append(
                f"Increase test coverage from {coverage}% to at least 80%"
            )
        
        # Duplication recommendations
        duplication = measures.get('duplicated_lines_density', 0)
        if duplication > 5:
            recommendations.append(
                f"Reduce code duplication from {duplication}% to below 5%"
            )
        
        # Issue-specific recommendations
        bugs = measures.get('bugs', 0)
        if bugs > 0:
            recommendations.append(f"Fix {bugs} bug(s) identified by SonarQube")
        
        vulnerabilities = measures.get('vulnerabilities', 0)
        if vulnerabilities > 0:
            recommendations.append(
                f"Address {vulnerabilities} security vulnerability(-ies)"
            )
        
        # Critical and blocker issues
        critical_issues = [i for i in issues if i.get('severity') in ['BLOCKER', 'CRITICAL']]
        if critical_issues:
            recommendations.append(
                f"Immediately address {len(critical_issues)} critical/blocker issue(s)"
            )
        
        # Code smells
        code_smells = measures.get('code_smells', 0)
        if code_smells > 10:
            recommendations.append(
                f"Consider refactoring to reduce {code_smells} code smell(s)"
            )
        
        # Quality gate recommendations
        if quality_gate and quality_gate.get('status') == 'ERROR':
            recommendations.append("Quality gate is failing - review all failed conditions")
            
            for condition in quality_gate.get('conditions', []):
                if condition.get('status') == 'ERROR':
                    metric = condition.get('metricKey')
                    actual = condition.get('actualValue')
                    threshold = condition.get('errorThreshold')
                    recommendations.append(
                        f"Fix {metric}: current value {actual} exceeds threshold {threshold}"
                    )
        
        if not recommendations:
            recommendations.append("Code quality looks good! Keep up the excellent work.")
        
        return recommendations
    
    async def create_project(self, project_key: str, project_name: str) -> bool:
        """Create a new project in SonarQube."""
        response = await self._make_request(
            'POST',
            'projects/create',
            data={
                'project': project_key,
                'name': project_name
            }
        )
        
        return response is not None
    
    async def get_webhook_deliveries(self, project_key: str) -> List[Dict[str, Any]]:
        """Get webhook deliveries for a project."""
        response = await self._make_request(
            'GET',
            'webhooks/deliveries',
            params={'componentKey': project_key}
        )
        
        if response and response.get('deliveries'):
            return response['deliveries']
        
        return []
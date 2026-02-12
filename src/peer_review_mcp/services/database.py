"""
Database management service for the Peer Review MCP Server.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy.future import select

from ..config import config
from ..models import (
    Base, Repository, PullRequest, Review, AutomatedCheck,
    ReviewCriteria, GovernanceValidation, ReviewStatus,
    RepositoryCreate, RepositoryResponse, PullRequestCreate, PullRequestResponse,
    ReviewCreate, ReviewResponse, AutomatedCheckCreate, AutomatedCheckResponse,
    ReviewCriteriaCreate, ReviewCriteriaResponse, GovernanceValidationCreate,
    GovernanceValidationResponse
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for handling all database operations."""
    
    def __init__(self):
        """Initialize database manager."""
        self.database_url = config.database.url
        self.echo = config.database.echo
        
        # Create async engine
        self.async_engine = create_async_engine(
            self.database_url.replace("sqlite://", "sqlite+aiosqlite://"),
            echo=self.echo
        )
        
        # Create session factory
        self.async_session = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def initialize(self):
        """Initialize database tables."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized")
    
    async def close(self):
        """Close database connections."""
        await self.async_engine.dispose()
        logger.info("Database connections closed")
    
    # Repository operations
    
    async def create_repository(self, repo_data: Dict[str, Any]) -> RepositoryResponse:
        """Create a new repository."""
        async with self.async_session() as session:
            repo = Repository(**repo_data)
            session.add(repo)
            await session.commit()
            await session.refresh(repo)
            return RepositoryResponse.from_orm(repo)
    
    async def get_repository_by_full_name(self, full_name: str) -> Optional[RepositoryResponse]:
        """Get repository by full name."""
        async with self.async_session() as session:
            result = await session.execute(
                select(Repository).where(Repository.full_name == full_name)
            )
            repo = result.scalar_one_or_none()
            return RepositoryResponse.from_orm(repo) if repo else None
    
    async def get_all_repositories(self) -> List[RepositoryResponse]:
        """Get all repositories."""
        async with self.async_session() as session:
            result = await session.execute(select(Repository))
            repos = result.scalars().all()
            return [RepositoryResponse.from_orm(repo) for repo in repos]
    
    async def get_or_create_repository_from_github(self, full_name: str) -> RepositoryResponse:
        """Get or create repository from GitHub data."""
        repo = await self.get_repository_by_full_name(full_name)
        if repo:
            return repo
        
        # Create basic repository entry
        owner, name = full_name.split('/')
        repo_data = {
            "name": name,
            "full_name": full_name,
            "clone_url": f"https://github.com/{full_name}.git",
            "owner": owner,
            "default_branch": "main"
        }
        
        return await self.create_repository(repo_data)
    
    # Pull Request operations
    
    async def create_pull_request(self, pr_data: Dict[str, Any]) -> PullRequestResponse:
        """Create a new pull request."""
        async with self.async_session() as session:
            pr = PullRequest(**pr_data)
            session.add(pr)
            await session.commit()
            await session.refresh(pr)
            return PullRequestResponse.from_orm(pr)
    
    async def get_pull_request_by_repo_and_number(
        self, repository: str, pr_number: int
    ) -> Optional[PullRequestResponse]:
        """Get pull request by repository and number."""
        async with self.async_session() as session:
            result = await session.execute(
                select(PullRequest)
                .join(Repository)
                .where(
                    and_(
                        Repository.full_name == repository,
                        PullRequest.pr_number == pr_number
                    )
                )
                .options(selectinload(PullRequest.repository))
            )
            pr = result.scalar_one_or_none()
            return PullRequestResponse.from_orm(pr) if pr else None
    
    async def get_active_pull_requests(self) -> List[PullRequestResponse]:
        """Get all active pull requests."""
        async with self.async_session() as session:
            result = await session.execute(
                select(PullRequest)
                .where(
                    PullRequest.status.in_([
                        ReviewStatus.PENDING,
                        ReviewStatus.IN_PROGRESS,
                        ReviewStatus.CHANGES_REQUESTED
                    ])
                )
                .options(selectinload(PullRequest.repository))
            )
            prs = result.scalars().all()
            return [PullRequestResponse.from_orm(pr) for pr in prs]
    
    async def update_pull_request_status(
        self, pr_id: int, status: ReviewStatus
    ) -> PullRequestResponse:
        """Update pull request status."""
        async with self.async_session() as session:
            result = await session.execute(
                select(PullRequest).where(PullRequest.id == pr_id)
            )
            pr = result.scalar_one()
            pr.status = status
            pr.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(pr)
            return PullRequestResponse.from_orm(pr)
    
    # Review operations
    
    async def create_review(self, review_data: Dict[str, Any]) -> ReviewResponse:
        """Create a new review."""
        async with self.async_session() as session:
            review = Review(**review_data)
            session.add(review)
            await session.commit()
            await session.refresh(review)
            return ReviewResponse.from_orm(review)
    
    async def get_reviews_by_pull_request(self, pr_id: int) -> List[ReviewResponse]:
        """Get all reviews for a pull request."""
        async with self.async_session() as session:
            result = await session.execute(
                select(Review).where(Review.pull_request_id == pr_id)
            )
            reviews = result.scalars().all()
            return [ReviewResponse.from_orm(review) for review in reviews]
    
    # Automated Check operations
    
    async def create_automated_check(
        self, check_data: Dict[str, Any]
    ) -> AutomatedCheckResponse:
        """Create a new automated check."""
        async with self.async_session() as session:
            check = AutomatedCheck(**check_data)
            session.add(check)
            await session.commit()
            await session.refresh(check)
            return AutomatedCheckResponse.from_orm(check)
    
    async def get_checks_by_pull_request(self, pr_id: int) -> List[AutomatedCheckResponse]:
        """Get all automated checks for a pull request."""
        async with self.async_session() as session:
            result = await session.execute(
                select(AutomatedCheck).where(AutomatedCheck.pull_request_id == pr_id)
            )
            checks = result.scalars().all()
            return [AutomatedCheckResponse.from_orm(check) for check in checks]
    
    async def update_check_status(
        self, check_id: int, status: str, details: Dict[str, Any] = None
    ) -> AutomatedCheckResponse:
        """Update automated check status."""
        async with self.async_session() as session:
            result = await session.execute(
                select(AutomatedCheck).where(AutomatedCheck.id == check_id)
            )
            check = result.scalar_one()
            check.status = status
            if details:
                check.details = details
            if status in ["success", "failure", "error"]:
                check.completed_at = datetime.utcnow()
            await session.commit()
            await session.refresh(check)
            return AutomatedCheckResponse.from_orm(check)
    
    # Review Criteria operations
    
    async def create_review_criteria(
        self, criteria_data: Dict[str, Any]
    ) -> ReviewCriteriaResponse:
        """Create new review criteria."""
        async with self.async_session() as session:
            criteria = ReviewCriteria(**criteria_data)
            session.add(criteria)
            await session.commit()
            await session.refresh(criteria)
            return ReviewCriteriaResponse.from_orm(criteria)
    
    async def get_review_criteria_by_repository(
        self, repository_id: int
    ) -> List[ReviewCriteriaResponse]:
        """Get all review criteria for a repository."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ReviewCriteria).where(ReviewCriteria.repository_id == repository_id)
            )
            criteria = result.scalars().all()
            return [ReviewCriteriaResponse.from_orm(c) for c in criteria]
    
    async def get_all_review_criteria(self) -> List[ReviewCriteriaResponse]:
        """Get all review criteria."""
        async with self.async_session() as session:
            result = await session.execute(select(ReviewCriteria))
            criteria = result.scalars().all()
            return [ReviewCriteriaResponse.from_orm(c) for c in criteria]
    
    async def update_review_criteria(
        self, criteria_id: int, rules: Dict[str, Any]
    ) -> ReviewCriteriaResponse:
        """Update review criteria rules."""
        async with self.async_session() as session:
            result = await session.execute(
                select(ReviewCriteria).where(ReviewCriteria.id == criteria_id)
            )
            criteria = result.scalar_one()
            criteria.rules = rules
            criteria.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(criteria)
            return ReviewCriteriaResponse.from_orm(criteria)
    
    # Governance Validation operations
    
    async def create_governance_validation(
        self, validation_data: Dict[str, Any]
    ) -> GovernanceValidationResponse:
        """Create new governance validation."""
        async with self.async_session() as session:
            validation = GovernanceValidation(**validation_data)
            session.add(validation)
            await session.commit()
            await session.refresh(validation)
            return GovernanceValidationResponse.from_orm(validation)
    
    async def get_validations_by_pull_request(
        self, pr_id: int
    ) -> List[GovernanceValidationResponse]:
        """Get all governance validations for a pull request."""
        async with self.async_session() as session:
            result = await session.execute(
                select(GovernanceValidation).where(
                    GovernanceValidation.pull_request_id == pr_id
                )
            )
            validations = result.scalars().all()
            return [GovernanceValidationResponse.from_orm(v) for v in validations]
    
    # Analytics and Metrics
    
    async def get_repository_metrics(
        self, repository_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """Get metrics for a repository."""
        async with self.async_session() as session:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Total PRs
            total_prs_result = await session.execute(
                select(func.count(PullRequest.id)).where(
                    and_(
                        PullRequest.repository_id == repository_id,
                        PullRequest.created_at >= since_date
                    )
                )
            )
            total_prs = total_prs_result.scalar()
            
            # Merged PRs
            merged_prs_result = await session.execute(
                select(func.count(PullRequest.id)).where(
                    and_(
                        PullRequest.repository_id == repository_id,
                        PullRequest.status == ReviewStatus.MERGED,
                        PullRequest.created_at >= since_date
                    )
                )
            )
            merged_prs = merged_prs_result.scalar()
            
            # Average review time (simplified)
            avg_review_time = 24.0  # Placeholder - would need more complex query
            
            # Compliance rate
            compliance_rate = merged_prs / total_prs if total_prs > 0 else 0.0
            
            # Automation success rate
            automation_success_rate = 0.85  # Placeholder - would calculate from checks
            
            return {
                "total_pull_requests": total_prs,
                "merged_pull_requests": merged_prs,
                "avg_review_time_hours": avg_review_time,
                "compliance_rate": compliance_rate,
                "automation_success_rate": automation_success_rate,
                "top_violation_types": []  # Placeholder
            }
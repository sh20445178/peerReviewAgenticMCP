"""
Default peer review criteria and governance rules.
"""

DEFAULT_REVIEW_CRITERIA = {
    "code_quality": {
        "name": "Code Quality Standards",
        "description": "General code quality and maintainability standards",
        "criteria_type": "quality",
        "rules": {
            "max_complexity": 10,
            "max_function_length": 50,
            "max_class_length": 200,
            "duplicate_threshold": 5.0,
            "comment_ratio": 0.15
        },
        "weight": 3,
        "is_required": True
    },
    "testing": {
        "name": "Testing Requirements",
        "description": "Testing coverage and quality standards",
        "criteria_type": "testing",
        "rules": {
            "min_coverage": 80.0,
            "unit_tests_required": True,
            "integration_tests_required": True,
            "test_naming_convention": r"test_.+|.+_test"
        },
        "weight": 3,
        "is_required": True
    },
    "security": {
        "name": "Security Standards",
        "description": "Security and vulnerability standards",
        "criteria_type": "security",
        "rules": {
            "vulnerability_scan_required": True,
            "secret_scan_required": True,
            "dependency_check_required": True,
            "max_critical_vulnerabilities": 0,
            "max_high_vulnerabilities": 0
        },
        "weight": 4,
        "is_required": True
    },
    "documentation": {
        "name": "Documentation Standards",
        "description": "Documentation completeness and quality",
        "criteria_type": "documentation",
        "rules": {
            "readme_required": True,
            "api_docs_required": True,
            "inline_comments_required": True,
            "changelog_required": True
        },
        "weight": 2,
        "is_required": False
    },
    "performance": {
        "name": "Performance Standards",
        "description": "Performance and scalability considerations",
        "criteria_type": "performance",
        "rules": {
            "performance_test_required": False,
            "load_test_threshold": 1000,
            "memory_usage_check": True,
            "database_query_optimization": True
        },
        "weight": 2,
        "is_required": False
    }
}

DEFAULT_GOVERNANCE_POLICIES = {
    "approval_workflow": {
        "min_reviewers": 2,
        "required_reviewer_roles": ["senior-developer"],
        "approval_timeout_hours": 48,
        "auto_merge_conditions": {
            "all_checks_pass": True,
            "min_approvals_met": True,
            "no_conflicts": True,
            "author_not_reviewer": True
        }
    },
    "branch_protection": {
        "protect_main": True,
        "protect_release": True,
        "require_pr_for_merge": True,
        "require_status_checks": True,
        "require_up_to_date": True,
        "dismiss_stale_reviews": True
    },
    "commit_standards": {
        "conventional_commits": True,
        "signed_commits_required": False,
        "max_commit_size": 1000,
        "squash_merge_preferred": True
    },
    "file_restrictions": {
        "protected_files": [
            "package.json",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            ".github/workflows/*.yml"
        ],
        "sensitive_paths": [
            "config/production/",
            "secrets/",
            ".env.production"
        ]
    }
}
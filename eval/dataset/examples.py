"""Example dataset for quick testing."""

EXAMPLE_PR_LIST = [
    {
        "pr_id": "001",
        "repository": "example-repo",
        "branch_source": "feature/auth",
        "branch_target": "main",
        "title": "Add authentication middleware",
        "description": "Implements JWT authentication middleware for API routes",
        "author": "developer",
        "commit_messages": ["Add JWT auth", "Fix validation", "Add tests"],
        "files_changed": 5,
        "lines_added": 150,
        "lines_deleted": 20,
        "language": "python",
    },
    {
        "pr_id": "002",
        "repository": "example-repo",
        "branch_source": "feature/api",
        "branch_target": "main",
        "title": "Refactor API endpoints",
        "description": "Restructure API endpoints for better organization",
        "author": "developer",
        "commit_messages": ["Refactor endpoints", "Update docs"],
        "files_changed": 8,
        "lines_added": 200,
        "lines_deleted": 180,
        "language": "python",
    },
]

EXAMPLE_GROUND_TRUTH = [
    {
        "pr_id": "001",
        "important_issues": [
            "Missing input validation on JWT token",
            "No rate limiting on auth endpoint",
        ],
        "false_positive_tolerance": 3,
        "labeler_id": "expert_1",
        "notes": "Authentication changes require extra scrutiny",
    },
    {
        "pr_id": "002",
        "important_issues": [
            "Breaking API change without version bump",
        ],
        "false_positive_tolerance": 5,
        "labeler_id": "expert_1",
        "notes": "Refactoring PR, mostly organizational",
    },
]

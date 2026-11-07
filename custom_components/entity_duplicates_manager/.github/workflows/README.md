# Entity Duplicates Manager CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### `validate.yml` - Code Validation
Runs on every push and pull request:
- Python syntax validation
- Home Assistant manifest validation
- JSON/YAML syntax checking
- Custom component structure validation

### `test.yml` - Testing
Runs on every push and pull request:
- Unit tests for core modules
- Integration tests with Home Assistant
- Frontend JavaScript validation

### `release.yml` - Release Management
Runs on version tag push:
- Creates GitHub release
- Packages for HACS distribution
- Updates version references

## Setup

1. Enable GitHub Actions in repository settings
2. Ensure workflows have appropriate permissions
3. Configure branch protection rules

## Local Testing

```bash
# Validate manifest
python -c "import json; json.load(open('custom_components/entity_duplicates_manager/manifest.json'))"

# Check Python syntax
python -m py_compile custom_components/entity_duplicates_manager/*.py

# Validate HACS config
python -c "import json; json.load(open('hacs.json'))"
```

## Workflow Triggers

- **Push**: Main branch and feature branches
- **Pull Request**: All PRs to main
- **Tags**: Version tags (v*) for releases
- **Schedule**: Weekly dependency checks
# Contributing to Multi-Agent Code Review Framework

Thank you for your interest in contributing! This is a master's thesis project with specific research goals, so please read carefully before contributing.

## Research Focus

This project aims to evaluate whether multi-agent code review with tool integration produces:
- Higher actionability (more patches/clear fixes)
- Lower noise (fewer false positives)
- Better coverage (detect more critical issues)

Contributions should align with these research goals.

## Before Contributing

1. **Open an issue first** - Discuss proposed changes to ensure alignment with research methodology
2. **Review architecture** - Read `ARCHITECTURE.md` to understand design principles
3. **Check thesis scope** - Some features may be intentionally out of scope for research validity

## Development Setup

```bash
# Clone and setup
git clone <repo>
cd code-review-agentic-framework
make setup
make install

# Run tests
make test

# Check code quality
make lint
```

## Types of Contributions

### ✅ Welcome Contributions

- **Bug fixes**: Clear bugs in existing functionality
- **Test improvements**: Better coverage, edge cases
- **Documentation**: Clarifications, examples, typos
- **Performance**: Optimizations without changing behavior
- **Tool integrations**: New linters/analyzers (with justification)

### ⚠️ Requires Discussion

- **New agents**: Must align with research design
- **Architecture changes**: May impact reproducibility
- **Metric changes**: Affects evaluation validity
- **Prompt modifications**: Controlled for research

### ❌ Out of Scope

- Major UI changes (CLI is sufficient for thesis)
- Auto-merge features (human-in-loop required)
- Complex deployment (single environment focus)

## Pull Request Process

1. **Branch naming**: `fix/description`, `feat/description`, `docs/description`
2. **Tests required**: All new code must have tests
3. **Linting**: Run `make lint` and fix issues
4. **Commit messages**: Clear, descriptive
5. **Reference issue**: Link to issue in PR description

### Checklist

- [ ] Tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated (if needed)
- [ ] Issue referenced
- [ ] Follows SOLID/DRY principles

## Code Style

- **Python 3.11+**
- **Type hints**: Required for all functions
- **Docstrings**: For public APIs
- **Line length**: 100 chars
- **Formatting**: Use `make format`

## Testing

```bash
# Run all tests
make test

# With coverage
make test-cov

# Specific test
poetry run pytest tests/unit/test_models.py -v
```

### Test Guidelines

- **Unit tests**: For pure logic (models, metrics, parsers)
- **Integration tests**: For tool integrations
- **E2E tests**: For complete flows (mock LLM when possible)
- **Coverage target**: 80%+ for core, 60%+ for agents

## Research Ethics

This project involves:
- Using LLM APIs (costs money)
- Analyzing code (may include sensitive data)

**Please**:
- Respect API rate limits
- Don't commit real API keys
- Anonymize any real PR data

## Questions?

Open an issue with label `question` or contact the maintainer.

## License

By contributing, you agree your contributions will be licensed under the MIT License.


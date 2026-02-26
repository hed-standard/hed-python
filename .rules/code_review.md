# Code Review Process

## Before Creating a PR
1. All tests pass: `pytest tests/ --cov` and `pytest spec_tests/`
2. Linting clean: `ruff check hed/ tests/`
3. Formatting clean: `black --check hed/ tests/`
4. Spelling clean: `codespell`
5. New functionality has tests (real data, no mocks)

## PR Review with pr-review-toolkit
Run `/review-pr` with all subagents in parallel:
- **Code reviewer:** bugs, logic errors, security vulnerabilities, code quality, project conventions
- **Silent failure hunter:** error handling, catch blocks, fallback behavior
- **Code simplifier:** unnecessary complexity
- **Comment analyzer:** comment accuracy and maintainability
- **Test analyzer:** test coverage quality and completeness
- **Type design analyzer:** type design quality (encapsulation, invariants)

## Review Standards
- Address all critical and important findings (fix or explain why skipped)
- Consider nice-to-haves if they improve quality without major effort
- Document unaddressed items in PR comments
- All 12 CI workflows must be green before merge

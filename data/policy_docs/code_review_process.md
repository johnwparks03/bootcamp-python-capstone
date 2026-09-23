# Engineering Code Review Process

**Document ID:** POL-002  
**Effective Date:** March 15, 2023  
**Last Updated:** July 10, 2024

## 1. Purpose

Code review is a critical quality gate in our development process. All changes to production code must pass peer review to ensure maintainability, correctness, and adherence to our engineering standards.

## 2. Scope

This process applies to all code merged into the main branch, including:
- Feature development
- Bug fixes
- Performance improvements
- Infrastructure and DevOps code

Excluded: documentation-only changes, internal experiment branches (with explicit team approval).

## 3. Code Review Requirements

Every pull request (PR) must:
1. Include a clear description of the change and its purpose
2. Have a minimum of one approval from another engineer (two approvals for changes affecting core systems)
3. Pass all automated tests and linting checks
4. Receive approval from a domain expert if the change touches critical paths (payment processing, customer data)
5. Include tests for new code (minimum 80% test coverage for new lines)

## 4. Reviewer Responsibilities

Reviewers shall:
- Evaluate code for correctness, performance, and readability
- Check for security vulnerabilities and best practices adherence
- Request changes if the code does not meet our standards
- Approve only when satisfied with the overall quality
- Provide constructive feedback within 24 hours of PR submission

## 5. Author Responsibilities

Authors shall:
- Keep PRs focused and reasonably sized (aim for <400 lines of logic)
- Respond to feedback promptly (within 24 hours)
- Make requested changes or discuss alternatives respectfully
- Ensure all CI checks pass before requesting review
- Update the PR description if major changes are made

## 6. Approval and Merge

- PRs require explicit approval before merging
- Authors may not merge their own code
- Once approved, the author or a reviewer must merge within 5 business days
- Long-lived branches (>2 weeks) should be rebased and re-reviewed

## 7. Escalation

Disputes about code quality are resolved by the engineering lead. Persistent non-compliance with this process may result in loss of merge privileges.

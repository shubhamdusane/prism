# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x (latest) | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within **Prism**, please send an email to sdusane4@gmail.com. Reports are handled on a best-effort basis.

**Please include the following in your report:**

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if applicable)
- Your contact information for follow-up

## Response Timeline

This is a single-maintainer, pre-1.0 project. Reports are handled on a best-effort basis; there is no guaranteed response or fix time.

## Security Update Process

1. Vulnerability reports are triaged and prioritized
2. A fix is developed and tested in a private branch
3. Security patch is released as a minor or patch version bump
4. Affected users are notified via release notes
5. CVE is requested if applicable

## Security-Related Configuration

- Input transformation pipelines are sandboxed per request
- Output rendering uses strict content-type enforcement
- User-contributed schemas undergo static analysis before activation
- Prism API tokens are scoped to specific transformation pipelines
- Execution timeouts prevent resource exhaustion from malicious inputs

## Known Security Gaps

- Custom transformer plugins execute in the same process as the core engine
- Schema import functionality does not validate against recursive definitions
- Transformation logs may leak sensitive data in error messages

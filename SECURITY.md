# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within **Prism**, please send an email to sdusane4@gmail.com. All reports will be promptly addressed.

**Please include the following in your report:**

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if applicable)
- Your contact information for follow-up

## Response Timeline

- **Acknowledgment:** Within 48 hours of report submission
- **Initial Assessment:** Within 72 hours
- **Fix Deployment:** Within 7 days for confirmed vulnerabilities

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

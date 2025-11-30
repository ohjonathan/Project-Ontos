# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.4.x   | :white_check_mark: |
| < 0.4   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Project Ontos, please report it responsibly:

1. **Do not** open a public issue
2. **Email** the maintainers directly or use GitHub's private vulnerability reporting
3. **Include** details about the vulnerability and steps to reproduce

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Resolution**: Depends on severity and complexity

## Security Considerations

Project Ontos processes local markdown files. Key security considerations:

### File System Access

- Scripts only read/write within specified directories
- No network requests are made by core scripts
- File paths are not sanitized for shell injection (don't pass untrusted input)

### YAML Parsing

- Uses PyYAML's `safe_load()` to prevent code execution
- Malformed YAML is handled gracefully

### Best Practices for Users

1. **Don't run scripts on untrusted directories** - Only use Ontos on your own projects
2. **Review generated files** - Always review `CONTEXT_MAP.md` before committing
3. **Keep dependencies updated** - Run `pip install --upgrade pyyaml`

## Scope

This security policy applies to:

- `scripts/generate_context_map.py`
- `scripts/migrate_frontmatter.py`
- `scripts/end_session.py`
- Related configuration files

Third-party dependencies (PyYAML, watchdog, etc.) have their own security policies.

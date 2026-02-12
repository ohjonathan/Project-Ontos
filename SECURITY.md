# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 3.3.x   | :white_check_mark: |
| 3.2.x   | :white_check_mark: |
| < 3.0   | :x:                |

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

Project Ontos processes local markdown files via the `ontos` Python package. Key security considerations:

### File System Access

- The `ontos` CLI reads/writes within the project root and configured doc directories
- No network requests are made by any command
- File paths are validated against the project root — path traversal outside the repo is rejected

### YAML Parsing

- Uses PyYAML's `safe_load()` exclusively to prevent code execution
- Malformed YAML is handled gracefully with structured error reporting

### Best Practices for Users

1. **Don't run ontos on untrusted repositories** — Only use Ontos on your own projects
2. **Review generated files** — Always review `Ontos_Context_Map.md` and `AGENTS.md` before committing
3. **Keep dependencies updated** — Run `pip install --upgrade ontos`
4. **Scan for secrets before releases** — Run `gitleaks detect` and `trufflehog git file://. --no-update`

## Scope

This security policy applies to:

- The `ontos` Python package (`ontos/` directory)
  - `ontos/io/yaml.py` — YAML parsing surface
  - `ontos/io/scan.py` — File system scanning and discovery
  - `ontos/cli.py` — CLI entry point and argument handling
- The `ontos` CLI entry point (`ontos <command>`)
- Generated files: `Ontos_Context_Map.md`, `AGENTS.md`, `.cursorrules`

Third-party dependencies (PyYAML) have their own security policies.

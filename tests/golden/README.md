# Golden Master Testing

Golden Master tests capture the exact behavior of Ontos v2.9.x to ensure
v3.0 refactoring doesn't introduce regressions.

## Quick Start

### Running Comparisons (CI)

```bash
python tests/golden/compare_golden_master.py --fixture all
```

Exit code 0 means all tests pass. Exit code 1 means regression detected.

### Updating Baselines

When intentional behavior changes occur in v3.0:

```bash
# Re-capture baseline for specific fixture
python tests/golden/capture_golden_master.py --fixture small

# Re-capture all baselines
python tests/golden/capture_golden_master.py --fixture all

# Commit the updated baselines
git add tests/golden/baselines/
git commit -m "chore: update golden master baselines for v3.0 changes"
```

## Fixture Sizes

| Fixture | Documents | Purpose | CI Time |
|---------|-----------|---------|---------|
| small | 5 | Smoke test | ~2s |
| medium | 25 | Integration | ~5s |
| large | 100+ | Scalability | ~15s |

## Normalization

The capture/compare scripts normalize:

- **Timestamps**: Replaced with `<TIMESTAMP>` or `<DATE>`
- **Absolute paths**: Replaced with `<FIXTURE_ROOT>` or `<HOME>`
- **Version strings**: Replaced with `<VERSION>`
- **Mode indicators**: Replaced with `<MODE>`

## Files Captured

For each command, we capture:

- `{command}_stdout.txt` - Normalized stdout
- `{command}_stderr.txt` - Normalized stderr
- `{command}_exit_code.txt` - Exit code
- `{command}_metadata.json` - Capture metadata
- `context_map.md` - Generated Ontos_Context_Map.md (for map)
- `session_log.md` - Generated session log (for log)

## Troubleshooting

### Comparison fails on timestamps

Check if a new timestamp format was introduced. Update normalization
patterns in `capture_golden_master.py`.

### Comparison fails on path differences

Check if new path patterns appear in output. Update normalization
patterns to handle them.

### Intentional behavior change

1. Verify the change is intentional
2. Re-capture the affected baseline
3. Document the change in commit message
4. Update this README if normalization patterns changed

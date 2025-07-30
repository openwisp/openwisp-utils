# OpenWISP Automated Changelog Generation

This directory contains tools for automating changelog generation in OpenWISP projects using [git-cliff](https://git-cliff.org/). This addresses issue #496 for automated changelog generation and release process.

## Overview

The automation consists of three main components:

1. **`cliff.toml`** - Git-cliff configuration for OpenWISP commit conventions
2. **`dependency_processor.py`** - Smart dependency deduplication processor  
3. **`release-helper.sh`** - Complete release workflow automation

## Quick Start

### Prerequisites

Install git-cliff:
```bash
# Using Cargo (Rust)
cargo install git-cliff

# Or download binary from https://github.com/orhun/git-cliff/releases
```

### Basic Usage

```bash
# Generate draft changelog since last tag
./scripts/release-helper.sh

# Generate changelog for specific version
./scripts/release-helper.sh 1.2.0

# Generate changelog between specific tags  
./scripts/release-helper.sh 1.2.0 v1.1.0
```

## Components

### 1. Git-cliff Configuration (`cliff.toml`)

Handles OpenWISP commit conventions:

**Supported commit formats:**
- `[feature]` → Features section
- `[change]` → Changes section  
- `[change!]` → Changes section with **BREAKING CHANGE** marker
- `[bugfix]`, `[fix]`, `[fix:*]` → Bugfixes section
- `[deps]`, `[dep]` → Dependencies section
- `[skip changelog]`, `[ci]`, `[qa]`, `[chores]`, `[tests]` → Skipped

**Features:**
- ✅ RST format output to match CHANGES.rst
- ✅ Automatic GitHub issue linking (#123 → [#123](link))
- ✅ Breaking change detection with `!` notation
- ✅ Logical grouping into sections
- ✅ Skip patterns for CI/QA commits

### 2. Dependency Processor (`dependency_processor.py`)

Enhances git-cliff output with intelligent dependency handling:

**Features:**
- ✅ Analyzes actual file changes (requirements.txt, setup.py, ci.yml)
- ✅ Deduplicates package updates (shows only latest versions)
- ✅ Formats dependencies in OpenWISP style
- ✅ Integrates seamlessly with git-cliff output

**Usage:**
```bash
# Process changelog with smart dependencies
git-cliff --config cliff.toml | python3 scripts/dependency_processor.py [since-tag]
```

### 3. Release Helper (`release-helper.sh`)

Complete workflow automation with human review checkpoints:

**Features:**
- ✅ Generates changelog with git-cliff
- ✅ Enhances dependencies intelligently
- ✅ Formats for RST and OpenWISP conventions
- ✅ Provides preview before updating files
- ✅ Integrates with existing CHANGES.rst
- ✅ Includes manual review checkpoints

**Workflow:**
1. Generate basic changelog with git-cliff
2. Enhance dependencies section
3. Format for RST and version headers
4. Show preview for review
5. Update CHANGES.rst (with confirmation)
6. Provide next steps guidance

## Configuration Details

### Commit Convention Mapping

| OpenWISP Convention | Git-cliff Group | Breaking Support |
|-------------------|----------------|-----------------|
| `[feature]` | Features | `[feature!]` |
| `[change]` | Changes | `[change!]` |
| `[bugfix]`, `[fix]` | Bugfixes | `[fix!]` |
| `[deps]` | Dependencies | No |
| `[skip changelog]` | Skipped | N/A |
| `[ci]`, `[qa]`, `[chores]`, `[tests]` | Skipped | N/A |

### Output Format

Generated changelog follows OpenWISP's RST format:

```rst
Version 1.2.0 [2024-01-15]
--------------------------

Features
~~~~~~~~

- Added new feature for XYZ functionality
- Enhanced ABC component with new capabilities

Changes  
~~~~~~~

- Modified existing behavior for better performance **BREAKING CHANGE**
- Updated configuration format

Dependencies
~~~~~~~~~~~~

- Bumped ``django~=4.2.0``
- Updated ``requests>=2.28.0``

Bugfixes
~~~~~~~~

- Fixed issue with authentication flow
- Resolved edge case in data processing
```

## Advanced Usage

### Manual Git-cliff Usage

```bash
# Generate changelog since specific tag
git-cliff --config cliff.toml --since v1.1.0

# Generate for specific version range
git-cliff --config cliff.toml v1.1.0..v1.2.0

# Generate latest version only
git-cliff --config cliff.toml --latest
```

### Customizing Templates

Edit `cliff.toml` to modify:
- Output formatting
- Commit grouping rules
- Skip patterns
- Link generation

### Dependency Processing Only

```bash
# Process existing changelog
cat CHANGES.rst | python3 scripts/dependency_processor.py v1.1.0
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Generate Release Changelog
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Release version'
        required: true

jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Install git-cliff
      run: cargo install git-cliff
    - name: Generate changelog
      run: |
        ./scripts/release-helper.sh ${{ github.event.inputs.version }}
    - name: Create PR
      # Add PR creation logic
```

## Troubleshooting

### Common Issues

**1. Git-cliff not found**
```bash
# Install git-cliff
cargo install git-cliff
# Or download from https://github.com/orhun/git-cliff/releases
```

**2. Template errors**
- Check cliff.toml syntax
- Validate Tera template formatting
- Test with `git-cliff --config cliff.toml --latest`

**3. No commits found**
- Ensure commit messages follow OpenWISP conventions
- Check tag patterns in configuration
- Verify git history exists

### Debug Mode

```bash
# Run git-cliff with verbose output
git-cliff --config cliff.toml --verbose

# Test dependency processor
python3 scripts/dependency_processor.py --help
```

## Contributing

To improve the changelog automation:

1. Test with actual releases
2. Refine commit patterns in cliff.toml
3. Enhance dependency detection logic
4. Improve template formatting
5. Add more automation features

## References

- [Issue #496: Automate changelog generation](https://github.com/openwisp/openwisp-utils/issues/496)
- [Git-cliff Documentation](https://git-cliff.org/docs/)
- [OpenWISP Commit Conventions](https://openwisp.io/docs/dev/contributing/)
- [Analysis Document](../docs/git-cliff-analysis.md)
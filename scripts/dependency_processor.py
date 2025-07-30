#!/usr/bin/env python3
"""
Smart dependency processor for OpenWISP changelog generation.

This script processes the dependency section from git-cliff output
to provide intelligent deduplication and formatting.
"""

import re
import subprocess
import sys
from typing import Dict, List, Tuple, Set
from collections import defaultdict


def parse_git_log_for_dependencies(since_tag: str = None) -> List[str]:
    """
    Parse git log to find dependency-related commits since a specific tag.
    """
    cmd = ["git", "log", "--oneline", "--grep=\\[deps\\]", "--grep=\\[dep\\]"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def parse_requirements_changes(since_tag: str = None) -> Dict[str, List[str]]:
    """
    Parse actual file changes to detect dependency updates.
    """
    dependencies = defaultdict(list)
    
    # Check requirements.txt changes
    cmd = ["git", "log", "--oneline", "-p", "--", "requirements*.txt", "setup.py"]
    if since_tag:
        cmd.append(f"{since_tag}..HEAD")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse diff output for dependency changes
        for line in result.stdout.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                # Look for package version patterns
                package_match = re.search(r'\+\s*([a-zA-Z0-9_-]+)[>=~<]+([0-9.]+)', line)
                if package_match:
                    package, version = package_match.groups()
                    dependencies[package].append(version)
    
    except subprocess.CalledProcessError:
        pass
    
    return dependencies


def deduplicate_dependencies(dependencies: Dict[str, List[str]]) -> Dict[str, str]:
    """
    For each package, keep only the latest version mentioned.
    """
    latest_deps = {}
    for package, versions in dependencies.items():
        # Simple approach: take the last version mentioned
        # In a real implementation, you might want to do semantic version comparison
        latest_deps[package] = versions[-1]
    
    return latest_deps


def format_dependency_section(dependencies: Dict[str, str]) -> str:
    """
    Format the dependencies section in RST format.
    """
    if not dependencies:
        return ""
    
    section = "Dependencies\n~~~~~~~~~~~~\n\n"
    
    for package, version in sorted(dependencies.items()):
        # Format as RST with proper markup
        section += f"- Bumped ``{package}~={version}``\n"
    
    return section


def process_changelog_with_smart_dependencies(changelog_content: str, since_tag: str = None) -> str:
    """
    Process a git-cliff generated changelog to enhance the dependencies section.
    """
    # Parse actual dependency changes from git
    req_changes = parse_requirements_changes(since_tag)
    smart_deps = deduplicate_dependencies(req_changes)
    
    # If we found dependency changes, replace the dependencies section
    if smart_deps:
        # Find and replace the Dependencies section
        deps_pattern = r'(Dependencies\n~+\n\n)(.*?)(\n\n|\Z)'
        new_deps_section = format_dependency_section(smart_deps)
        
        if re.search(deps_pattern, changelog_content, re.DOTALL):
            # Replace existing dependencies section
            changelog_content = re.sub(
                deps_pattern,
                f"{new_deps_section}\n",
                changelog_content,
                flags=re.DOTALL
            )
        else:
            # Add dependencies section before the last section or at the end
            # This is a simplified approach
            if "Bugfixes" in changelog_content:
                changelog_content = changelog_content.replace(
                    "Bugfixes\n~",
                    f"{new_deps_section}\nBugfixes\n~"
                )
            else:
                changelog_content += f"\n{new_deps_section}"
    
    return changelog_content


def main():
    """Main function to process changelog."""
    if len(sys.argv) > 1:
        since_tag = sys.argv[1]
    else:
        since_tag = None
    
    # Read changelog from stdin or file
    if not sys.stdin.isatty():
        changelog_content = sys.stdin.read()
    else:
        print("Usage: cat changelog.md | python3 dependency_processor.py [since_tag]")
        print("   or: python3 dependency_processor.py [since_tag] < changelog.md")
        sys.exit(1)
    
    # Process the changelog
    enhanced_changelog = process_changelog_with_smart_dependencies(changelog_content, since_tag)
    
    # Output the enhanced changelog
    print(enhanced_changelog)


if __name__ == "__main__":
    main()
#!/bin/bash
#
# OpenWISP Release Helper Script
# 
# This script automates the changelog generation process using git-cliff
# and provides a foundation for the complete release workflow.
#
# Usage: ./release-helper.sh [version] [since-tag]
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIFF_CONFIG="${SCRIPT_DIR}/cliff.toml"
DEPENDENCY_PROCESSOR="${SCRIPT_DIR}/dependency_processor.py"
CHANGELOG_FILE="CHANGES.rst"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check if git-cliff is installed
    if ! command -v git-cliff &> /dev/null; then
        log_error "git-cliff is not installed. Please install it first:"
        echo "  cargo install git-cliff"
        echo "  # or"
        echo "  # Download from https://github.com/orhun/git-cliff/releases"
        exit 1
    fi
    
    # Check if python3 is available
    if ! command -v python3 &> /dev/null; then
        log_error "python3 is not installed."
        exit 1
    fi
    
    log_success "All dependencies are available"
}

get_latest_tag() {
    git tag --sort=-version:refname | head -n1 || echo ""
}

generate_changelog() {
    local version="$1"
    local since_tag="$2"
    local output_file="$3"
    
    log_info "Generating changelog with git-cliff..."
    
    # Build git-cliff command
    local cmd="git-cliff"
    
    if [[ -f "$CLIFF_CONFIG" ]]; then
        cmd="$cmd --config $CLIFF_CONFIG"
    fi
    
    if [[ -n "$since_tag" ]]; then
        cmd="$cmd --since $since_tag"
    fi
    
    if [[ -n "$version" ]]; then
        cmd="$cmd --tag $version"
    fi
    
    # Generate changelog
    log_info "Running: $cmd"
    eval "$cmd" > "$output_file"
    
    log_success "Basic changelog generated: $output_file"
}

enhance_dependencies() {
    local changelog_file="$1"
    local since_tag="$2"
    
    log_info "Enhancing dependencies section..."
    
    if [[ -f "$DEPENDENCY_PROCESSOR" ]]; then
        # Create backup
        cp "$changelog_file" "${changelog_file}.backup"
        
        # Process dependencies
        python3 "$DEPENDENCY_PROCESSOR" "$since_tag" < "$changelog_file" > "${changelog_file}.enhanced"
        mv "${changelog_file}.enhanced" "$changelog_file"
        
        log_success "Dependencies section enhanced"
    else
        log_warning "Dependency processor not found: $DEPENDENCY_PROCESSOR"
    fi
}

format_for_rst() {
    local changelog_file="$1"
    local version="$2"
    local release_date="$3"
    
    log_info "Formatting changelog for RST..."
    
    # Add version header in OpenWISP format
    local version_header="Version $version [$release_date]"
    local version_underline=$(printf "%*s" ${#version_header} | tr ' ' '-')
    
    # Prepend version information
    {
        echo "$version_header"
        echo "$version_underline"
        echo ""
        cat "$changelog_file"
        echo ""
    } > "${changelog_file}.formatted"
    
    mv "${changelog_file}.formatted" "$changelog_file"
    
    log_success "Changelog formatted for RST"
}

show_changelog_preview() {
    local changelog_file="$1"
    
    echo ""
    log_info "Generated changelog preview:"
    echo "==========================================="
    cat "$changelog_file"
    echo "==========================================="
    echo ""
}

update_changes_rst() {
    local temp_changelog="$1"
    local version="$2"
    
    log_info "Updating CHANGES.rst..."
    
    if [[ -f "$CHANGELOG_FILE" ]]; then
        # Insert new changelog at the top, after the header
        {
            # Keep the header (first 3 lines typically)
            head -n 3 "$CHANGELOG_FILE"
            echo ""
            # Add new changelog
            cat "$temp_changelog"
            echo ""
            # Add rest of the file (skip header)
            tail -n +4 "$CHANGELOG_FILE"
        } > "${CHANGELOG_FILE}.new"
        
        mv "${CHANGELOG_FILE}.new" "$CHANGELOG_FILE"
        log_success "CHANGES.rst updated"
    else
        log_warning "CHANGES.rst not found, creating new file"
        {
            echo "Changelog"
            echo "========="
            echo ""
            cat "$temp_changelog"
        } > "$CHANGELOG_FILE"
    fi
}

main() {
    local version="$1"
    local since_tag="$2"
    local release_date=$(date +%Y-%m-%d)
    local temp_changelog="/tmp/openwisp-changelog-${version:-draft}.md"
    
    log_info "OpenWISP Release Helper"
    log_info "======================="
    
    # Validate inputs
    if [[ -z "$version" ]]; then
        log_warning "No version specified, generating draft changelog"
        version="Unreleased"
        release_date="TBD"
    fi
    
    if [[ -z "$since_tag" ]]; then
        since_tag=$(get_latest_tag)
        if [[ -n "$since_tag" ]]; then
            log_info "Using latest tag as base: $since_tag"
        else
            log_warning "No tags found, generating full changelog"
        fi
    fi
    
    # Check dependencies
    check_dependencies
    
    # Generate changelog
    generate_changelog "$version" "$since_tag" "$temp_changelog"
    
    # Enhance dependencies
    enhance_dependencies "$temp_changelog" "$since_tag"
    
    # Format for RST
    format_for_rst "$temp_changelog" "$version" "$release_date"
    
    # Show preview
    show_changelog_preview "$temp_changelog"
    
    # Ask for confirmation
    echo -n "Do you want to update CHANGES.rst with this changelog? (y/N): "
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        update_changes_rst "$temp_changelog" "$version"
        log_success "Changelog generation completed!"
        log_info "Next steps:"
        log_info "1. Review and edit CHANGES.rst manually"
        log_info "2. Add any missing hyperlinks or context"
        log_info "3. Commit the changes"
        log_info "4. Create release tag: git tag v$version"
    else
        log_info "Changelog saved to: $temp_changelog"
        log_info "You can review and manually integrate it later."
    fi
}

# Handle help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [version] [since-tag]"
    echo ""
    echo "Arguments:"
    echo "  version     Version number for the release (e.g., 1.2.0)"
    echo "  since-tag   Git tag to generate changelog since (auto-detected if not provided)"
    echo ""
    echo "Examples:"
    echo "  $0 1.2.0                  # Generate changelog for v1.2.0 since last tag"
    echo "  $0 1.2.0 v1.1.0           # Generate changelog for v1.2.0 since v1.1.0"
    echo "  $0                        # Generate draft changelog since last tag"
    echo ""
    exit 0
fi

# Run main function
main "$@"
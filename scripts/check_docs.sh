#!/bin/bash
# Documentation validation script
# Run this locally before committing, or it runs automatically in CI

set -e

echo "🔍 Checking documentation consistency..."

# Check 1: All active modules must have README.md
echo "✓ Checking module READMEs..."
modules_in_main=("example" "transcripts" "projects" "autonomy_guard" "record" "console" "privacy_shield")
missing_readme=()

for module in "${modules_in_main[@]}"; do
    if [ -d "backend/app/modules/$module" ]; then
        if [ ! -f "backend/app/modules/$module/README.md" ]; then
            missing_readme+=("$module")
        fi
    fi
done

if [ ${#missing_readme[@]} -ne 0 ]; then
    echo "❌ ERROR: Modules missing README.md: ${missing_readme[*]}"
    exit 1
else
    echo "✅ All active modules have README.md"
fi

# Check 2: Required core documentation exists
echo "✓ Checking required documentation..."
required_docs=(
    "README.md"
    "docs/core.md"
    "docs/frontend.md"
    "docs/architecture.md"
    "docs/getting-started.md"
)

missing_docs=()
for doc in "${required_docs[@]}"; do
    if [ ! -f "$doc" ]; then
        missing_docs+=("$doc")
    fi
done

if [ ${#missing_docs[@]} -ne 0 ]; then
    echo "❌ ERROR: Missing required documentation: ${missing_docs[*]}"
    exit 1
else
    echo "✅ All required documentation exists"
fi

# Check 3: No orphaned .md files in root (except allowed ones)
echo "✓ Checking root .md files..."
allowed_root_files=("README.md" "CHANGELOG.md" "agent.md" "PROJECT_GUIDE.md")
root_md_files=$(find . -maxdepth 1 -name "*.md" -type f | xargs -n 1 basename)

for file in $root_md_files; do
    if [[ ! " ${allowed_root_files[@]} " =~ " ${file} " ]]; then
        echo "⚠️  WARNING: .md file in root that should be in docs/ or tests/: $file"
        # Don't fail, just warn
    fi
done

echo "✅ Documentation check complete!"


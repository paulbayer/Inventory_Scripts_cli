#!/bin/bash
# Script to install the pre-commit hook for version updates

HOOK_SOURCE=".git/hooks/pre-commit"
HOOK_DIR=".git/hooks"

# Ensure we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: Not in a git repository root directory"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$HOOK_DIR"

# Create the pre-commit hook
cat > "$HOOK_SOURCE" << 'EOF'
#!/bin/bash
# Pre-commit hook to update __version__ with current date in changed files

# Get current date in YYYY.MM.DD format
CURRENT_DATE=$(date +"%Y.%m.%d")

# Get list of staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$STAGED_FILES" ]; then
    echo "No Python files staged for commit."
    exit 0
fi

UPDATED_COUNT=0

# Process each staged file
for FILE in $STAGED_FILES; do
    # Check if file exists and contains __version__
    if [ -f "$FILE" ] && grep -q '__version__' "$FILE"; then
        # Read current version (macOS compatible)
        CURRENT_VERSION=$(grep '__version__' "$FILE" | sed -n 's/.*"\(.*\)".*/\1/p' | head -1)
        
        # Only update if version is different
        if [ "$CURRENT_VERSION" != "$CURRENT_DATE" ]; then
            echo "Updating version in $FILE from $CURRENT_VERSION to $CURRENT_DATE"
            
            # Update the version in the file (macOS requires '' after -i)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/__version__ = \".*\"/__version__ = \"$CURRENT_DATE\"/" "$FILE"
            else
                sed -i "s/__version__ = \".*\"/__version__ = \"$CURRENT_DATE\"/" "$FILE"
            fi
            
            # Stage the updated file
            git add "$FILE"
            
            UPDATED_COUNT=$((UPDATED_COUNT + 1))
        fi
    fi
done

if [ $UPDATED_COUNT -gt 0 ]; then
    echo "Successfully updated version in $UPDATED_COUNT file(s)!"
else
    echo "All versions are already current: $CURRENT_DATE"
fi

exit 0
EOF

# Make the hook executable
chmod +x "$HOOK_SOURCE"

echo "Pre-commit hook installed successfully!"
echo "The hook will automatically update __version__ in any staged Python files that contain it."
echo ""
echo "To test it, try modifying a file with __version__ and commit it."

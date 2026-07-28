#!/usr/bin/env bash
set -euo pipefail

MANIFEST="custom_components/resideo_firstalert/manifest.json"

current_version=$(python3 -c "import json; print(json.load(open('$MANIFEST'))['version'])")

if [ -z "${1:-}" ]; then
    IFS='.' read -r major minor patch <<< "$current_version"
    new_version="$major.$((minor + 1)).0"
    echo "Current version: $current_version"
    echo "Next version:    $new_version (bump minor)"
    echo ""
    read -rp "Use $new_version? (enter a different version or press Enter to confirm): " input
    new_version="${input:-$new_version}"
else
    new_version="$1"
fi

if [ "$new_version" = "$current_version" ]; then
    echo "Error: new version is the same as current ($current_version)"
    exit 1
fi

echo "Bumping $current_version -> $new_version"

python3 -c "
import json
with open('$MANIFEST', 'r') as f:
    data = json.load(f)
data['version'] = '$new_version'
with open('$MANIFEST', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
"

git add "$MANIFEST"
git commit -m "Bump version to $new_version"
git push

echo ""
echo "Triggering release workflow for v$new_version..."
gh workflow run release.yml -f version="$new_version"

echo ""
echo "Done! Release v$new_version is being created."
echo "Check progress: gh run list --workflow=release.yml"

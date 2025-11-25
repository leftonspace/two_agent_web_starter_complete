#!/bin/bash
# JARVIS External Tools Deployment Script
# Replaces placeholder URLs in configuration files
#
# Usage: ./deploy.sh <base_url>
# Example: ./deploy.sh https://jarvis.yourcompany.com

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check arguments
if [ -z "$1" ]; then
    echo -e "${RED}Error: Base URL required${NC}"
    echo ""
    echo "Usage: $0 <base_url>"
    echo "Example: $0 https://jarvis.yourcompany.com"
    echo ""
    echo "This script replaces \${JARVIS_BASE_URL} placeholders in:"
    echo "  - gmail-addon/appsscript.json"
    echo "  - outlook-addin/manifest.xml"
    exit 1
fi

BASE_URL="$1"

# Validate URL format
if [[ ! "$BASE_URL" =~ ^https?:// ]]; then
    echo -e "${YELLOW}Warning: URL should start with https:// for production${NC}"
fi

# Remove trailing slash if present
BASE_URL="${BASE_URL%/}"

echo "=============================================="
echo "  JARVIS External Tools Deployment"
echo "=============================================="
echo ""
echo "Base URL: $BASE_URL"
echo ""

# Function to replace placeholders in a file
replace_placeholders() {
    local file="$1"
    local backup="${file}.bak"

    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}  Skipped: $file (not found)${NC}"
        return
    fi

    # Count placeholders before replacement
    local count=$(grep -o '\${JARVIS_BASE_URL}' "$file" 2>/dev/null | wc -l)

    if [ "$count" -eq 0 ]; then
        echo -e "${YELLOW}  Skipped: $file (no placeholders found)${NC}"
        return
    fi

    # Create backup
    cp "$file" "$backup"

    # Replace placeholders
    sed -i "s|\\\${JARVIS_BASE_URL}|${BASE_URL}|g" "$file"

    echo -e "${GREEN}  Updated: $file ($count replacements)${NC}"
}

# Process Gmail Add-on
echo "Processing Gmail Add-on..."
replace_placeholders "${SCRIPT_DIR}/gmail-addon/appsscript.json"

# Process Outlook Add-in
echo ""
echo "Processing Outlook Add-in..."
replace_placeholders "${SCRIPT_DIR}/outlook-addin/manifest.xml"

echo ""
echo "=============================================="
echo -e "${GREEN}  Deployment configuration complete!${NC}"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Verify the changes in each configuration file"
echo "  2. Ensure icon files are hosted at:"
echo "     - ${BASE_URL}/assets/icon-16.png"
echo "     - ${BASE_URL}/assets/icon-32.png"
echo "     - ${BASE_URL}/assets/icon-64.png"
echo "     - ${BASE_URL}/assets/icon-80.png"
echo "     - ${BASE_URL}/assets/icon-128.png"
echo "  3. Deploy each add-on following DEPLOYMENT_GUIDE.md"
echo ""
echo "To restore original files (with placeholders):"
echo "  mv gmail-addon/appsscript.json.bak gmail-addon/appsscript.json"
echo "  mv outlook-addin/manifest.xml.bak outlook-addin/manifest.xml"

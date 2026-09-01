#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS="$ROOT/tools"
SITE="$ROOT/site"
VERSION="1.4.25"

JAR="$TOOLS/widoco-${VERSION}-jar-with-dependencies.jar"
URL="https://github.com/dgarijo/Widoco/releases/download/v${VERSION}/widoco-${VERSION}-jar-with-dependencies.jar"

ONTOLOGY="$ROOT/ontology/mexo-publication.ttl"
CONFIG="$ROOT/widoco/config.properties"

# ----------------------------------------------------------------------
# Pre-flight checks
# ----------------------------------------------------------------------

if ! command -v java >/dev/null 2>&1; then
  echo "ERROR: Java was not found."
  echo
  echo "On macOS with Homebrew, install Java 17 with:"
  echo "  brew install openjdk@17"
  echo
  echo "On Apple Silicon, if java is still not found, run:"
  echo '  echo '\''export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"'\'' >> ~/.zshrc'
  echo "  source ~/.zshrc"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl was not found."
  exit 1
fi

if [[ ! -f "$ONTOLOGY" ]]; then
  echo "ERROR: Ontology publication file not found:"
  echo "  $ONTOLOGY"
  exit 1
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "ERROR: WIDOCO configuration file not found:"
  echo "  $CONFIG"
  exit 1
fi

echo "Using Java:"
java -version
echo

# ----------------------------------------------------------------------
# Prepare directories
# ----------------------------------------------------------------------

mkdir -p "$TOOLS"

rm -rf "$SITE"
mkdir -p "$SITE"

# ----------------------------------------------------------------------
# Download WIDOCO if necessary
# ----------------------------------------------------------------------

if [[ ! -f "$JAR" ]]; then
  echo "Downloading WIDOCO ${VERSION}..."
  curl -fL "$URL" -o "$JAR"
fi

if [[ ! -s "$JAR" ]]; then
  echo "ERROR: WIDOCO JAR is missing or empty:"
  echo "  $JAR"
  exit 1
fi

# ----------------------------------------------------------------------
# Generate documentation
# ----------------------------------------------------------------------

echo
echo "Generating MEXO documentation with WIDOCO ${VERSION}..."
echo "Ontology: $ONTOLOGY"
echo "Output:   $SITE"
echo

java -jar "$JAR" \
  -ontFile "$ONTOLOGY" \
  -outFolder "$SITE" \
  -confFile "$CONFIG" \
  -rewriteAll \
  -webVowl \
  -uniteSections \
  -lang en

# ----------------------------------------------------------------------
# Normalize output for GitHub Pages
#
# MEXO uses a slash namespace:
#   https://w3id.org/mexo/
#
# WIDOCO may therefore generate the documentation under site/doc/.
# GitHub Pages should expose the documentation directly from site/.
# ----------------------------------------------------------------------

if [[ -d "$SITE/doc" ]]; then
  echo
  echo "Slash namespace detected: moving generated documentation from site/doc/ to site/..."
  cp -a "$SITE/doc/." "$SITE/"
fi

# Prevent Jekyll processing when site/ is deployed with GitHub Pages.
touch "$SITE/.nojekyll"

# GitHub Pages expects an index.html at the root.
if [[ ! -f "$SITE/index.html" && -f "$SITE/index-en.html" ]]; then
  cp "$SITE/index-en.html" "$SITE/index.html"
fi

# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------

if [[ ! -f "$SITE/index.html" && ! -f "$SITE/index-en.html" ]]; then
  echo
  echo "ERROR: WIDOCO finished without producing an HTML index page."
  echo "Generated files:"
  find "$SITE" -maxdepth 3 -type f -print || true
  exit 1
fi

if [[ ! -d "$SITE/resources" ]]; then
  echo
  echo "WARNING: No resources/ directory was found."
  echo "The documentation may be incomplete."
fi

if [[ ! -d "$SITE/webvowl" ]]; then
  echo
  echo "WARNING: No webvowl/ directory was found."
  echo "WIDOCO may have completed without generating the WebVOWL visualization."
fi

# ----------------------------------------------------------------------
# Result
# ----------------------------------------------------------------------

echo
echo "WIDOCO documentation generated successfully."
echo
echo "Publication directory:"
echo "  $SITE"
echo
echo "Main page:"
if [[ -f "$SITE/index.html" ]]; then
  echo "  $SITE/index.html"
else
  echo "  $SITE/index-en.html"
fi

echo
echo "Preview locally with:"
echo "  python3 -m http.server 8000 --directory \"$SITE\""
echo
echo "Then open:"
echo "  http://localhost:8000/"

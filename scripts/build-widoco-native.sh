#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS="$ROOT/tools"
SITE="$ROOT/site"
VERSION="1.4.25"
JAR="$TOOLS/widoco-${VERSION}-jar-with-dependencies.jar"
URL="https://github.com/dgarijo/Widoco/releases/download/v${VERSION}/widoco-${VERSION}-jar-with-dependencies.jar"

if ! command -v java >/dev/null 2>&1; then
  echo "Java was not found."
  echo "On macOS with Homebrew, install it with:"
  echo "  brew install openjdk@17"
  exit 1
fi

mkdir -p "$TOOLS"
rm -rf "$SITE"
mkdir -p "$SITE"

if [[ ! -f "$JAR" ]]; then
  echo "Downloading WIDOCO ${VERSION}..."
  curl -fL "$URL" -o "$JAR"
fi

java -jar "$JAR" \
  -ontFile "$ROOT/ontology/mexo-publication.ttl" \
  -outFolder "$SITE" \
  -confFile "$ROOT/widoco/config.properties" \
  -rewriteAll \
  -webVowl \
  -uniteSections \
  -lang en

touch "$SITE/.nojekyll"

echo
echo "WIDOCO documentation generated natively in: $SITE"
echo "Preview with:"
echo "  python3 -m http.server 8000 --directory \"$SITE\""
echo "Then open http://localhost:8000/"

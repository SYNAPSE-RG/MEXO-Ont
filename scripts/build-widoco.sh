#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="$ROOT/site"

rm -rf "$SITE"
mkdir -p "$SITE"

docker pull ghcr.io/dgarijo/widoco:v1.4.25

docker run --rm \
  -v "$ROOT/ontology:/usr/local/widoco/in:ro" \
  -v "$SITE:/usr/local/widoco/out" \
  -v "$ROOT/widoco:/usr/local/widoco/conf:ro" \
  ghcr.io/dgarijo/widoco:v1.4.25 \
  -ontFile in/mexo-publication.ttl \
  -outFolder out \
  -confFile conf/config.properties \
  -rewriteAll \
  -webVowl \
  -uniteSections \
  -lang en

touch "$SITE/.nojekyll"

echo
echo "WIDOCO documentation generated in: $SITE"
echo "Preview locally with:"
echo "  python3 -m http.server 8000 --directory \"$SITE\""
echo "Then open http://localhost:8000/"

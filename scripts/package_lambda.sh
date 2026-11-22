#!/usr/bin/env bash
# Build lambda.zip for the ingestion function (deployed by infra/terraform).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build/lambda"
rm -rf "$BUILD" && mkdir -p "$BUILD"
pip install --quiet --target "$BUILD" \
  --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12 \
  "sqlalchemy>=2.0" "psycopg[binary]>=3.1" "httpx>=0.27" "pydantic-settings>=2.2"
cp -r "$ROOT/backend/app" "$ROOT/backend/ingestion" "$BUILD/"
(cd "$BUILD" && zip -qr "$ROOT/lambda.zip" .)
echo "Built $ROOT/lambda.zip"

#!/usr/bin/env bash
# Rebuild datasets, charts (zh/en), Markdown parts and the two Word documents.
set -euo pipefail
cd "$(dirname "$0")"
python3 build_datasets.py
python3 charts_rates.py
python3 charts_banks.py
python3 ipo_fees.py
python3 build_report_parts.py
python3 build_docx.py

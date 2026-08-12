---
name: data-profiler
description: Perform comprehensive exploratory data analysis (EDA) on tabular datasets (CSV, TSV, Parquet, Feather, ORC, JSON/JSONL, Excel) and generate statistical reports.
license: MIT
compatibility: opencode
metadata:
  domain: data-engineering
  task: eda-profiling
---

# Data Profiler Skill

Use this skill when you need to conduct exploratory data analysis (EDA) on a dataset before performing preprocessing, feature engineering, or modeling.

## Supported Formats

Explicitly supported tabular dataset formats:
- `.csv`, `.tsv` (Comma/Tab separated text)
- `.parquet`, `.feather`, `.orc` (Columnar data formats)
- `.json`, `.jsonl` (Structured JSON objects/lines)
- `.xlsx`, `.xls` (Spreadsheets)

## How to Execute

To profile a dataset, execute the bundled Python profiling engine script using `run_command` or bash:

```bash
python ~/.config/opencode/skills/data-profiler/scripts/profile_dataset.py --dataset-path path/to/dataset.csv
```

### CLI Options:

- `--dataset-path`: Path to the input dataset file (required).
- `--target`: Name of the target variable column (optional).
- `--task-type`: Task type resolution (`auto`, `classification`, `regression`; default: `auto`).
- `--problem-statement`: Problem description text to assist target & task type resolution (optional).
- `--output-dir`: Output directory for generated Markdown reports (default: `data/eda/` with fallback to `data/scratch/`).

## Expected Output

The script outputs a single line to STDOUT:
`Report generated at <report_path>. Proceed to read the report file for full findings.`

After execution, read the generated `.md` report using `view_file` to review:
1. Data Overview (dimensions, memory usage, head preview if sub-20 columns).
2. Schema & Null Count Table (`.info` replacement).
3. Summary Statistics Table (`.describe` replacement).
4. Target Variable & Class Imbalance Analysis (if classification).
5. Feature Correlation Matrix & Top Correlated Pairs (using Dask or out-of-core NumPy memmap for datasets with >100 columns).

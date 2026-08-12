import argparse
import gc
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import numpy.typing as npt
import pandas as pd


class BadEnvironmentError(Exception):
    """Raised when running under a base system Python executable instead of a virtual environment."""

    pass


def ensure_dependencies() -> None:
    """Ensures required third-party Python packages are installed in the venv using uv or pip."""
    
    def _get_conditions(exe_path: Path) -> Tuple[bool, bool, bool]:
        parts_lower: List[str] = [p.lower() for p in exe_path.parts]

        is_system_appdata: bool = ("appdata" in parts_lower) and ("local" in parts_lower)
        is_venv: bool = (".venv" in parts_lower) or ("venv" in parts_lower)
        is_conda: bool = (
            ("miniconda" in parts_lower)
            or ("anaconda" in parts_lower)
            or ("conda" in parts_lower)
        )

        return (is_system_appdata, is_venv, is_conda)
        
    def _get_cmd(
        conditions_list: Tuple[bool, bool, bool],
        exe_path: Path,
        missing_packages: List[str]
    ) -> List[str]:
        """Helper to construct the executed install command.

        Args:
            conditions_list (Tuple[bool]): List of environment detection outputs, 
            (is_system_appdata, is_venv, is_conda).
            exe_path (Path): python executable path.
            missing_packages (List[str]): Constructed list of missing packages/libraries.

        Raises:
            BadEnvironmentError: A custom error class with an informative name, since the
            output is read by agents.
        """
        is_system_appdata, is_venv, is_conda = conditions_list

        if is_system_appdata:
            raise BadEnvironmentError(
                f"Agent is running in a system executable ({exe_path}). "
                "Please try again after using a virtual environment (.venv or conda)."
            )

        if is_venv:
            return ["uv", "pip", "install", "--python", str(exe_path), *missing_packages]
        elif is_conda:
            return [sys.executable, "-m", "pip", "install", *missing_packages]
        else:
            uv_bin: Optional[str] = shutil.which("uv")
            if uv_bin:
                return [uv_bin, "pip", "install", "--python", str(exe_path), *missing_packages]
            else:
                return [sys.executable, "-m", "pip", "install", *missing_packages]

    required_packages: List[str] = [
        "pyarrow",
        "pandas",
        "polars",
        "dask",
        "psutil",
        "tabulate",
    ]
    missing_packages: List[str] = []

    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing_packages.append(pkg)

    if missing_packages:
        exe_path: Path = Path(sys.executable)

        conditions_list: Tuple[bool, bool, bool] = _get_conditions(exe_path)
        cmd: List[str] = _get_cmd(conditions_list, exe_path, missing_packages)

        print(f"Installing missing dependencies {missing_packages} via: {' '.join(cmd)}")
        subprocess.check_call(cmd)


ensure_dependencies()

import dask.array as da
import dask.dataframe as dd
import psutil


def load_dataset(file_path: Path) -> pd.DataFrame:
    """Loads dataset into a pandas DataFrame using pyarrow or appropriate engine."""
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")

    ext: str = file_path.suffix.lower()

    if ext in [".csv", ".txt"]:
        # Check if file is semicolon-separated by examining first line
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if ';' in first_line and ',' not in first_line:
                    # Semicolon-separated file
                    try:
                        return pd.read_csv(file_path, sep=';', engine="pyarrow")
                    except Exception:
                        return pd.read_csv(file_path, sep=';')
                else:
                    # Regular CSV
                    try:
                        return pd.read_csv(file_path, engine="pyarrow")
                    except Exception:
                        return pd.read_csv(file_path)
        except Exception:
            # Fallback to regular CSV reading
            try:
                return pd.read_csv(file_path, engine="pyarrow")
            except Exception:
                return pd.read_csv(file_path)

    if ext == ".tsv":
        try:
            return pd.read_csv(file_path, sep="\t", engine="pyarrow")
        except Exception:
            return pd.read_csv(file_path, sep="\t")

    if ext == ".parquet":
        return pd.read_parquet(file_path, engine="pyarrow")

    if ext == ".feather":
        return pd.read_feather(file_path)

    if ext == ".orc":
        return pd.read_orc(file_path)

    if ext in [".json", ".jsonl"]:
        lines_flag: bool = ext == ".jsonl"
        try:
            return pd.read_json(file_path, lines=lines_flag, engine="pyarrow")
        except Exception:
            return pd.read_json(file_path, lines=lines_flag)

    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)

    raise ValueError(f"Unsupported dataset format: {ext}")


def chunked_memmap_corr(
    data_matrix: Union[np.ndarray, np.memmap],
    chunk_size: int = 2000,
    filename: str = "corr_matrix.dat",
) -> np.memmap:
    """Computes a correlation matrix out-of-core using NumPy memmap."""
    n_samples: int
    n_features: int
    n_samples, n_features = data_matrix.shape

    mean: npt.NDArray[np.float64] = np.mean(data_matrix, axis=0)
    std: npt.NDArray[np.float64] = np.std(data_matrix, axis=0)
    std[std == 0.0] = 1.0

    fp: np.memmap = np.memmap(
        filename, dtype="float32", mode="w+", shape=(n_features, n_features)
    )

    for i in range(0, n_features, chunk_size):
        end_i: int = min(i + chunk_size, n_features)
        chunk_i: np.ndarray = (
            data_matrix[:, i:end_i] - mean[i:end_i]
        ) / std[i:end_i]

        for j in range(i, n_features, chunk_size):
            end_j: int = min(j + chunk_size, n_features)
            chunk_j: np.ndarray = (
                data_matrix[:, j:end_j] - mean[j:end_j]
            ) / std[j:end_j]

            block_corr: np.ndarray = (chunk_i.T @ chunk_j) / n_samples
            fp[i:end_i, j:end_j] = block_corr

            if i != j:
                fp[j:end_j, i:end_i] = block_corr.T

        fp.flush()
        gc.collect()

    return fp


def dask_fast_corr(
    csv_filepath: Path, target_columns: Optional[List[str]] = None
) -> npt.NDArray[np.float64]:
    """Computes a correlation matrix using Dask's lazy evaluation graph."""
    df: dd.DataFrame = dd.read_csv(str(csv_filepath), blocksize="128MB")

    if target_columns:
        df = df[target_columns]

    df_mean: dd.Series = df.mean()
    df_std: dd.Series = df.std()
    df_scaled: dd.DataFrame = (df - df_mean) / df_std

    dask_arr: da.Array = df_scaled.to_dask_array(lengths=True)
    n_samples: int = dask_arr.shape[0]

    corr_graph: da.Array = (dask_arr.T @ dask_arr) / n_samples
    final_corr_matrix: npt.NDArray[np.float64] = corr_graph.compute()

    return final_corr_matrix


def resolve_target_column(
    df: pd.DataFrame,
    target_arg: Optional[str] = None,
    problem_statement: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Resolves target column name and logs any ambiguity."""
    if target_arg and target_arg in df.columns:
        return target_arg, None

    candidate_names: List[str] = ["target", "label", "class"]
    matched_cols: List[str] = [
        col for col in df.columns if col.lower() in candidate_names
    ]

    if len(matched_cols) == 1:
        return matched_cols[0], None

    if len(matched_cols) > 1:
        msg: str = (
            f"Escalation: Multiple target candidate columns found {matched_cols}. "
            "Please specify --target explicitly."
        )
        return None, msg

    if problem_statement:
        ps_lower: str = problem_statement.lower()
        statement_matches: List[str] = [
            col for col in df.columns if col.lower() in ps_lower
        ]

        if len(statement_matches) == 1:
            return statement_matches[0], None

        if len(statement_matches) > 1:
            msg = (
                f"Escalation: Multiple columns {statement_matches} match problem statement. "
                "Please specify --target explicitly."
            )
            return None, msg

    return None, None


def resolve_task_type(
    df: pd.DataFrame,
    target_col: Optional[str],
    task_type_arg: str,
    problem_statement: Optional[str],
) -> str:
    """Deterministically resolves task type as classification or regression."""
    if task_type_arg in ["classification", "regression"]:
        return task_type_arg

    if not target_col or target_col not in df.columns:
        return "unknown"

    target_series: pd.Series = df[target_col]
    total_rows: int = len(df)
    n_unique: int = target_series.nunique()
    is_non_numeric: bool = not pd.api.types.is_numeric_dtype(target_series)
    is_low_cardinality_ratio: bool = (total_rows >= 20) and (
        (n_unique / total_rows) < 0.05
    )

    if is_non_numeric or is_low_cardinality_ratio:
        return "classification"

    if problem_statement:
        classification_keywords: List[str] = [
            "classifi",
            "label",
            "category",
            "churn",
            "fraud",
            "anomaly",
            "binary",
            "multiclass",
        ]
        has_keyword: bool = any(
            kw in problem_statement.lower() for kw in classification_keywords
        )
        if has_keyword:
            return "classification"

    return "regression"


def compute_correlation_analysis(
    df: pd.DataFrame, file_path: Path, output_dir: Path
) -> Tuple[List[str], Optional[Path]]:
    """Computes feature correlations and returns top pairs summary & artifact path."""
    numeric_df: pd.DataFrame = df.select_dtypes(include=[np.number]).dropna()
    n_features: int = len(numeric_df.columns)

    if n_features < 2:
        return ["Insufficient numeric features for correlation matrix."], None

    matrix_file: Optional[Path] = None
    corr_matrix: np.ndarray

    if n_features <= 100:
        corr_matrix = numeric_df.corr().to_numpy()
    else:
        dataset_bytes: int = numeric_df.values.nbytes
        available_ram: int = psutil.virtual_memory().available
        has_sufficient_ram: bool = available_ram > (2 * dataset_bytes)

        if has_sufficient_ram and file_path.suffix.lower() == ".csv":
            corr_matrix = dask_fast_corr(
                file_path, target_columns=list(numeric_df.columns)
            )
        else:
            matrix_file = output_dir / f"{file_path.stem}_corr.dat"
            corr_matrix = chunked_memmap_corr(
                numeric_df.to_numpy(), filename=str(matrix_file)
            )

    top_pairs: List[Tuple[str, str, float]] = []
    cols: List[str] = list(numeric_df.columns)

    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val: float = float(corr_matrix[i, j])
            if abs(val) >= 0.7 and not np.isnan(val):
                top_pairs.append((cols[i], cols[j], val))

    top_pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    summary_lines: List[str] = []
    if not top_pairs:
        summary_lines.append("No feature pairs found with |r| >= 0.7.")
    else:
        summary_lines.append("| Feature 1 | Feature 2 | Correlation |")
        summary_lines.append("| --- | --- | --- |")
        for f1, f2, r_val in top_pairs[:20]:
            summary_lines.append(f"| {f1} | {f2} | {r_val:.4f} |")

    return summary_lines, matrix_file


def generate_markdown_report(
    df: pd.DataFrame,
    file_path: Path,
    target_col: Optional[str],
    task_type: str,
    escalation_msg: Optional[str],
    corr_lines: List[str],
    corr_artifact: Optional[Path],
    output_dir: Path,
) -> Path:
    """Generates comprehensive EDA report in Markdown format."""
    dataset_name: str = file_path.stem
    report_path: Path = output_dir / f"{dataset_name}.md"

    lines: List[str] = [
        f"# Exploratory Data Analysis Report: `{file_path.name}`",
        "",
        "## 1. Overview",
        f"- **Source File**: `{file_path.resolve()}`",
        f"- **Rows**: {len(df):,}",
        f"- **Columns**: {len(df.columns):,}",
        f"- **Memory Usage**: {df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB",
        "",
    ]

    if len(df.columns) < 20:
        lines.extend([
            "### Data Preview (.head)",
            df.head(5).to_markdown(index=False),
            "",
        ])

    lines.extend([
        "## 2. Schema & Null Analysis (.info)",
        "| Column | Data Type | Non-Null Count | Null Count | Null % |",
        "| --- | --- | --- | --- | --- |",
    ])

    for col in df.columns:
        null_cnt: int = int(df[col].isnull().sum())
        non_null_cnt: int = len(df) - null_cnt
        null_pct: float = (null_cnt / len(df)) * 100.0
        lines.append(
            f"| `{col}` | `{df[col].dtype}` | {non_null_cnt:,} | {null_cnt:,} | {null_pct:.2f}% |"
        )

    lines.extend([
        "",
        "## 3. Summary Statistics (.describe)",
        df.describe(include="all").T.to_markdown(),
        "",
        "## 4. Target Variable & Task Analysis",
    ])

    if escalation_msg:
        lines.append(f"> [!WARNING]\n> {escalation_msg}\n")

    if target_col:
        lines.extend([
            f"- **Identified Target Column**: `{target_col}`",
            f"- **Resolved Task Type**: `{task_type}`",
            "",
        ])

        if task_type == "classification":
            vc: pd.Series = df[target_col].value_counts(dropna=False)
            vc_df: pd.DataFrame = pd.DataFrame(
                {"Count": vc, "Percentage": (vc / len(df)) * 100.0}
            )

            lines.extend([
                "### Class Distribution",
                vc_df.to_markdown(),
                "",
            ])

            if len(vc) > 1:
                maj_cnt: int = int(vc.iloc[0])
                min_cnt: int = int(vc.iloc[-1])
                ratio: float = maj_cnt / max(min_cnt, 1)

                is_imbalanced: bool = (ratio > 4.0) or ((min_cnt / len(df)) < 0.10)
                if is_imbalanced:
                    lines.append(
                        f"> [!WARNING]\n> Class imbalance detected! Majority/Minority Ratio: `{ratio:.2f}:1`. Minority class ratio: `{(min_cnt/len(df))*100:.2f}%`.\n"
                    )
    else:
        lines.append("- Target column not specified or auto-detected.")

    lines.extend([
        "",
        "## 5. Feature Correlation Analysis",
    ])

    if corr_artifact:
        lines.append(
            f"- Large matrix (>100 cols) saved to out-of-core artifact: `{corr_artifact.resolve()}`"
        )

    lines.extend(corr_lines)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exploratory Data Analysis (EDA) Dataset Profiler Engine"
    )
    parser.add_argument(
        "--dataset-path", required=True, type=str, help="Path to tabular dataset"
    )
    parser.add_argument(
        "--target", type=str, default=None, help="Target variable column name"
    )
    parser.add_argument(
        "--task-type",
        type=str,
        default="auto",
        choices=["auto", "classification", "regression"],
        help="Task type resolution",
    )
    parser.add_argument(
        "--problem-statement",
        type=str,
        default=None,
        help="Problem description context",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/eda",
        help="Directory to save report",
    )

    args = parser.parse_args()

    file_path: Path = Path(args.dataset_path)
    output_dir: Path = Path(args.output_dir)

    try:
        df: pd.DataFrame = load_dataset(file_path)
    except Exception as err:
        output_dir = Path("data/scratch")
        output_dir.mkdir(parents=True, exist_ok=True)
        err_report: Path = output_dir / f"{file_path.stem}_error.md"
        err_report.write_text(f"# EDA Failed\n\nError: {err}")
        print(f"Report generated at {err_report}. Proceed to read the report file for full findings.")
        sys.exit(0)

    target_col, escalation_msg = resolve_target_column(
        df, target_arg=args.target, problem_statement=args.problem_statement
    )
    task_type: str = resolve_task_type(
        df,
        target_col=target_col,
        task_type_arg=args.task_type,
        problem_statement=args.problem_statement,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    corr_lines, corr_artifact = compute_correlation_analysis(
        df, file_path=file_path, output_dir=output_dir
    )

    report_path: Path = generate_markdown_report(
        df=df,
        file_path=file_path,
        target_col=target_col,
        task_type=task_type,
        escalation_msg=escalation_msg,
        corr_lines=corr_lines,
        corr_artifact=corr_artifact,
        output_dir=output_dir,
    )

    print(f"Report generated at {report_path}. Proceed to read the report file for full findings.")


if __name__ == "__main__":
    main()

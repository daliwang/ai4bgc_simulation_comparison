#!/usr/bin/env python3
"""Standard ELM h0 comparison: aggregate, time series, and one-year maps.

The global sum is land only (landmask == 1), drop longitudes 0 and 358.75, then
sum(data * area * landfrac). Fluxes whose units end in gC/m^2/s are
multiplied by the seconds in a year and labeled tonC/km^2/year.

The year in a history name is the model year in the filename.
h0.0021-01-01-00000.nc is year 21 (the usual 20-year snapshot).
h0.0101 is year 101. h0.0201 is year 201.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

SECONDS_PER_YEAR = 365 * 24 * 3600
DEFAULT_EXCLUDE_LONS = (0.0, 358.75)
H0_YEAR = re.compile(r"\.elm\.h0\.(\d{4})-")

TIMESERIES_VARIABLES = [
    "NEE", "GPP", "HR", "TLAI", "TOTCOLC", "SOIL1C",
    "SOIL2C", "SOIL3C", "SOIL4C", "TOTSOMC", "CWDC", "DEADSTEMC",
    "LABILEP", "SECONDP", "OCCLP", "PRIMP",
]
MAP_VARIABLES = [
    "CWDC", "DEADSTEMC", "GPP", "HR", "NEE", "SOIL1C",
    "SOIL2C", "SOIL3C", "SOIL4C", "TLAI", "TOTCOLC", "TOTSOMC",
]

MAP_SCRIPT = Path(__file__).resolve().parent / "map_plot_h0_comparison.py"


def _table_name(variable: str) -> str:
    return f"new_twenty_year_sum_{variable.lower()}_data.txt"


def find_h0_files(run_dir: Path, start_year: int | None, end_year: int | None) -> list[tuple[int, Path]]:
    if not run_dir.is_dir():
        raise SystemExit(f"Run directory does not exist: {run_dir}")
    found: list[tuple[int, Path]] = []
    for path in sorted(run_dir.iterdir()):
        if not path.is_file() or not path.name.endswith(".nc") or ".elm.h0." not in path.name:
            continue
        match = H0_YEAR.search(path.name)
        if not match:
            continue
        year = int(match.group(1))
        if start_year is not None and year < start_year:
            continue
        if end_year is not None and year > end_year:
            continue
        found.append((year, path))
    if not found:
        raise SystemExit(
            f"No *.elm.h0.*.nc files in {run_dir}"
            + (f" for years {start_year}–{end_year}." if start_year is not None or end_year is not None else ".")
            + " Pass the directory that contains the history files."
        )
    by_year: dict[int, Path] = {}
    for year, path in found:
        if year in by_year:
            raise SystemExit(
                f"Two history files for year {year:04d} in {run_dir}:\n"
                f"  {by_year[year].name}\n  {path.name}"
            )
        by_year[year] = path
    return sorted(by_year.items())


def _exclude_columns(lon_vals: np.ndarray, exclude_lons: tuple[float, ...]) -> np.ndarray:
    lon_1d = lon_vals[0, :] if lon_vals.ndim > 1 else lon_vals
    exclude_cols = np.zeros(lon_1d.shape, dtype=bool)
    for ex_lon in exclude_lons:
        exclude_cols |= np.isclose(lon_1d, ex_lon, atol=1e-2)
    return exclude_cols


def global_sum(ds, variable: str, exclude_lons: tuple[float, ...]) -> tuple[float, str, str]:
    """Return (sum, display_unit, area_units) using the historical formula."""
    import xarray as xr  # local import keeps --help usable without xarray

    del xr
    if variable not in ds.variables:
        raise KeyError(variable)
    var = ds[variable]
    data = np.asarray(var.values, dtype=float)
    if data.ndim == 3:
        data = np.nanmean(data, axis=0)

    area = np.asarray(ds["area"].values, dtype=float)
    landfrac = np.asarray(ds["landfrac"].values, dtype=float)
    landmask = np.asarray(ds["landmask"].values)
    units = var.attrs.get("units", "") or ""
    area_units = ds["area"].attrs.get("units", "") or ""

    mask = landmask == 1
    data = np.where(mask, data, np.nan)
    area_eff = area.copy()
    landfrac_eff = landfrac.copy()
    if "lon" in ds.variables and exclude_lons:
        exclude_cols = _exclude_columns(np.asarray(ds["lon"].values), exclude_lons)
        if data.ndim == 2 and data.shape[1] == exclude_cols.shape[0]:
            data[:, exclude_cols] = np.nan
        if area_eff.ndim == 2 and area_eff.shape[1] == exclude_cols.shape[0]:
            area_eff[:, exclude_cols] = np.nan
        if landfrac_eff.ndim == 2 and landfrac_eff.shape[1] == exclude_cols.shape[0]:
            landfrac_eff[:, exclude_cols] = np.nan

    total = float(np.nansum(data * area_eff * landfrac_eff))
    if units.endswith("gC/m^2/s"):
        total = total * SECONDS_PER_YEAR
        display_unit = "tonC/km^2/year"
    elif units.endswith("gC/m^2"):
        total = total / 1e6 * 1e6
        display_unit = "tonC/km^2"
    else:
        display_unit = units
    return total, display_unit, area_units


def write_table(path: Path, variable: str, display_unit: str, area_units: str, rows: list[tuple[int, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Header spelling matches the existing new_twenty_year_sum_*.txt files.
    lines = [
        f"# Variable: {variable}",
        f"# Varibale Unit: {display_unit}",
        f"# Area units: {area_units}",
        "Year\tSum",
    ]
    for year, value in rows:
        lines.append(f"{year:04d}\t{value}")
    path.write_text("\n".join(lines) + "\n")


def read_table(path: Path) -> tuple[str, str, np.ndarray]:
    text = path.read_text().splitlines()
    if len(text) < 5:
        raise SystemExit(f"Table is missing the 4-line header or has no rows: {path}")
    variable = text[0].split(":", 1)[-1].strip()
    unit = text[1].split(":", 1)[-1].strip()
    data = np.loadtxt(path, skiprows=4)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return variable, unit, data


def aggregate_run(
    run_dir: Path,
    out_dir: Path,
    variables: list[str],
    start_year: int | None,
    end_year: int | None,
    exclude_lons: tuple[float, ...],
) -> list[Path]:
    import xarray as xr

    files = find_h0_files(run_dir, start_year, end_year)
    sums: dict[str, list[tuple[int, float]]] = {name: [] for name in variables}
    units: dict[str, str] = {}
    area_units = ""
    missing: dict[str, list[int]] = {name: [] for name in variables}

    for year, path in files:
        with xr.open_dataset(path) as ds:
            for name in variables:
                if name not in ds.variables:
                    missing[name].append(year)
                    continue
                total, display_unit, area_u = global_sum(ds, name, exclude_lons)
                sums[name].append((year, total))
                units[name] = display_unit
                if area_u:
                    area_units = area_u
        print(f"read {path.name}")

    written: list[Path] = []
    for name in variables:
        if not sums[name]:
            print(f"No data for {name}; skipped.")
            continue
        if missing[name]:
            skipped = ", ".join(f"{year:04d}" for year in missing[name])
            print(f"{name} missing in years: {skipped}")
        out_path = out_dir / _table_name(name)
        write_table(out_path, name, units[name], area_units, sums[name])
        written.append(out_path)
        print(f"wrote {out_path}")
    if not written:
        raise SystemExit(f"None of the requested variables were found under {run_dir}.")
    return written


def plot_timeseries(
    reference_dir: Path,
    reference_label: str,
    case_dir: Path,
    case_label: str,
    variables: list[str],
    plot_dir: Path,
    drop_years: set[int],
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in variables:
        ref_path = reference_dir / _table_name(name)
        case_path = case_dir / _table_name(name)
        if not ref_path.is_file() or not case_path.is_file():
            print(f"Skipping {name}: need both {ref_path.name} tables.")
            continue
        _, unit, ref = read_table(ref_path)
        _, _, case = read_table(case_path)
        ref = ref[~np.isin(ref[:, 0], list(drop_years))]
        case = case[~np.isin(case[:, 0], list(drop_years))]
        if ref.size == 0 or case.size == 0:
            print(f"Skipping {name}: no years left after dropping {sorted(drop_years)}.")
            continue
        fig, ax = plt.subplots()
        ax.plot(ref[:, 0], ref[:, 1], label=reference_label)
        ax.plot(case[:, 0], case[:, 1], label=case_label)
        ax.set_xlabel("Year")
        ax.set_ylabel(unit if unit else "Sum")
        ax.set_title(f"{name} comparison")
        ax.legend()
        fig.tight_layout()
        out_path = plot_dir / f"{name.upper()}_comparison.png"
        fig.savefig(out_path)
        plt.close(fig)
        written.append(out_path)
        print(f"wrote {out_path}")
    if not written:
        raise SystemExit("No comparison plots were written.")
    return written


def h0_for_year(run_dir: Path, year: int) -> Path:
    files = find_h0_files(run_dir, year, year)
    return files[0][1]


def run_maps(
    ai_file: Path,
    model_file: Path,
    variables: list[str],
    out_dir: Path,
    ai_label: str,
    model_label: str,
    exclude_lons: tuple[float, ...],
) -> None:
    if not MAP_SCRIPT.is_file():
        raise SystemExit(f"Map script not found: {MAP_SCRIPT}")
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(MAP_SCRIPT),
        "--latest", str(ai_file),
        "--model", str(model_file),
        "--variables", *variables,
        "--label1", ai_label,
        "--label2", model_label,
        "--output_dir", str(out_dir),
    ]
    if exclude_lons:
        cmd.extend(["--exclude_lons", *[str(lon) for lon in exclude_lons]])
    else:
        cmd.append("--exclude_lons")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def _years(parser_args) -> tuple[int | None, int | None]:
    return parser_args.start_year, parser_args.end_year


def _add_year_args(parser: argparse.ArgumentParser, required: bool) -> None:
    parser.add_argument("--start-year", type=int, required=required, help="First filename year to include, e.g. 1.")
    parser.add_argument("--end-year", type=int, required=required, help="Last filename year to include, e.g. 201.")


def _add_variable_arg(parser: argparse.ArgumentParser, default: list[str]) -> None:
    parser.add_argument(
        "--variables",
        nargs="+",
        default=default,
        help="Variable names (default: the historical set for this command).",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    aggregate = sub.add_parser("aggregate", help="Write new_twenty_year_sum_*.txt from one run directory.")
    aggregate.add_argument("--run-dir", type=Path, required=True)
    aggregate.add_argument("--out-dir", type=Path, required=True)
    _add_year_args(aggregate, required=True)
    _add_variable_arg(aggregate, TIMESERIES_VARIABLES)
    aggregate.add_argument("--exclude-lons", type=float, nargs="*", default=list(DEFAULT_EXCLUDE_LONS))

    series = sub.add_parser("timeseries", help="Aggregate one case and plot it against an existing reference.")
    series.add_argument("--reference-tables", type=Path, required=True, help="Directory of reference new_twenty_year_sum_*.txt files.")
    series.add_argument("--reference-name", required=True, help="Legend label for the reference.")
    series.add_argument("--case-dir", type=Path, required=True, help="Directory of the AI-restart history files.")
    series.add_argument("--case-name", required=True, help="Legend label and output folder name.")
    series.add_argument("--out-dir", type=Path, required=True, help="Parent directory. Tables go in <out-dir>/<case-name>/.")
    _add_year_args(series, required=True)
    _add_variable_arg(series, TIMESERIES_VARIABLES)
    series.add_argument("--drop-years", type=int, nargs="*", default=[1], help="Filename years left off the line plots (default: 1).")
    series.add_argument("--exclude-lons", type=float, nargs="*", default=list(DEFAULT_EXCLUDE_LONS))

    maps = sub.add_parser("maps", help="Three-panel maps of one AI h0 file against the reference h0 file.")
    maps.add_argument("--year", type=int, required=True, help="Filename year, e.g. 21, 101, or 201.")
    maps.add_argument("--ai-dir", type=Path, help="Directory containing the AI-restart h0 file for --year.")
    maps.add_argument("--model-dir", type=Path, help="Directory containing the reference h0 file for --year.")
    maps.add_argument("--ai-file", type=Path, help="AI h0 file. Used instead of --ai-dir.")
    maps.add_argument("--model-file", type=Path, help="Reference h0 file. Used instead of --model-dir.")
    maps.add_argument("--ai-label", default="AI restart")
    maps.add_argument("--model-label", default="Model")
    maps.add_argument("--out-dir", type=Path, required=True)
    _add_variable_arg(maps, MAP_VARIABLES)
    maps.add_argument("--exclude-lons", type=float, nargs="*", default=list(DEFAULT_EXCLUDE_LONS))
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    exclude = tuple(args.exclude_lons)
    if args.command == "aggregate":
        aggregate_run(args.run_dir, args.out_dir, args.variables, *_years(args), exclude)
        return
    if args.command == "timeseries":
        if not args.reference_tables.is_dir():
            raise SystemExit(
                f"Reference tables not found: {args.reference_tables}\n"
                "Run the aggregate command on the model reference first."
            )
        case_tables = args.out_dir / args.case_name
        aggregate_run(args.case_dir, case_tables, args.variables, *_years(args), exclude)
        plot_timeseries(
            args.reference_tables,
            args.reference_name,
            case_tables,
            args.case_name,
            args.variables,
            case_tables / "timeseries",
            set(args.drop_years),
        )
        return
    if args.command == "maps":
        if args.ai_file is None and args.ai_dir is None:
            raise SystemExit("maps needs --ai-file or --ai-dir.")
        if args.model_file is None and args.model_dir is None:
            raise SystemExit("maps needs --model-file or --model-dir.")
        ai_file = args.ai_file if args.ai_file else h0_for_year(args.ai_dir, args.year)
        model_file = args.model_file if args.model_file else h0_for_year(args.model_dir, args.year)
        run_maps(ai_file, model_file, args.variables, args.out_dir, args.ai_label, args.model_label, exclude)
        return
    raise SystemExit(f"Unknown command {args.command}")


if __name__ == "__main__":
    main()

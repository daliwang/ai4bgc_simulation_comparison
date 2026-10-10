import os
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import matplotlib.gridspec as gridspec
from matplotlib.colors import TwoSlopeNorm
import argparse
from datetime import datetime
import glob
import sys


variables = ['CWDC', 'DEADSTEMC', 'GPP', 'HR', 'NEE', 'SOIL1C', 'SOIL2C', 'SOIL3C', 'SOIL4C', 'TLAI', 'TOTCOLC', 'TOTSOMC']
#variables = ['GPP']

# Fixed color limits for variables with small dynamic range (tonC/km^2/year after scaling).
VARIABLE_COLOR_LIMITS = {
    "NEE": {
        "data": (-5.0, 5.0),
        "diff": (-5.0, 5.0),
    },
}

def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    return max(files, key=os.path.getmtime)


def percentile_limits(*arrays, low=2.0, high=98.0):
    """Return (vmin, vmax) from pooled finite values using percentile clipping."""
    pooled = np.concatenate([np.asarray(arr, dtype=float).ravel() for arr in arrays])
    pooled = pooled[np.isfinite(pooled)]
    if pooled.size == 0:
        return 0.0, 1.0
    vmin, vmax = np.nanpercentile(pooled, [low, high])
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
        vmin = float(np.nanmin(pooled))
        vmax = float(np.nanmax(pooled))
        if vmin == vmax:
            vmax = vmin + 1.0
    return float(vmin), float(vmax)


def symmetric_diff_limit(diff, percentile=98.0):
    """Symmetric difference color scale from the percentile of |diff|."""
    valid = np.abs(np.asarray(diff, dtype=float))
    valid = valid[np.isfinite(valid)]
    if valid.size == 0:
        return 1.0
    limit = float(np.nanpercentile(valid, percentile))
    if not np.isfinite(limit) or limit == 0.0:
        limit = float(np.nanmax(valid))
    if limit == 0.0:
        limit = 1.0
    return limit


def get_display_unit_and_scaled(data, var, ds):
    # Try to get area, landfrac, landmask
    area = ds["area"].values if "area" in ds.variables else 1.0
    landfrac = ds["landfrac"].values if "landfrac" in ds.variables else 1.0
    landmask = ds["landmask"].values if "landmask" in ds.variables else None
    units = var.attrs.get("units", "")
    display_unit = units
    # Mask
    if landmask is not None:
        mask = (landmask == 1)
        data = np.where(mask, data, np.nan)
    # Area/landfrac scaling
    weighted = data * area * landfrac
    # Unit conversion
    if units.endswith("gC/m^2/s"):
        weighted = weighted * 365 * 24 * 3600 / 1e6  # gC/m^2/s to gC/m^2/year, then to tonC/km^2/year
        display_unit = "tonC/km^2/year"
    elif units.endswith("gC/m^2"):
        weighted = weighted / 1e6  # gC/m^2 to tonC/km^2
        display_unit = "tonC/km^2"
    return weighted, display_unit





def plot_variable_comparison(
    var,
    data1,
    data2,
    lon,
    lat,
    label1,
    label2,
    save_path,
    unit1,
    unit2,
    exclude_lons=None,
    color_percentiles=None,
):
    # Build longitude mask once and apply to all panels (so AI/Latest and Model also hide 0° etc.)
    mask_cols = None
    if exclude_lons is not None and len(exclude_lons) > 0:
        lon_values = np.asarray(lon)
        lon_1d = lon_values[0, :] if lon_values.ndim > 1 else lon_values
        mask_cols = np.zeros(lon_1d.shape, dtype=bool)
        for ex_lon in exclude_lons:
            mask_cols |= np.isclose(lon_1d, ex_lon, atol=1e-2)
        # Mask data1 and data2 so top two panels (Latest, Model) also show no data at exclude_lons
        if mask_cols.ndim == 1:
            if data1.ndim == 2 and data1.shape[1] == mask_cols.shape[0]:
                data1 = np.where(mask_cols[np.newaxis, :], np.nan, data1)
            if data2.ndim == 2 and data2.shape[1] == mask_cols.shape[0]:
                data2 = np.where(mask_cols[np.newaxis, :], np.nan, data2)
    diff = data1 - data2
    if mask_cols is not None and diff.ndim == 2 and diff.shape[1] == mask_cols.shape[0]:
        diff[:, mask_cols] = np.nan
    fig = plt.figure(figsize=(12, 15))
    gs = gridspec.GridSpec(3, 1, figure=fig, hspace=0.3)
    proj = ccrs.PlateCarree()
    vmin_1 = float(np.nanmin(data1))
    vmax_1 = float(np.nanmax(data1))
    vmin_2 = float(np.nanmin(data2))
    vmax_2 = float(np.nanmax(data2))
    fixed_limits = VARIABLE_COLOR_LIMITS.get(var)
    if fixed_limits is not None:
        vmin_orig, vmax_orig = fixed_limits["data"]
        diff_vmin, diff_vmax = fixed_limits["diff"]
        diff_abs_max = max(abs(diff_vmin), abs(diff_vmax))
        color_limit_note = f"fixed data [{vmin_orig:g}, {vmax_orig:g}], diff [{diff_vmin:g}, {diff_vmax:g}]"
    elif color_percentiles is not None:
        p_low, p_high = color_percentiles
        vmin_orig, vmax_orig = percentile_limits(data1, data2, low=p_low, high=p_high)
        diff_abs_max = symmetric_diff_limit(diff, percentile=p_high)
        diff_vmin, diff_vmax = -diff_abs_max, diff_abs_max
        color_limit_note = f"{color_percentiles[0]:g}th-{color_percentiles[1]:g}th percentiles"
    else:
        vmin_orig = min(vmin_1, vmin_2)
        vmax_orig = max(vmin_1, vmax_2)
        diff_abs_max = float(np.nanmax(np.abs(diff)))
        diff_vmin, diff_vmax = -diff_abs_max, diff_abs_max
        color_limit_note = "data min/max"
    diff_min = float(np.nanmin(diff))
    diff_max = float(np.nanmax(diff))
    
    # Calculate statistics for summary
    stats = {
        'variable': var,
        'label1': label1,
        'label2': label2,
        'data1_min': vmin_1,
        'data1_max': vmax_1,
        'data1_sum': float(np.nansum(data1)),
        'data2_min': vmin_2,
        'data2_max': vmax_2,
        'data2_sum': float(np.nansum(data2)),
        'diff_min': diff_min,
        'diff_max': diff_max,
        'diff_sum': float(np.nansum(diff)),
        'diff_abs_max': diff_abs_max,
        'color_vmin': vmin_orig,
        'color_vmax': vmax_orig,
        'diff_color_vmin': diff_vmin,
        'diff_color_vmax': diff_vmax,
        'color_percentiles': None if color_percentiles is None else f"{color_percentiles[0]}-{color_percentiles[1]}",
        'color_limit_note': color_limit_note,
    }
    
    # Helper function to add consistent map features
    def add_map_features(ax, title):
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.6)
        ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.5)
        ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.3)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_global()
        gl = ax.gridlines(draw_labels=True, alpha=0.5, linestyle='--', linewidth=0.5)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 10}
        gl.ylabel_style = {'size': 10}
    
    # Helper function to add consistent colorbar
    def add_colorbar(im, ax, label, shrink=0.7, pad=0.05):
        cbar = plt.colorbar(im, ax=ax, shrink=shrink, pad=pad)
        cbar.set_label(label, fontsize=12, fontweight='bold')
        cbar.ax.tick_params(labelsize=10)
        return cbar
    
    # Plot 1: First dataset
    ax1 = fig.add_subplot(gs[0, 0], projection=proj)
    im1 = ax1.pcolormesh(lon, lat, data1, transform=proj, vmin=vmin_orig, vmax=vmax_orig, cmap='viridis')
    add_map_features(ax1, f'{var} - {label1}')
    cbar1 = add_colorbar(im1, ax1, f'{unit1}')
    
    # Plot 2: Second dataset
    ax2 = fig.add_subplot(gs[1, 0], projection=proj)
    im2 = ax2.pcolormesh(lon, lat, data2, transform=proj, vmin=vmin_orig, vmax=vmax_orig, cmap='viridis')
    add_map_features(ax2, f'{var} - {label2}')
    cbar2 = add_colorbar(im2, ax2, f'{unit2}')
    
    # Plot 3: Absolute difference (removed max/min from title)
    ax3 = fig.add_subplot(gs[2, 0], projection=proj)
    norm = TwoSlopeNorm(vmin=diff_vmin, vcenter=0, vmax=diff_vmax)
    im3 = ax3.pcolormesh(lon, lat, diff, transform=proj, norm=norm, cmap='RdBu_r')
    add_map_features(ax3, f'{var} - Difference ({label1} - {label2})')
    cbar3 = add_colorbar(im3, ax3, f'Δ{var}')
    
    title_suffix = f" ({color_limit_note})" if color_limit_note else ""
    plt.suptitle(f'Variable {var} Comparison Analysis{title_suffix}', fontsize=18, fontweight='bold', y=0.96)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Save the plot
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Comparison plot saved: {save_path}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='Compare variables between NetCDF files.')
    parser.add_argument('--latest', type=str, default=None, help='Path to the latest result NetCDF file (file 1).')
    parser.add_argument('--model', type=str, required=True, help='Path to the model reference NetCDF file or directory containing one.')
    default_year = datetime.now().strftime("%Y")
    parser.add_argument('--search_pattern', type=str, default=f'*{default_year}*.nc', help='Glob pattern to find latest NetCDF (default: *YYYY*.nc for current year).')
    parser.add_argument('--exclude_lons', type=float, nargs='*', default=[0.0, 358.75], help='Longitude values to exclude from all panels. Pass no values to disable exclusion.')
    parser.add_argument('--color_percentiles', type=float, nargs=2, metavar=('LOW', 'HIGH'), default=None, help='Clip color limits to these percentiles (e.g. 2 98). When set, 0-degree longitude is kept and outliers are handled by color scaling instead of masking.')
    parser.add_argument('--variables', nargs='+', default=None, help='Subset of variables to plot (default: all).')
    parser.add_argument('--label1', type=str, default='Latest', help='Panel label for --latest (default: Latest).')
    parser.add_argument('--label2', type=str, default='Model', help='Panel label for --model (default: Model).')
    parser.add_argument('--case', type=str, default=None, help='Optional case label to include in the output directory name.')
    parser.add_argument('--output_dir', type=str, default='./mapplots', help='Output directory for plots (default: ./mapplots).')
    parser.add_argument('--timestamp', action='store_true', help='Include a timestamp in the output directory name.')
    args = parser.parse_args()

    color_percentiles = None
    if args.color_percentiles is not None:
        color_percentiles = (float(args.color_percentiles[0]), float(args.color_percentiles[1]))
        # Percentile mode keeps all longitudes unless user explicitly passes --exclude_lons.
        if '--exclude_lons' not in sys.argv:
            args.exclude_lons = []

    # Find latest file if not provided (default search in current dir ./)
    if args.latest is None:
        args.latest = get_latest_file(args.search_pattern)
        print(f"Auto-selected latest file: {args.latest}")
    
    model_file = args.model
    if os.path.isdir(model_file):
        model_file = get_latest_file(os.path.join(model_file, "*.nc"))
        print(f"Model path is directory, using: {model_file}")
    
    # Extract base names from file paths for folder names
    latest_basename = os.path.splitext(os.path.basename(args.latest))[0]
    model_basename = os.path.splitext(os.path.basename(model_file))[0]
    
    # Output folder using file names (optionally include case/timestamp)
    if args.output_dir:
        latest_model_dir = args.output_dir
    else:
        parts = [f'{latest_basename}_vs_{model_basename}']
        if args.case:
            parts.append(args.case)
        if args.timestamp:
            parts.append(datetime.now().strftime('%Y%m%d-%H%M%S'))
        latest_model_dir = "_".join(parts)
    
    os.makedirs(latest_model_dir, exist_ok=True)
    
    # Open datasets
    ds_latest = xr.open_dataset(args.latest)
    ds_model = xr.open_dataset(model_file)
    lon = ds_latest['lon']
    lat = ds_latest['lat']
    
    plot_variables = [v.upper() for v in args.variables] if args.variables else variables
    
    print(f"\nComparing variables: {plot_variables}\n")
    
    # Store all statistics for summary file
    all_stats = []
    
    for var in plot_variables:
        if var not in ds_latest.data_vars or var not in ds_model.data_vars:
            print(f"Variable {var} not found in latest/model, skipping...")
        else:
            v_latest = ds_latest[var]
            v_model = ds_model[var]
            data_latest = v_latest.isel(time=0).values if 'time' in v_latest.dims else v_latest.values
            data_model = v_model.isel(time=0).values if 'time' in v_model.dims else v_model.values
            data_latest_scaled, unit_latest = get_display_unit_and_scaled(data_latest, v_latest, ds_latest)
            data_model_scaled, unit_model = get_display_unit_and_scaled(data_model, v_model, ds_model)
            save_path = os.path.join(latest_model_dir, f'{var}_comparison.png')
            stats = plot_variable_comparison(
                var,
                data_latest_scaled,
                data_model_scaled,
                lon,
                lat,
                args.label1,
                args.label2,
                save_path,
                unit_latest,
                unit_model,
                exclude_lons=args.exclude_lons,
                color_percentiles=color_percentiles,
            )
            stats['comparison_type'] = f'{args.label1} vs {args.label2}'
            stats['unit1'] = unit_latest
            stats['unit2'] = unit_model
            all_stats.append(stats)
    
    # Save summary statistics to CSV file
    import pandas as pd
    summary_file = os.path.join(latest_model_dir, f'comparison_summary_{latest_basename}.csv')
    if os.path.exists(summary_file) and args.variables:
        existing = pd.read_csv(summary_file)
        existing = existing[~existing["variable"].isin([s["variable"] for s in all_stats])]
        df = pd.concat([existing, pd.DataFrame(all_stats)], ignore_index=True)
    else:
        df = pd.DataFrame(all_stats)
    df.to_csv(summary_file, index=False)
    print(f"\nSummary statistics saved to: {summary_file}")
    
    ds_latest.close()
    ds_model.close()
    print("\nAll variable comparison plots are complete!")
    print(f"Images saved in: {latest_model_dir}/")
    print(f"Summary file: {summary_file}")

if __name__ == '__main__':
    main()
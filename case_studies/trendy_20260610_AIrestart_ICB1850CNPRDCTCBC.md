# TRENDY case study: 20260610 AI restart

This note records the simulation setup, the locations of the two runs, and the h0 comparison used for the paper. The figures and history files stay on PathFinder. The global-sum numbers in this file, and in `trendy_20260610_AIrestart_ICB1850CNPRDCTCBC_global_sums.csv` beside it, are the values to cite.

The AI-restart case ran on PathFinder. The model-reference segment ran on CADES baseline, and the history files used here are the PathFinder copy of that segment. The comparison itself was built on PathFinder on 10 October 2026.

## Simulations

Both runs use the same compset, grid, CO2, and CRUJRA meteorology. They differ in the initial condition and in the machine that wrote the history.

| Item | Value |
| --- | --- |
| Compset | `1850_SATM_ELM%CNPRDCTCBC_SICE_SOCN_MOSART_SGLC_SWAV_SIAC_SESP` |
| Land model | ELM with CN, carbon–nitrogen–phosphorus, nutrient competition by relative demand, the CTC soil cascade, and methane |
| Atmosphere | Stub atmosphere. Meteorology is CRUJRA TRENDY 2024 through `metdata_type = 'crujra'` and `metdata_bypass` |
| Resolution | Land `0.9x1.25`; mask `gx1v6` |
| Grid | `a%null_l%0.9x1.25_oi%null_r%r05_g%null_w%null_z%null_m%gx1v6` |
| Calendar | No-leap |
| CO2 | 284.7 ppm, `co2_type = 'constant'` |
| Accelerated spinup | Off (`ELM_ACCELERATED_SPINUP = off`, `spinup_state = 0`) |
| Supplementary N and P | `suplnitro = 'NONE'`, `suplphos = 'NONE'` |
| Surface data | `surfdata_0.9x1.25_hist_1700_17pfts_c240731.nc` |
| Use case | `1850_control` |
| Run length | 200 years (`STOP_OPTION = nyears`, `STOP_N = 200`), start date `0001-01-01` |
| Restarts | Every 20 years (`REST_OPTION = nyears`, `REST_N = 20`) |
| ELM history | One instantaneous field every 20 years (`hist_nhtfrq = -175200` hours, `hist_mfilt = 1`) |

### AI restart (PathFinder)

| Item | Value |
| --- | --- |
| Case | `20260610_TRENDY2024_AIrestart_ICB1850CNPRDCTCBC` |
| Machine | PathFinder (`MACH = pathfinder`, history `hostname = pathfinder`) |
| Compiler / MPI | `gnu` / `openmpi` |
| Tasks | 336 MPI tasks, 4 nodes, 84 tasks per node, 1 thread (`preview_run.log`) |
| User | `zdr` |
| Code | E3SM `source_id` / `git_version` `ebc39ea5a9` |
| Source tree | `/projects/hpcl-cli185/proj-shared/zdr/trendy_2024/E3SM_TRENDY` |
| Case directory | `/scratch/hpcl-cli185/zdr/e3sm_cases/20260610_TRENDY2024_AIrestart_ICB1850CNPRDCTCBC` |
| Run directory | `/scratch/hpcl-cli185/zdr/e3sm_run/20260610_TRENDY2024_AIrestart_ICB1850CNPRDCTCBC/run` |
| Executable | `/projects/hpcl-cli185/proj-shared/zdr/e3sm_run/20260610_TRENDY2024_AIrestart_ICB1850CNRDCTCBC_ad_spinup/bld/e3sm.exe` |
| Initial condition | `/projects/hpcl-cli185/proj-shared/wangd/AI4ELM/AI_data/trendy1_restart_files/run_20260512_083650_phase3_tworegions/updated_restart_phase3_tworegions_5P_bias_corrected_amazon_africa_v3_tropical.nc` |
| History written | `h0.0001` on 10 June 2026 14:55; `h0.0201` on 11 June 2026 02:58 |

The `finidat` line in the copied `lnd_in` is that phase-3 restart. The history attribute `Initial_conditions_dataset` is the same file name.

### Model reference (CADES baseline, files on PathFinder)

| Item | Value |
| --- | --- |
| Case | `20251201_TRENDY2024_default_ICB1850CNPRDCTCBC` |
| Machine that wrote the history | CADES baseline (`MACH = cades-baseline`, history `hostname = cades-baseline`) |
| Compiler / MPI | `gnu` / `openmpi` |
| User | `wangd` |
| Code version in the history files | `source_id` / `git_version` `unknown` |
| Source tree recorded in the case | `/gpfs/wolf2/cades/cli185/proj-shared/zdr/trendy_2024/E3SM_TRENDY` |
| Case directory on CADES | `/gpfs/wolf2/cades/cli185/proj-shared/wangd/AI_spinup/e3sm_cases/20251201_TRENDY2024_default_ICB1850CNPRDCTCBC` |
| Initial condition | `20251201_TRENDY2024_default_ICB1850CNPRDCTCBC.elm.r.0801-01-01-00000.nc` |
| History written | `h0.0021` on 3 January 2026 18:25; `h0.0201` on 3 January 2026 23:15 |

This segment is the 200-year run started from that case’s year-801 restart. The model clock in these files begins again at year 1, so `h0.0021` is 1 January of year 21 after the 801-year restart, and `h0.0201` is 1 January of year 201. The job directory name is `347073.260103-175022_new_801year_model_restart`.

## Where the two simulations are

History files are named `<case>.elm.h0.YYYY-01-01-00000.nc`. Both runs have `h0.0001` through `h0.0201`, every 20 years (11 files).

| Role | What was compared | Directory |
| --- | --- | --- |
| Model reference | Years 1–201 after the 801-year model restart | `/projects/hpcl-cli185/proj-shared/wangd/AI4ELM/AI_spinup/e3sm_run/20251201_TRENDY2024_default_ICB1850CNPRDCTCBC/run/347073.260103-175022_new_801year_model_restart` |
| AI restart | Years 1–201 after the phase-3 restart | `/projects/hpcl-cli185/proj-shared/wangd/AI4ELM/AI_data/JAMES2026/restart_comparison_2026/restart_comparison/trendy_case_james_paper_case` |

`restart_comparison_2026/restart_comparison/commands.txt` names `NewModel801YearRestart_260103` for the older global-sum tables and `New801YearModelRestartSimulationReference` for the older maps. The map directory is not on disk. The history files above are the ones those maps used. GPP recomputed from those files agrees with `restart_comparison_2026/NewModel801YearRestart_260103/new_twenty_year_sum_gpp_data.txt` to the precision of that older file, which stored rounded integers (relative difference about 10^−7).

## Comparison method

Tool checkout on PathFinder: `/projects/hpcl-cli185/proj-shared/wangd/AI4ELM/AI_data/JAMES2026/elm_h0_compare` (`h0_compare.py`, commit `0d47ddd`, `--forcing trendy`).

`--forcing trendy` drops longitudes 0 and 358.75. ERA5 keeps every longitude.

The global sum uses land only (`landmask == 1`):

`sum(field * area * landfrac)`.

`area` is in km^2. A flux whose units end in `gC/m^2/s` is then multiplied by 31,536,000 s/year. With area in km^2, that global sum is metric tons of carbon per year. Divide by 10^9 to report Pg C/yr. A carbon pool in `gC/m^2` uses the same area weighting and is metric tons of carbon; divide by 10^9 for Pg C. The text files label fluxes `tonC/km^2/year` and pools `tonC/km^2`. Those labels are the tool headers. The numbers in the results section are the global integrals.

`TLAI` is dimensionless. Its table value is the same area-weighted sum, not a global-mean leaf area index.

Both series use the filename year. `--reference-zero-year 0` and `--case-zero-year 0` put year 0 at x = 0, so the markers sit on years 21, 41, …, 201. Year 1 stays in the tables and is left off the line plots. Maps compare filename years 21, 101, and 201 (`h0.0021`, `h0.0101`, `h0.0201`). Each map is the AI field, the model field, and the difference.

The ten variables present in both runs are CWDC, DEADSTEMC, GPP, HR, NEE, SOIL3C, SOIL4C, TLAI, TOTCOLC, and TOTSOMC. The AI history files omit SOIL1C, SOIL2C, LABILEP, SECONDP, OCCLP, and PRIMP. Those six variables have model tables only, and they are not on the line plots or the maps.

## Where the comparison products are

All products are under

`/projects/hpcl-cli185/proj-shared/wangd/AI4ELM/AI_data/JAMES2026/trendy_james_paper_h0_comparison`.

| Product | Path under that directory |
| --- | --- |
| Model global-sum tables (16 variables, years 0001–0201) | `model_reference/new_twenty_year_sum_<var>_data.txt` |
| AI-restart global-sum tables (10 variables) | `trendy_ai_restart/new_twenty_year_sum_<var>_data.txt` |
| Time-series figures | `trendy_ai_restart/timeseries/<VAR>_comparison.png` |
| Maps at year 21 | `trendy_ai_restart/maps/h0021/` |
| Maps at year 101 | `trendy_ai_restart/maps/h0101/` |
| Maps at year 201 | `trendy_ai_restart/maps/h0201/` |

Each map folder also has `comparison_summary_<ai h0 file>.csv`. The paired sums for every snapshot are stored in this repository as `trendy_20260610_AIrestart_ICB1850CNPRDCTCBC_global_sums.csv`, so the numbers are available on a machine that does not mount the PathFinder run directory.

The figures, global-sum tables, and map CSVs are packed for transfer, without any history NetCDF files, in

`/projects/hpcl-cli185/proj-shared/wangd/AI4ELM/AI_data/JAMES2026/trendy_james_paper_h0_comparison.zip`

Packed on 10 October 2026. The archive is 46 MB (`48066126` bytes). Its SHA-256 is `d1ae8bae45d5503b6d6733714038da2cf20a5a1b96569dea4680137f5426e5f2`. It contains 40 PNG files (10 time-series plots and 30 maps), 3 map summary CSVs, and 26 global-sum tables (16 model variables and 10 AI-restart variables). No `.nc` files are in the archive. The original history files stay in the two run directories above.

## Results

Percent difference is `(AI - model) / model`. Year 1 is the initial snapshot. Year 21 is the first point on the line plots, 20 years after each initial condition. Year 201 is the end of both runs.

At the initial snapshot, GPP is 42.787 Pg C/yr in the AI restart and 36.236 Pg C/yr in the model (+18.08%). By year 21, GPP is 137.801 against 138.993 Pg C/yr (−0.86%). At year 201 it is 138.006 against 138.888 Pg C/yr (−0.63%). Heterotrophic respiration at year 201 is 45.366 against 46.421 Pg C/yr (−2.27%).

NEE at year 201 is a small sink in the AI restart (−0.093 Pg C/yr) and near zero in the model (0.00046 Pg C/yr). The percent difference for NEE is omitted because the model flux is near zero.

Carbon pools stay lower in the AI restart through year 201. Total column carbon is 3450.03 Pg C against 3637.91 Pg C (−5.16%), close to the year-21 difference (−5.16%). Total soil organic matter carbon is 2497.89 against 2663.22 Pg C (−6.21%). The slow soil pool, SOIL4C, is 2256.85 against 2413.67 Pg C (−6.50%). Coarse woody debris is 136.770 against 143.573 Pg C (−4.74%). Dead-stem carbon starts nearly equal (498.988 against 496.513 Pg C at year 1, +0.50%) and is 483.275 against 496.733 Pg C at year 201 (−2.71%).

| Variable | Unit of the columns | AI year 21 | Model year 21 | % | AI year 201 | Model year 201 | % |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPP | Pg C/yr | 137.801 | 138.993 | −0.86 | 138.006 | 138.888 | −0.63 |
| HR | Pg C/yr | 44.851 | 46.459 | −3.46 | 45.366 | 46.421 | −2.27 |
| NEE | Pg C/yr | −0.486 | 0.004 | — | −0.093 | 0.00046 | — |
| TOTCOLC | Pg C | 3450.28 | 3638.13 | −5.16 | 3450.03 | 3637.91 | −5.16 |
| TOTSOMC | Pg C | 2481.30 | 2663.93 | −6.86 | 2497.89 | 2663.22 | −6.21 |
| SOIL3C | Pg C | 216.682 | 227.701 | −4.84 | 220.342 | 228.045 | −3.38 |
| SOIL4C | Pg C | 2244.21 | 2414.81 | −7.06 | 2256.85 | 2413.67 | −6.50 |
| CWDC | Pg C | 136.574 | 143.364 | −4.74 | 136.770 | 143.573 | −4.74 |
| DEADSTEMC | Pg C | 496.350 | 496.489 | −0.03 | 483.275 | 496.733 | −2.71 |
| TLAI | area-weighted sum | 2.110e8 | 2.175e8 | −2.99 | 2.128e8 | 2.173e8 | −2.05 |

Exact tool sums, before the Pg conversion, are in the CSV. Carbon columns in the table are those sums divided by 10^9.

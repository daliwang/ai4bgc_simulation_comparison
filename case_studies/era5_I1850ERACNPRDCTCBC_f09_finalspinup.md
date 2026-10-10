# ERA5 case study: I1850ERACNPRDCTCBC f09 final spinup

This note records the simulation setup, the locations of the two runs, and the h0 comparison used for the paper. The figures and history files stay on Orion. The global-sum numbers in this file, and in `era5_I1850ERACNPRDCTCBC_f09_finalspinup_global_sums.csv` beside it, are the values to cite.

## Simulations

Both history files were written by the same E3SM case on Frontier.

| Item | Value |
| --- | --- |
| Case | `I1850ERACNPRDCTCBC_f09_finalspinup` |
| Compset | `I1850ERACNPRDCTCBC` |
| Compset long name | `1850_DATM%ERAf09_ELM%CNPRDCTCBC_SICE_SOCN_MOSART_SGLC_SWAV_SIAC_SESP` |
| Land model | ELM with CN, carbon–nitrogen–phosphorus, nutrient competition by relative demand, and the CTC soil cascade with black-carbon deposition |
| Atmosphere | Data atmosphere, ERA5, 6-hourly, remapped to f09 |
| Resolution | Atmosphere and land `0.9x1.25`; river `r05`; mask `gx1v6` |
| Grid alias | `f09_f09` (`a%0.9x1.25_l%0.9x1.25_oi%null_r%r05_g%null_w%null_z%null_m%gx1v6`) |
| Calendar | No-leap |
| CO2 | 284.7 ppm |
| Prescribed aerosol | `clim_1850` |
| Accelerated spinup | Off (`ELM_ACCELERATED_SPINUP = off`, `spinup_state = 0`) |
| Supplementary phosphorus | `suplphos = 'NONE'` |
| Surface data | `/lustre/orion/cli115/world-shared/e3sm/inputdata/lnd/clm2/surfdata_map/surfdata_0.9x1.25_simyr1850_c180306.nc` |
| Machine | Frontier (`MACH = frontier`, `hostname = frontier`) |
| Compiler / MPI | `craygnu` / `mpich` |
| Tasks | 1280 MPI tasks per component, 1 thread |
| Code | E3SM `source_id` / `git_version` `2a1960cd8a` in both sets of history files |
| Source tree | `/lustre/orion/cli115/world-shared/wangd/kmELM/E3SM` |
| Case directory | `/lustre/orion/cli115/world-shared/wangd/kmELM/E3SM/e3sm_cases/I1850ERACNPRDCTCBC_f09_finalspinup` |
| Build | `/lustre/orion/cli115/world-shared/wangd/kmELM/E3SM/e3sm_runs/I1850ERACNPRDCTCBC_f09_finalspinup/bld` |

ELM history is one instantaneous field every 20 years (`hist_nhtfrq = -175200` hours, `hist_mfilt = 1`). Restarts are written every 10 years (`REST_OPTION = nyears`, `REST_N = 10`). The case run length per submission is 10 years (`STOP_OPTION = nyears`, `STOP_N = 10`). The run start date in `env_run.xml` is `0401-01-01`.

The model-reference initial condition, kept as a comment in `user_nl_elm`, is the accelerated-spinup restart

`/lustre/orion/cli115/world-shared/wangd/kmELM/E3SM/e3sm_runs/I1850ERACNPRDCTCBC_f09_adspinup/run/I1850ERACNPRDCTCBC_f09_adspinup.elm.r.0401-01-01-00000.nc`.

The AI-restart initial condition, the active `finidat` in `user_nl_elm` and in the run-directory `lnd_in`, is

`/lustre/orion/cli115/world-shared/wangd/LandSim/TrainingData/ERA5_1_data/simData/updated_restart_phase3_tworegions_5P_bias_corrected_tropical.nc`.

## Where the two simulations are

History files are named `I1850ERACNPRDCTCBC_f09_finalspinup.elm.h0.YYYY-01-01-00000.nc`. The year in the name is the model date of that snapshot. `h0.0401` is 1 January of year 401. `h0.1001` is 1 January of year 1001.

| Role | What was compared | Directory | History files used | File written |
| --- | --- | --- | --- | --- |
| Model reference | Last 200 years of the native-model final spinup (simulation years 1000–1200) | `/lustre/orion/cli115/world-shared/wangd/kmELM/E3SM/e3sm_runs/I1850ERACNPRDCTCBC_f09_finalspinup/run/model_reference_run` | `h0.1001` through `h0.1201`, every 20 years (11 files) | 5 September 2026 (`h0.1201` history attribute) |
| AI restart | Years 400–600 after the phase-3 restart | `/lustre/orion/cli115/world-shared/wangd/kmELM/E3SM/e3sm_runs/I1850ERACNPRDCTCBC_f09_finalspinup/run` | `h0.0401` through `h0.0601`, every 20 years (11 files) | 9 October 2026 (`h0.0601` history attribute) |

The model-reference directory also holds the earlier native-model history, from `h0.0401` through `h0.1201`. Only `h0.1001`–`h0.1201` entered this comparison. The AI-restart directory holds `h0.0401`–`h0.0601`.

## Comparison method

Tool checkout on Orion: `/lustre/orion/cli115/world-shared/wangd/ai4bgc_simulation_comparison` (`h0_compare.py`, commit `939cf36`, `--forcing era5`). Other machines use their own clone of `github.com:daliwang/ai4bgc_simulation_comparison.git`.

ERA5 keeps every longitude. Longitudes 0 and 358.75 are dropped only for `--forcing trendy`.

The global sum uses land only (`landmask == 1`):

`sum(field * area * landfrac)`.

`area` is in km^2. A flux whose units end in `gC/m^2/s` is then multiplied by 31,536,000 s/year. With area in km^2, that global sum is metric tons of carbon per year. Divide by 10^9 to report Pg C/yr. A carbon pool in `gC/m^2` uses the same area weighting and is metric tons of carbon; divide by 10^9 for Pg C. A phosphorus pool in `gP/m^2` is metric tons of phosphorus; divide by 10^9 for Pg P. The text files label fluxes `tonC/km^2/year` and pools `tonC/km^2`. Those labels are the tool headers. The numbers above are the global integrals.

`TLAI` is dimensionless. Its table value is the same area-weighted sum, not a global-mean leaf area index.

Time-series plots draw both runs on one axes. Model year 1000 is x = 0 (`--reference-zero-year 1000`). AI-restart year 400 is x = 0 (`--case-zero-year 400`). The first snapshots are year 1001 and year 401, so the first markers sit at x = 1. Maps compare the window endpoints: AI year 401 against model year 1001, and AI year 601 against model year 1201. Each map is the AI field, the model field, and the difference. Mapped variables are CWDC, DEADSTEMC, GPP, HR, NEE, SOIL1C, SOIL2C, SOIL3C, SOIL4C, TLAI, TOTCOLC, and TOTSOMC. Phosphorus pools are in the time series and the tables, and are not mapped.

## Where the comparison products are

All products are under

`/lustre/orion/cli115/world-shared/wangd/kmELM/E3SM/e3sm_runs/I1850ERACNPRDCTCBC_f09_finalspinup/h0_comparison_ai_y0401-0601_vs_model_y1001-1201`.

| Product | Path under that directory |
| --- | --- |
| Model global-sum tables | `model_reference/new_twenty_year_sum_<var>_data.txt` |
| AI-restart global-sum tables | `ai_restart_y0401-0601/new_twenty_year_sum_<var>_data.txt` |
| Time-series figures | `ai_restart_y0401-0601/timeseries/<VAR>_comparison.png` |
| Maps at the start of each window | `ai_restart_y0401-0601/maps/h0401_vs_h1001/` |
| Maps at the end of each window | `ai_restart_y0401-0601/maps/h0601_vs_h1201/` |
| Paired sums for every snapshot | `aligned_global_sum_differences.csv` |

The same paired table is stored in this repository as `era5_I1850ERACNPRDCTCBC_f09_finalspinup_global_sums.csv`, so the numbers are available on a machine that does not mount the Orion run directory. The PNG files are only on Orion (about 1.6 MB of time-series plots and about 51 MB of maps).

## Results

Relative year 0 is AI year 401 against model year 1001. Relative year 200 is AI year 601 against model year 1201. Percent difference is `(AI - model) / model`.

Carbon fluxes at the end of the window are close. GPP is 128.912 Pg C/yr in the AI restart and 129.748 Pg C/yr in the model (−0.64%). Heterotrophic respiration is 43.206 and 43.834 Pg C/yr (−1.43%). The first AI snapshot is not close: GPP is 43.275 Pg C/yr against the model’s 129.744 Pg C/yr (−66.65%), and NEE is a 52.226 Pg C/yr source against a model sink of 0.038 Pg C/yr. By the next snapshot, AI year 421 against model year 1021, GPP is 127.534 against 129.752 Pg C/yr (−1.71%).

At year 601, NEE is still a stronger sink in the AI restart (−0.193 Pg C/yr) than in the model at year 1201 (−0.027 Pg C/yr). The percent difference for NEE is not a useful measure, because the model flux is near zero.

Carbon pools at the end of the window are within about 2%, except coarse woody debris at −2.99%. Total column carbon is 2982.53 Pg C against 3019.12 Pg C (−1.21%). Total soil organic matter carbon is 2071.78 against 2108.63 Pg C (−1.75%). Dead-stem carbon is slightly higher in the AI restart (467.59 against 464.45 Pg C, +0.67%).

Labile, secondary, and occluded phosphorus stay about 6–7% below the model. Primary mineral phosphorus moves farther away, from −28.50% at the start of the window to −51.04% at the end (1.216 Pg P against 2.483 Pg P).

| Variable | Unit of the columns | AI year 401 | Model year 1001 | % | AI year 601 | Model year 1201 | % |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPP | Pg C/yr | 43.275 | 129.744 | −66.65 | 128.912 | 129.748 | −0.64 |
| HR | Pg C/yr | 37.048 | 43.766 | −15.35 | 43.206 | 43.834 | −1.43 |
| NEE | Pg C/yr | 52.226 | −0.038 | — | −0.193 | −0.027 | — |
| TOTCOLC | Pg C | 2987.52 | 3012.84 | −0.84 | 2982.53 | 3019.12 | −1.21 |
| TOTSOMC | Pg C | 2060.79 | 2105.58 | −2.13 | 2071.78 | 2108.63 | −1.75 |
| SOIL1C | Pg C | 1.720 | 1.633 | 5.30 | 1.623 | 1.645 | −1.33 |
| SOIL2C | Pg C | 15.898 | 16.599 | −4.22 | 16.577 | 16.769 | −1.15 |
| SOIL3C | Pg C | 179.099 | 181.858 | −1.52 | 181.762 | 182.969 | −0.66 |
| SOIL4C | Pg C | 1864.07 | 1905.49 | −2.17 | 1871.82 | 1907.25 | −1.86 |
| CWDC | Pg C | 127.551 | 131.304 | −2.86 | 128.434 | 132.388 | −2.99 |
| DEADSTEMC | Pg C | 484.029 | 462.686 | 4.61 | 467.586 | 464.453 | 0.67 |
| LABILEP | Pg P | 6.544 | 6.945 | −5.78 | 6.496 | 6.915 | −6.05 |
| SECONDP | Pg P | 145.885 | 154.941 | −5.84 | 146.286 | 154.887 | −5.55 |
| OCCLP | Pg P | 95.713 | 103.077 | −7.14 | 96.051 | 103.454 | −7.16 |
| PRIMP | Pg P | 2.283 | 3.194 | −28.50 | 1.216 | 2.483 | −51.04 |
| TLAI | area-weighted sum | 1.897e8 | 2.175e8 | −12.80 | 2.153e8 | 2.177e8 | −1.13 |

Exact tool sums, before the Pg conversion, are in the CSV. Carbon and phosphorus columns in the table are those sums divided by 10^9.

# ELM h0 case comparison

Compare one AI-restart ELM history run with a model-restart reference. Three products are written the same way every time: global-sum tables, one line plot per variable, and a three-panel map at one model year.

This folder is the whole workflow. It does not read scripts or paths from a results tree.

```bash
pip install -r requirements.txt
```

The year in the filename is the model year. `h0.0021` is year 21 (the 20-year snapshot), `h0.0101` is year 101, and `h0.0201` is year 201.

## 1. Reference time series

Reads `*.elm.h0.*.nc` in the run directory and writes `new_twenty_year_sum_<var>_data.txt`.

```bash
python h0_compare.py aggregate \
  --run-dir /path/to/model/run \
  --out-dir /path/to/output/model_reference \
  --start-year 1 \
  --end-year 201 \
  --variables NEE GPP HR TLAI TOTCOLC SOIL1C SOIL2C SOIL3C SOIL4C TOTSOMC CWDC DEADSTEMC LABILEP SECONDP OCCLP PRIMP
```

`--start-year` and `--end-year` are inclusive filename years. Year 1 is kept in the table and left off the line plot later. If `--variables` is omitted, the command uses that same list.

## 2. AI case time series and line plots

```bash
python h0_compare.py timeseries \
  --reference-tables /path/to/output/model_reference \
  --reference-name model_reference \
  --case-dir /path/to/ai/run \
  --case-name phase3_africa \
  --out-dir /path/to/output \
  --start-year 1 \
  --end-year 201 \
  --variables NEE GPP HR TLAI TOTCOLC SOIL1C SOIL2C SOIL3C SOIL4C TOTSOMC CWDC DEADSTEMC LABILEP SECONDP OCCLP PRIMP
```

Tables go in `/path/to/output/phase3_africa/`. Plots go in `/path/to/output/phase3_africa/timeseries/<VAR>_comparison.png`.

Both runs are drawn on one axes. Each series is shifted so its zero year is at x = 0. `--reference-zero-year` and `--case-zero-year` set those origins. If either is omitted, that series uses the first year left in its table. For an AI restart that begins at year 400 compared with a model window that begins at year 1000:

```bash
python h0_compare.py timeseries \
  --reference-tables /path/to/output/model_reference \
  --reference-name model_reference \
  --reference-zero-year 1000 \
  --case-dir /path/to/ai/run \
  --case-name phase3_africa \
  --case-zero-year 400 \
  --out-dir /path/to/output \
  --start-year 401 \
  --end-year 601 \
  --forcing era5
```

## 3. Map at one year

```bash
python h0_compare.py maps \
  --year 201 \
  --ai-dir /path/to/ai/run \
  --model-dir /path/to/model/run \
  --ai-label phase3_africa \
  --model-label model_reference \
  --out-dir /path/to/output/phase3_africa/maps/h0201 \
  --variables CWDC DEADSTEMC GPP HR NEE SOIL1C SOIL2C SOIL3C SOIL4C TLAI TOTCOLC TOTSOMC
```

Each variable is a PNG with the AI run, the model run, and the difference. A CSV of min, max, and sum is written in the same folder. NEE color bars stay fixed at −5 to 5. If `--variables` is omitted, phosphorus pools are not mapped.

## Longitude columns

`--forcing era5` is the default. ERA5 and any other non-Trendy run keep every longitude in the global sum and in the maps. `--forcing trendy` drops longitudes 0 and 358.75, because those model columns are not usable. `--exclude-lons` overrides `--forcing` on any command. The same `--forcing` value has to be used for `aggregate`, `timeseries`, and `maps` so the tables and the maps describe the same grid.

## What stays fixed

- Land only (`landmask == 1`).
- The global sum is `sum(data * area * landfrac)`. A flux in `gC/m^2/s` is multiplied by the seconds in a year and labeled `tonC/km^2/year`.
- Map panels use the first time record in that h0 file. The time-series sum averages the time axis first when the file has more than one time.

Write `--out-dir` outside this folder so plot files stay out of the git repo.

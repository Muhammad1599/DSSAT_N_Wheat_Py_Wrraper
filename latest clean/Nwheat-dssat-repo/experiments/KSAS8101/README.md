# KSAS8101 NWheat Experiment

## Overview
This folder contains a complete, self-contained NWheat (CROPSIM-Wheat) experiment setup for the Kansas State University KSAS8101 study.

## Experiment Details
- **Location**: Kansas State University, Ashland, KS
- **Year**: 1981
- **Cultivar**: Newton (IB0488) - Winter wheat
- **Study Type**: Nitrogen response with irrigation treatments
- **Treatments**: 6 treatments (3 nitrogen levels × 2 irrigation levels)

## Files Included

### Experiment Files
- `KSAS8101.WHX` - Experiment definition file (treatments, management, cultivar)
- `KSAS8101.WHA` - Observed data for model validation (yield, phenology, etc.)
- `KSAS8101.WHT` - Time series observations during growing season
- `KSAS8101.WTH` - Daily weather data (temperature, rainfall, solar radiation)

### NWheat Model Files
- `Genotype/WHCRP048.CUL` - Cultivar parameters for NWheat model
- `Genotype/WHCRP048.ECO` - Ecotype parameters for NWheat model  
- `Genotype/WHCRP048.SPE` - Species parameters for NWheat model

### DSSAT System Files
- `DSCSM048.EXE` - DSSAT model executable (10.1 MB)
- `DATA.CDE` - DSSAT data codes
- `DETAIL.CDE` - DSSAT detail codes
- `DSCSM048.CTR` - DSSAT control file

### Execution Scripts
- `run_nwheat.py` - Python script to run simulation with detailed output
- `run_nwheat.bat` - Simple batch file to run simulation

## How to Run

### Method 1: Using Python Script (Recommended)
```bash
python run_nwheat.py
```

### Method 2: Using Batch File
```bash
run_nwheat.bat
```

### Method 3: Direct DSSAT Execution
```bash
DSCSM048.EXE KSAS8101.WHX
```

## Expected Outputs
After running the simulation, the following output files will be generated:

- `*.SUM` - Summary results file with key outputs (yield, biomass, dates)
- `*.PLT` - Plant growth details throughout the season
- `*.OUT` - Overview results file  
- `*.ETH` - Evapotranspiration details

## Validation Data Available
The `KSAS8101.WHA` file contains observed field data that can be compared with model outputs for accuracy assessment, including:

- Harvest weight (HARWT)
- Top weight/biomass (TOPWT)  
- Anthesis date (ADAT)
- Maturity date (MDAT)
- Grain yield (HWAM)
- Harvest index (HI)

## Model Information
- **Model**: NWheat (CROPSIM-Wheat) - WHCRP048
- **DSSAT Version**: 4.8
- **Crop**: Winter Wheat
- **Simulation Type**: Seasonal run with multiple treatments

## Troubleshooting
If the simulation fails:
1. Ensure all files are present in the directory
2. Check that DSCSM048.EXE has execute permissions
3. Verify the Genotype folder contains all three .CUL, .ECO, .SPE files
4. Make sure weather file KSAS8101.WTH is in the same directory

## File Sizes Reference
- DSCSM048.EXE: ~10.1 MB
- DATA.CDE: ~123 KB
- DETAIL.CDE: ~52 KB
- KSAS8101.WHX: ~4 KB
- KSAS8101.WTH: ~3 KB
- WHCRP048.SPE: ~16 KB
- WHCRP048.ECO: ~6 KB
- WHCRP048.CUL: ~6 KB

Total folder size: ~10.3 MB

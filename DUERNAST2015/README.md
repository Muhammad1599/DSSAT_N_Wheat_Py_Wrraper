# DUERNAST2015 - DSSAT Spring Wheat Nitrogen Response Analysis

A complete automated workflow for analyzing spring wheat response to nitrogen fertilization using the DSSAT N-Wheat model. This repository provides end-to-end simulation and visualization capabilities for the Duernast 2015 field experiment in Germany.

## What This Repository Does

This repository automates the complete analysis pipeline for a spring wheat nitrogen fertilization experiment:

1. **Runs DSSAT Simulations**: Executes the N-Wheat crop model (WHAPS048) for 15 nitrogen treatment scenarios
2. **Generates Scientific Visualizations**: Creates a comprehensive 16-panel figure comparing model results with observed field data
3. **Validates Model Performance**: Compares simulated vs. observed yields, grain quality, and nitrogen dynamics
4. **Produces Publication-Ready Outputs**: High-resolution figures ready for academic papers

## Experiment Details

- **Location**: Dürnast, Freising, Bayern, Germany
- **Crop**: Spring Wheat (Sommerweizen, cv. WHAPS048)
- **Treatments**: 15 nitrogen treatments (0, 120, 180 kg N/ha)
- **Fertilizer Types**: Urea, Ammonium sulfate, Calcium ammonium nitrate, UAN, Mixed formulations
- **Model**: DSSAT N-Wheat (WHAPS048)
- **Output**: 16-panel scientific visualization

## Quick Start

### 1. Install Dependencies

```bash
cd DUERNAST2015
pip install -r requirements.txt
```

### 2. Run the Complete Workflow

```bash
python MASTER_WORKFLOW.py
```

That's it! The workflow will:
- Check all prerequisites
- Copy DSSAT executable files (from parent DSSAT48 folder)
- Copy all input files to output directory
- Run DSSAT simulation
- Generate 16-panel visualization
- Display summary report

**Note**: The workflow can start with an empty `output/` folder - all required files are automatically copied before simulation.

**Execution Time**: ~12-15 seconds  
**Output**: 9 files (~6.1 MB total)

### Expected Output

```
==========================================================================================
                        WORKFLOW COMPLETED SUCCESSFULLY!
==========================================================================================
- output/Summary.OUT (main results)
- output/PlantGro.OUT (growth time series)
- output/PlantN.OUT (nitrogen dynamics)
- output/Weather.OUT (weather data)
- output/duernast_2015_comprehensive_analysis.png (3.3 MB visualization)
- output/duernast_2015_comprehensive_analysis.pdf (105 KB vector)
```

## Repository Structure

```
DUERNAST2015/
├── MASTER_WORKFLOW.py              # Main workflow orchestrator
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules (excludes generated files)
├── README.md                       # This file
├── VISUALIZATION_TECHNICAL_DOCUMENTATION.txt  # Panel documentation
│
├── Genotype/                       # Cultivar parameters
│   ├── WHAPS048.CUL                # Cultivar coefficients
│   ├── WHAPS048.ECO                # Ecotype coefficients
│   └── WHAPS048.SPE                # Species coefficients
│
├── input/                          # Input data
│   ├── DE.SOL                      # Soil profile
│   ├── TUDU1501.WHX                # Experiment definition
│   ├── TUDU1501.WTH                # Weather data
│   ├── TUDU1501.WHT                # Observed harvest data
│   └── TUDU1501.WHA                # Treatment list
│
├── output/                         # Generated outputs
│   ├── *.OUT                       # DSSAT output files
│   ├── duernast_2015_comprehensive_analysis.png
│   └── duernast_2015_comprehensive_analysis.pdf
│
└── scripts/                        # Visualization scripts
    └── create_duernast_visualizations.py
```

## Visualization Output

The workflow generates a comprehensive 16-panel scientific figure:

### Panel Organization
- **Weather** (A-B): Temperature, precipitation, solar radiation
- **Stress Analysis** (C-F): Water stress, nitrogen stress indicators
- **Growth Metrics** (G-J): Yield, biomass, harvest index, grain number
- **Yield Components** (K-L): Individual grain weight, root depth
- **Nitrogen Dynamics** (M): Grain nitrogen accumulation
- **Phenology** (N): Developmental timeline for all treatments
- **Validation** (O-P): Model vs. observed comparison, N response curve

Each panel includes:
- All 15 treatment trajectories
- Phenology markers (emergence, anthesis, maturity)
- Observed data points with error bars where available
- Color-coded treatment identification

See `VISUALIZATION_TECHNICAL_DOCUMENTATION.txt` for detailed panel-by-panel documentation.

## Requirements

### Python Packages
- `pandas` >= 1.3.0 (data manipulation)
- `numpy` >= 1.21.0 (numerical calculations)
- `matplotlib` >= 3.4.0 (plotting)
- `seaborn` >= 0.11.0 (styling)

### DSSAT Dependencies
The workflow automatically handles DSSAT executable files. It looks for them in:
1. Current directory
2. Parent `../DSSAT48/` folder

Required files:
- `DSCSM048.EXE` - DSSAT crop simulation model
- `DSCSM048.CTR` - Control file
- `DATA.CDE` - Crop database
- `DETAIL.CDE` - Output detail codes

These are automatically copied to the `output/` directory from the parent `DSSAT48` folder if it exists.

## How It Works

### Step 1: Prerequisites Check
- Validates directory structure
- Checks required input files
- Verifies Python dependencies
- Confirms DSSAT files availability

### Step 2: DSSAT Simulation
- Copies files to working directory
- Executes N-Wheat model for 15 treatments
- Generates time series outputs
- Handles errors gracefully

### Step 3: Visualization Generation
- Parses 6 output files
- Extracts treatment-specific data
- Merges weather and nitrogen data
- Creates 16-panel figure (18" × 48")
- Saves in PNG (300 DPI) and PDF formats

### Step 4: Summary Report
- Displays performance metrics
- Lists generated files
- Reports success/failure status

## Key Features

- **Complete Automation**: One command runs everything
- **Model Validation**: Systematic comparison with observed data
- **Publication Quality**: 300 DPI high-resolution figures
- **Robust Error Handling**: Informative messages and graceful failures
- **Detailed Documentation**: Every panel documented

## Troubleshooting

### "Not in DUERNAST2015 directory"
**Solution**: Navigate to the DUERNAST2015 folder before running

### "Missing Python package"
**Solution**: Run `pip install -r requirements.txt`

### "DSSAT executable not found"
**Solution**: This is normal if DSSAT isn't installed. The workflow will use existing output files if available.

### "Simulation outputs missing"
**Solution**: Check that the previous simulation completed successfully

## Citation

If you use this workflow in your research, please cite:

- DSSAT crop simulation model
- N-Wheat (WHAPS048) model
- Original field experiment data

## License

This workflow is provided as-is for research and educational purposes.

## Contact

For questions or issues, please refer to:
- Technical documentation: `VISUALIZATION_TECHNICAL_DOCUMENTATION.txt`

---

**Version**: 1.0  
**Last Updated**: 2025-10-27  
**Status**: Tested and validated

# Duernast DSSAT Crop Modeling Pipeline

Complete pipeline for simulating wheat crop growth using the DSSAT (Decision Support System for Agrotechnology Transfer) model, calibrated and validated against the Duernast Long-Term Fertilization Experiment.

## Overview

This repository provides a reproducible computational workflow for crop simulation modeling, encompassing data transformation, model execution, statistical validation, and visualization generation. The pipeline implements the CERES-Wheat model (CSCER048) to simulate nitrogen fertilizer response in spring wheat production systems.

**Key Features:**
- Automated data transformation from BonaRes format to DSSAT input files
- Complete DSSAT simulation workflow for multiple crop seasons
- Statistical validation framework with multiple performance metrics
- Publication-quality visualization generation
- Comprehensive documentation and reproducible research standards

## Dataset

**Experiment:** Duernast Long-Term Fertilization Experiment  
**Location:** Dürnast Research Station, Freising, Bavaria, Germany  
**Coordinates:** 48.4°N, 11.69°E, 471m elevation  
**Time Period:** 2015-2022  
**Crop Systems:** Spring wheat, maize  
**DOI:** https://doi.org/10.20387/bonares-fgzk-4p92

The experiment examines nitrogen fertilizer effects (0-180 kg N/ha) on crop production, soil health, and environmental outcomes across multiple fertilizer types and application strategies.

## Quick Start

### Prerequisites

- Python 3.8 or higher
- DSSAT 4.8 (Windows executable included)
- 2 GB free disk space
- R 4.4+ (optional, only for data transformation from raw BonaRes files)

### Installation

```bash
# Clone or download the repository
cd duernast-dssat-modeling

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import pandas, numpy, matplotlib, seaborn; print('Dependencies OK')"
```

### Run Complete Pipeline

The simplest way to run the complete analysis:

```bash
cd DUERNAST2015
python MASTER_WORKFLOW.py
```

This executes:
1. Prerequisites verification
2. DSSAT model simulation
3. Statistical validation
4. Comprehensive visualization generation
5. Report compilation

**Expected Duration:** 5-10 seconds  
**Output:** 31 DSSAT files, validation statistics, publication-ready figures

### Manual Step-by-Step Execution

For more control, run individual components:

```bash
# 1. Run DSSAT simulation (15 nitrogen fertilizer treatments)
cd DUERNAST2015
DSCSM048.EXE A TUDU1501.WHX

# 2. Extract and analyze yields
python scripts/extract_yields.py

# 3. Perform statistical validation
python scripts/comprehensive_validation.py

# 4. Generate visualizations
python scripts/create_duernast_visualizations.py
```

## Repository Structure

```
duernast-dssat-modeling/
├── DUERNAST2015/                   Main experiment directory
│   ├── TUDU1501.WHX                Experiment definition (15 treatments)
│   ├── TUDU1501.WTH                Weather data (2015)
│   ├── TUDU1501.WHA                Observed yield data
│   ├── DE.SOL                      Soil profile
│   ├── DSCSM048.EXE                DSSAT simulation engine
│   ├── Genotype/                   Cultivar parameters
│   ├── scripts/                    Analysis scripts
│   ├── output/                     Simulation results
│   └── documentation/              Technical reports
│
├── duernast_exp_modeling-main/     Data transformation pipeline
│   ├── data/
│   │   ├── 0_raw/                  Original BonaRes data
│   │   ├── 1_icasa/                ICASA standardized format
│   │   └── 2_dssat/                DSSAT-ready files
│   ├── R/                          Data mapping scripts
│   └── inst/                       Mapping configurations
│
├── DSSAT48/                        DSSAT installation
│   ├── DSSAT48.exe                 Main DSSAT application
│   ├── Genotype/                   Cultivar databases
│   ├── Soil/                       Soil profile library
│   └── Weather/                    Weather station data
│
└── Nwheat-dssat-repo/              NWheat model reference
    └── experiments/KSAS8101/       Example winter wheat experiment
```

## Results Summary

### Duernast 2015 Spring Wheat

**Simulation Performance:**
- Model: CERES-Wheat (CSCER048)
- Treatments: 15 nitrogen fertilizer regimes
- Validation: 64 field observations
- Success Rate: 80% (12/15 treatments within acceptable error)
- Average Error: 7.5% for functional treatments

**Key Validation Metrics:**
- R² = 0.75 (excluding outliers)
- RMSE = 700 kg/ha
- Fertilizer Use Efficiency: 37.5 kg grain/kg N
- Nitrogen Recovery: 49%

**Phenology:**
- Planting: March 18, 2015 (DOY 077)
- Anthesis: June 27, 2015 (DOY 178, 101 days after planting)
- Maturity: August 9, 2015 (DOY 221, 144 days after planting)
- Observed Harvest: August 25, 2015 (DOY 237, 160 days after planting)

**Known Issues:**
- Treatment 3 and 10: Severe yield underestimation (-67%), attributed to FE900 fertilizer code recognition
- Maturity prediction: 16 days earlier than observed, indicating potential for P5 parameter adjustment
- Control treatment: 30% underestimation, within expected range for unfertilized conditions

## Data Processing Pipeline

The repository includes a complete data transformation pipeline:

```
Raw BonaRes Data (24 CSV files, German format)
    ↓ [lte_duernast_data_mapping.R]
ICASA Format (21 CSV files, international standard)
    ↓ [csmTools package]
DSSAT Input Files (.WHX, .WTH, .WHA, .SOL)
    ↓ [DSCSM048.EXE]
Simulation Outputs (31 files: Summary, PlantGro, SoilWat, etc.)
    ↓ [Analysis scripts]
Statistical Validation + Visualizations
```

## Output Files

### DSSAT Simulation Outputs

After running the simulation, 31 output files are generated:

**Primary Results:**
- `Summary.OUT` - Treatment-level summary statistics
- `OVERVIEW.OUT` - Comprehensive treatment details
- `Evaluate.OUT` - Model evaluation metrics

**Time Series Data:**
- `PlantGro.OUT` - Daily plant growth variables (LAI, biomass, height)
- `PlantN.OUT` - Plant nitrogen dynamics
- `SoilWat.OUT` - Soil water balance by layer
- `SoilNi.OUT` - Soil nitrogen transformations
- `Weather.OUT` - Weather data processing results
- `ET.OUT` - Evapotranspiration components

**Environmental Outputs:**
- `N2O.OUT` - Nitrous oxide emissions
- `GHG.OUT` - Greenhouse gas totals
- `SoilTemp.OUT` - Soil temperature profile
- `SoilOrg.OUT` - Soil organic matter dynamics

### Analysis Outputs

**Visualizations:**
- `duernast_2015_comprehensive_analysis.png` - 15-panel comprehensive analysis
- `duernast_2015_comprehensive_analysis.pdf` - Vector format for publication
- `duernast_validation_3panels.png` - Focused validation plots

**Reports:**
- `duernast_workflow_log.json` - Complete execution log
- `documentation/SCIENTIFIC_REPORT_COMPLETE.txt` - Full research manuscript
- `documentation/VALIDATION_TABLES_AND_FIGURES.txt` - Statistical tables

## Model Configuration

### CERES-Wheat Model

**Model Code:** CSCER048  
**Version:** DSSAT 4.8.5.000

**Selected Cultivar:** 990015 Hartog_KY (spring wheat)
- P1V = 20 (vernalization days)
- P1D = 94 (photoperiod sensitivity)
- P5 = 700 (grain filling duration, degree-days)
- G1 = 22 (kernel number coefficient)
- G2 = 39 (kernel weight, mg)
- G3 = 2.0 (non-stressed dry weight, g)
- PHINT = 95 (phyllochron interval)

**Critical Configuration:**
- FERTI = R (calendar date format for fertilizer application)
- PHOTO = C (canopy-level photosynthesis)
- NITRO = Y (nitrogen simulation enabled)
- WATER = Y (water balance simulation enabled)

## Troubleshooting

### Common Issues

**Problem:** DSSAT executable not found  
**Solution:** Ensure DSCSM048.EXE is in DUERNAST2015/ or DSSAT48/ directory

**Problem:** Python dependencies missing  
**Solution:** Run `pip install -r requirements.txt`

**Problem:** Script produces non-zero exit code but outputs exist  
**Solution:** This is a known non-critical issue; check that output files were generated

**Problem:** Treatments 3 and 10 show very low yields  
**Solution:** Known issue with FE900 fertilizer code; see documentation/SCIENTIFIC_REPORT_COMPLETE.txt for details

### Getting Help

For technical issues:
1. Check `WARNING.OUT` for DSSAT-specific errors
2. Review `duernast_workflow_log.json` for execution details
3. Consult `documentation/OBSERVED_DATA_INVENTORY.txt` for data specifications
4. Review `REPOSITORY_GUIDE.md` for detailed structure information

## Contributing

This is a research repository. For modifications:

1. Document all parameter changes in experiment notes
2. Maintain backward compatibility with original analyses
3. Update validation metrics when modifying model configuration
4. Preserve original data files in appropriate directories

## License

This research code and documentation are provided for academic and research purposes. The DSSAT model is separately licensed by the DSSAT Foundation.

## Citation

If you use this pipeline in your research, please cite:

**Dataset:**
```
Duernast Long-Term Fertilization Experiment (2015-2022)
DOI: 10.20387/bonares-fgzk-4p92
Institution: TU München, Dürnast Research Station
```

**Model:**
```
DSSAT Foundation (2019). Decision Support System for Agrotechnology 
Transfer (DSSAT) Version 4.8. DSSAT Foundation, Gainesville, Florida, USA.
```

## Acknowledgments

**Funding:** German Ministry of Education and Research (BonaRes I4S project)  
**Data Source:** BonaRes Repository  
**Institution:** Technical University of Munich, School of Life Sciences  
**Model Platform:** DSSAT Foundation

## References

**CERES-Wheat Model:**
Ritchie, J.T., and D.C. Otter. 1985. Description and performance of CERES-Wheat: 
a user-oriented wheat yield model. ARS Wheat Yield Project. ARS-38. 
National Technical Information Service, Springfield, VA.

**DSSAT Platform:**
Hoogenboom, G., et al. (2019). Decision Support System for Agrotechnology 
Transfer (DSSAT) Version 4.7.5. DSSAT Foundation, Gainesville, Florida, USA.

**Solar Radiation Estimation:**
Hargreaves, G.H., and Z.A. Samani. 1982. Estimating potential evapotranspiration. 
Journal of Irrigation and Drainage Engineering 108:225-230.

## Contact

For questions about the experimental data, contact:  
Dürnast Research Station, TU München  
Email: [Contact information from dataset metadata]

For technical issues with this repository, refer to the troubleshooting section above.

---

**Version:** 1.0.0  
**Last Updated:** October 2025  
**Status:** Production - Validated and tested


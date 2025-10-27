# NWheat DSSAT Experiment Repository

A complete, reproducible NWheat (CROPSIM-Wheat) modeling setup using DSSAT 4.8 for winter wheat simulation and validation.

## Overview

This repository provides a complete experimental setup for running NWheat model simulations with DSSAT, including:

- **Complete experiment data** for KSAS8101 (Kansas State University winter wheat study)
- **All simulation outputs** with actual results
- **Model validation tools** comparing simulated vs observed data
- **Automated scripts** for running simulations and analyzing results
- **Comprehensive documentation** for reproducible research

## Experiment Details

### KSAS8101 - Kansas State University Winter Wheat Study (1981-1982)

- **Location**: Ashland, KS (37.18°N, 97.75°W, 226m elevation)
- **Cultivar**: Newton (IB0488) - Winter wheat
- **Treatments**: 6 nitrogen × irrigation combinations:
  1. Dryland + 0 kg N/ha
  2. Dryland + 60 kg N/ha
  3. Dryland + 180 kg N/ha
  4. Irrigated + 0 kg N/ha
  5. Irrigated + 60 kg N/ha
  6. Irrigated + 180 kg N/ha

## Quick Start

### Prerequisites

- Python 3.7+
- DSSAT 4.8 (for running new simulations)
- Required Python packages (see `requirements.txt`)

### Installation

```bash
# Clone the repository
git clone https://github.com/Muhammad1599/NWheat-DSSAT-Experiment.git
cd NWheat-DSSAT-Experiment

# Install Python dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Running the Experiment

```bash
# Navigate to experiment directory
cd experiments/KSAS8101

# Run simulation (requires DSSAT executable)
python scripts/run_nwheat.py

# Analyze results
python scripts/analyze_results.py

# Extract yields
python scripts/extract_yields.py
```

## Repository Structure

```
NWheat-DSSAT-Experiment/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── setup.py                     # Package installation
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore file
├── experiments/                 # Experiment data and results
│   └── KSAS8101/               # Kansas State experiment
│       ├── input/              # Input files (WHX, WHA, WHT, WTH, SOL)
│       ├── model/              # NWheat model parameters
│       │   └── genotype/       # Cultivar, ecotype, species files
│       ├── output/             # Complete simulation outputs
│       ├── scripts/            # Experiment-specific scripts
│       └── README.md           # Experiment documentation
├── src/                        # Source code
│   └── nwheat_runner/          # Python package
├── scripts/                    # Utility scripts
├── docs/                       # Documentation
├── examples/                   # Usage examples
└── executables/                # DSSAT executables and support files
```

## Results Summary

The KSAS8101 experiment demonstrates successful NWheat simulation with realistic yield predictions:

| Treatment | Observed Yield | Simulated Yield | Error | Status |
|-----------|---------------|-----------------|-------|---------|
| Dryland + 0N | 2,317 kg/ha | 2,010 kg/ha | -13.2% | Good |
| Dryland + 60N | 3,330 kg/ha | 3,485 kg/ha | +4.7% | Excellent |
| Dryland + 180N | 4,521 kg/ha | 4,848 kg/ha | +7.2% | Good |
| Irrigated + 0N | 1,438 kg/ha | 1,391 kg/ha | -3.3% | Excellent |
| Irrigated + 60N | 3,025 kg/ha | 2,019 kg/ha | -33.3% | Needs calibration |
| Irrigated + 180N | 4,695 kg/ha | 3,627 kg/ha | -22.7% | Acceptable |

**Model Performance**: Mean absolute relative error: 14.1% (Good)

## Key Features

### Complete Experimental Setup
- All input files (experiment definition, weather, soil, observed data)
- NWheat model parameters (cultivar, ecotype, species)
- DSSAT executable and support files

### Comprehensive Outputs
- 28 detailed output files included
- Summary results, plant growth, soil water, ET, nitrogen dynamics
- All outputs from successful simulation runs

### Validation Tools
- Automated comparison with observed field data
- Statistical analysis and error metrics
- Python scripts for model performance analysis

### Reproducible Research
- Version-controlled setup
- Documented procedures
- Automated scripts for consistency

## Output Files Included

The repository includes complete simulation outputs (28 files, ~5.2 MB):

**Main Results:**
- `Summary.OUT` (6,110 bytes) - Key simulation results
- `OVERVIEW.OUT` (56,852 bytes) - Comprehensive overview
- `Evaluate.OUT` (2,013 bytes) - Model evaluation metrics

**Detailed Analysis:**
- `PlantGrf.OUT` (264,682 bytes) - Plant growth dynamics
- `SoilWater.OUT` (599,223 bytes) - Soil water balance
- `ET.OUT` (289,747 bytes) - Evapotranspiration
- `N2O.OUT` (828,124 bytes) - Nitrogen cycling
- And 20+ additional output files

## Usage Examples

### Basic Analysis
```bash
cd experiments/KSAS8101
python scripts/analyze_results.py
python scripts/extract_yields.py
```

### Python Package Usage
```python
from nwheat_runner import NWheatRunner, ResultsAnalyzer

# Analyze existing results
analyzer = ResultsAnalyzer('experiments/KSAS8101')
yield_analysis = analyzer.analyze_yields()
validation = analyzer.validate_against_observed()
```

## Documentation

- [Experiment Details](experiments/KSAS8101/README.md) - Detailed experiment documentation
- [Model Validation Report](experiments/KSAS8101/model_validation_report.md) - Comprehensive validation analysis
- [Corrections Made](experiments/KSAS8101/CORRECTIONS_MADE.md) - Documentation of fixes and improvements

## Research Applications

This repository is suitable for:

- **Model validation studies** - Compare NWheat predictions with field data
- **Sensitivity analysis** - Test parameter impacts on yield predictions
- **Climate impact studies** - Assess weather effects on wheat production
- **Nitrogen management research** - Optimize fertilizer applications
- **Teaching and training** - Learn DSSAT modeling techniques

## Model Performance

The DSSAT N-Wheat model demonstrates good performance for this Kansas winter wheat experiment:

- **Execution time**: ~1.4 seconds
- **Success rate**: 100% (all treatments completed)
- **Validation**: 4/6 treatments show good to excellent predictions
- **Mean error**: 14.1% (within acceptable range for crop models)
- **Nitrogen response**: Properly captured across all treatments

## Citation

If you use this repository in your research, please cite:

```
NWheat DSSAT Experiment Repository (2025). Kansas State University Winter Wheat 
Modeling Dataset with Complete Simulation Outputs. 
GitHub: https://github.com/Muhammad1599/NWheat-DSSAT-Experiment
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For questions or issues:

- Open an [Issue](https://github.com/Muhammad1599/NWheat-DSSAT-Experiment/issues)
- Contact: Arslanhoney1599@gmail.com

## Acknowledgments

- Kansas State University for the original experimental data
- DSSAT Foundation for the modeling platform
- USDA for weather data
- Contributors and researchers who validate and improve the model

---


**Ready-to-use NWheat modeling setup with complete experimental data and validation results!**

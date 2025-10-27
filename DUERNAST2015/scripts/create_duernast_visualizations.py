#!/usr/bin/env python3
"""
Duernast 2015 Spring Wheat - Comprehensive Visualization Package

Purpose: Creates 16-panel visualization for N-Wheat model results showing seasonal
         progression, stress factors, yield components, and validation against
         observed data for 15 nitrogen treatments.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import re
from collections import Counter

# Set style for publication-quality visualization
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def parse_summary_phenology():
    """Parse phenology stages and nitrogen levels from Summary.OUT for all 15 treatments"""
    
    stages = {}
    n_levels = {}
    
    if not Path('Summary.OUT').exists():
        print("[ERROR] Summary.OUT not found!")
        return None, None
    
    try:
        with open('Summary.OUT', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if not lines:
            print("[ERROR] Summary.OUT is empty!")
            return None, None
        
        # Detect model type from Summary.OUT
        model_type = 'UNKNOWN'
        for line in lines[:10]:
            if 'WHAPS' in line:
                model_type = 'NWHEAT'
                break
        
        print(f"[INFO] Summary.OUT model type: {model_type}")
        
        if model_type != 'NWHEAT':
            print("[ERROR] Only N-Wheat (WHAPS) model is supported!")
            return None, None
        
        # Find data section - look for lines starting with numbers
        data_start = -1
        for i, line in enumerate(lines):
            # Skip header lines and look for data lines
            if line.strip() and line.strip()[0].isdigit() and not line.startswith('!'):
                data_start = i
                break
        
        if data_start == -1:
            print("[ERROR] Could not find data section in Summary.OUT")
            return None, None
        
        # Parse each treatment
        for i in range(data_start, min(data_start + 20, len(lines))):
            line = lines[i].strip()
            if not line or line.startswith('*'):
                continue
            
            parts = line.split()
            if len(parts) >= 51:  # Need at least 51 columns to get NICM
                try:
                    treatment = int(parts[1])
                    sdat = int(parts[16])  # Sowing date (SDAT)
                    pdat = int(parts[17])  # Planting date (PDAT)
                    edat = int(parts[18])  # Emergence date (EDAT)
                    adat = int(parts[19])  # Anthesis date (ADAT)
                    mdat = int(parts[20])  # Maturity date (MDAT)
                    hdat = int(parts[21])  # Harvest date (HDAT)
                    nicm = int(parts[50])   # Nitrogen applied (NICM)
                    
                    # Convert to days after sowing
                    def date_to_das(date, sdate):
                        if date == -99 or sdate == -99:
                            return -99
                        date_doy = date % 1000
                        sdate_doy = sdate % 1000
                        return date_doy - sdate_doy if date_doy >= sdate_doy else date_doy + 365 - sdate_doy
                    
                    stages[treatment] = {
                        'emergence_das': date_to_das(edat, pdat),
                        'anthesis_das': date_to_das(adat, pdat),
                        'maturity_das': date_to_das(mdat, pdat),
                        'harvest_das': date_to_das(hdat, pdat),
                        'sowing_date': sdat,
                        'planting_date': pdat
                    }
                    
                    # Store nitrogen level for this treatment
                    n_levels[treatment] = nicm
                    
                except (ValueError, IndexError) as e:
                    if len(stages) == 0:  # Only warn for first parse attempts
                        print(f"[WARNING] Skipped line {i}: {str(e)[:50]}")
                    continue
        
        if not stages or not n_levels:
            print("[ERROR] No phenology data parsed from Summary.OUT")
            return None, None
        
        return stages, n_levels
        
    except Exception as e:
        print(f"[ERROR] Could not parse Summary.OUT: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def get_consensus_stages(detailed_stages):
    """Get consensus phenology stages (most treatments have same timing)"""
    
    if not detailed_stages or len(detailed_stages) == 0:
        print("[WARNING] No phenology stages provided, using defaults")
        return {'emergence_das': 12, 'anthesis_das': 97, 'maturity_das': 144}
    
    try:
        emergence_vals = [s['emergence_das'] for s in detailed_stages.values() if s.get('emergence_das', -99) != -99]
        anthesis_vals = [s['anthesis_das'] for s in detailed_stages.values() if s.get('anthesis_das', -99) != -99]
        maturity_vals = [s['maturity_das'] for s in detailed_stages.values() if s.get('maturity_das', -99) != -99]
        
        print(f"[DEBUG] Emergence values: {set(emergence_vals) if emergence_vals else 'None'}")
        print(f"[DEBUG] Anthesis values: {set(anthesis_vals) if anthesis_vals else 'None'}")
        print(f"[DEBUG] Maturity values: {set(maturity_vals) if maturity_vals else 'None'}")
        
        if not emergence_vals or not anthesis_vals or not maturity_vals:
            print("[WARNING] Missing phenology values, using defaults")
            return {'emergence_das': 12, 'anthesis_das': 97, 'maturity_das': 144}
        
        consensus = {
            'emergence_das': Counter(emergence_vals).most_common(1)[0][0],
            'anthesis_das': Counter(anthesis_vals).most_common(1)[0][0],
            'maturity_das': Counter(maturity_vals).most_common(1)[0][0]
        }
        
        print(f"[DEBUG] Consensus: {consensus}")
        
        return consensus
    
    except Exception as e:
        print(f"[WARNING] Error calculating consensus stages: {e}, using defaults")
        return {'emergence_das': 12, 'anthesis_das': 97, 'maturity_das': 144}

def detect_model_type():
    """Detect if PlantGro.OUT is from N-Wheat model"""
    
    try:
        with open('PlantGro.OUT', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(500)  # Read first 500 chars
        
        if 'WHAPS' in content or 'N-Wheat' in content:
            return 'NWHEAT'
        else:
            print("[WARNING] Model type not detected as N-Wheat")
            return 'UNKNOWN'
    except Exception as e:
        print(f"[WARNING] Could not detect model type: {e}")
        return 'UNKNOWN'

def parse_temperature_data():
    """Parse Weather.OUT for temperature data (returns dictionary)"""
    
    if not Path('Weather.OUT').exists():
        print("[WARNING] Weather.OUT not found, temperature data unavailable")
        return {}
    
    try:
        weather_by_das = {}
        with open('Weather.OUT', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if not lines:
            print("[WARNING] Weather.OUT is empty")
            return {}
        
        data_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('@YEAR DOY'):
                data_start = i + 1
                break
        
        if data_start == -1:
            print("[WARNING] Could not find data section in Weather.OUT")
            return {}
        
        for i in range(data_start, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith(('*', '@', '!')):
                continue
            
            parts = line.split()
            if len(parts) >= 12:
                try:
                    das = int(parts[2])
                    tavd = float(parts[11])  # TAVD = average daily temperature
                    if -50 <= tavd <= 60:  # Sanity check for temperature
                        weather_by_das[das] = tavd
                except (ValueError, IndexError):
                    continue
        
        if weather_by_das:
            print(f"[INFO] Loaded temperature data for {len(weather_by_das)} days")
        else:
            print("[WARNING] No temperature data parsed from Weather.OUT")
        
        return weather_by_das
    except Exception as e:
        print(f"[WARNING] Error parsing Weather.OUT: {e}")
        return {}

def parse_plantgro_data(n_levels=None):
    """Parse PlantGro.OUT for all 15 treatments (N-Wheat model)
    
    Args:
        n_levels: Dictionary mapping treatment number to N applied (kg/ha)
    """
    
    if not Path('PlantGro.OUT').exists():
        print("[ERROR] PlantGro.OUT not found!")
        return None
    
    # Detect model type
    model_type = detect_model_type()
    print(f"[INFO] Detected model type: {model_type}")
    
    if model_type != 'NWHEAT':
        print("[ERROR] Only N-Wheat model is supported!")
        return None
    
    # Load temperature data (shared across all treatments)
    weather_data = parse_temperature_data()
    
    try:
        with open('PlantGro.OUT', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if not content:
            print("[ERROR] PlantGro.OUT is empty!")
            return None
        
        # Split by RUN sections
        run_sections = re.split(r'\*RUN\s+\d+', content)
        
        treatments_data = {}
        
        # Generate treatment names using actual N levels from data
        fertilizer_types = {
            1: "Harnstoff", 2: "Harnstoff", 3: "Mixed",
            4: "AmmonSulf", 5: "Kalkamm", 6: "Kalkamm",
            7: "Kalkamm", 8: "Kalkamm", 9: "UAN",
            10: "Mixed", 11: "Kalkstick", 12: "Mixed",
            13: "UAN", 14: "UAN", 15: "Control"
        }
        
        treatment_names = {}
        for trt in range(1, 16):
            fert_type = fertilizer_types.get(trt, f"Trt{trt}")
            if n_levels and trt in n_levels:
                n_kg = n_levels[trt]
                if trt == 15:
                    treatment_names[trt] = f"Trt{trt}:Control-{n_kg}N"
                elif trt in [3, 10]:  # Problem treatments - mark with asterisk
                    treatment_names[trt] = f"Trt{trt}:{fert_type}-{n_kg}N*"
                else:
                    treatment_names[trt] = f"Trt{trt}:{fert_type}-{n_kg}N"
            else:
                # Fallback if N levels not provided
                treatment_names[trt] = f"Trt{trt}:{fert_type}"
        
        for run_num in range(1, min(16, len(run_sections))):
            section = run_sections[run_num]
            treatment_name = treatment_names.get(run_num, f"Treatment{run_num}")
            
            lines = section.split('\n')
            data_start = -1
            
            for i, line in enumerate(lines):
                if line.strip().startswith('@YEAR DOY'):
                    data_start = i + 1
                    break
            
            if data_start == -1:
                continue
            
            data_rows = []
            for i in range(data_start, len(lines)):
                line = lines[i].strip()
                
                if not line or line.startswith('*RUN') or line.startswith('$'):
                    break
                
                if line.startswith('@') or line.startswith('*'):
                    continue
                
                parts = line.split()
                
                try:
                    # N-Wheat column positions (WHAPS048 model)
                    if len(parts) >= 35:
                        das = int(parts[2])
                        # Get temperature from Weather.OUT
                        tmean = float(weather_data.get(das, 15.0)) if len(weather_data) > 0 else 15.0
                        
                        # N-Wheat water stress variables (with bounds checking)
                        wspd = max(0.0, min(1.0, float(parts[18])))  # Water stress photosynthesis (0-1)
                        wsgd = max(0.0, min(1.0, float(parts[19])))  # Water stress grain filling (0-1)
                        slft = max(0.0, min(1.0, float(parts[20])))  # Soil water factor for leaves (0-1)
                        nstd = max(0.0, float(parts[21]))  # N stress cumulative (non-negative)
                        
                        # N-Wheat doesn't have daily N stress factor, so derive from cumulative
                        # When NSTD is low (no stress), factor is high (optimal)
                        # NSTD typically ranges 0-100+
                        if nstd == 0:
                            nftd = 1.0
                        else:
                            nftd = max(0.0, min(1.0, 1.0 - (nstd / 100.0)))
                        
                        # Water stress factor: use minimum of photosynthesis and leaf factors
                        if wspd > 0 or slft > 0:
                            wftd = min(wspd, slft)
                        else:
                            wftd = 1.0
                        
                        # Extract values with bounds checking
                        cwad = max(0.0, float(parts[12]))  # Total biomass (non-negative)
                        hwad = max(0.0, float(parts[9]))   # Grain weight (non-negative)
                        hiad = max(0.0, min(1.0, float(parts[16])))  # Harvest index (0-1)
                        h_ad = max(0.0, float(parts[13]))  # Grain number (non-negative)
                        gwgd = max(0.0, float(parts[15]))  # Grain weight per grain (non-negative)
                        rdpd = max(0.0, float(parts[34]))  # Root depth (non-negative)
                        
                        data_rows.append({
                            'DAS': das,
                            'TMEAN': tmean,
                            'CWAD': cwad,
                            'HWAD': hwad,
                            'HIAD': hiad,
                            'H#AD': h_ad,
                            'GWGD': gwgd,
                            'RDPD': rdpd,
                            'WFTD': wftd,
                            'WFPD': wspd,
                            'WFGD': wsgd,
                            'NFTD': nftd,
                            'NSTD': nstd,
                        })
                except (ValueError, IndexError) as e:
                    if run_num == 1 and len(data_rows) < 5:  # Debug first treatment only
                        print(f"[DEBUG] Skipped line (treatment {run_num}): {str(e)[:100]}")
                    continue
            
            if data_rows:
                df = pd.DataFrame(data_rows)
                
                if df.empty:
                    print(f"[WARNING] Empty dataframe for {treatment_name}")
                    continue
                
                # Calculate derived variables with safe operations
                # Use GWGD directly (grain weight per grain in mg) from column 15
                df['grain_size_mg'] = df['GWGD'].clip(lower=0)  # Use direct value, ensure non-negative
                
                # Stress calculations (all already bounded 0-1)
                # Water stress: WFTD is 1=no stress, 0=max stress
                df['daily_water_stress'] = df['WFTD']  # 1=optimal, 0=stressed
                # Cumulative water stress: sum of daily stress amounts (invert factor to get stress)
                df['cumulative_water_stress'] = (1.0 - df['WFTD']).cumsum()  # Sum of stress days
                
                # Nitrogen stress: NFTD is 1=no stress, 0=max stress
                df['daily_nitrogen_stress'] = df['NFTD']  # Keep as is: 1=optimal, 0=stressed
                # Invert to show stress level (makes small variations visible)
                # N-Wheat shows very little N stress (NFTD ~0.99), so invert to magnify differences
                df['nitrogen_stress_level'] = 1.0 - df['NFTD']  # 0=optimal, 1=stressed
                
                # Calculate TRUE cumulative nitrogen stress
                df['cumulative_nitrogen_stress'] = df['nitrogen_stress_level'].cumsum()
                
                treatments_data[treatment_name] = df
        
        if not treatments_data:
            print("[ERROR] No treatment data was parsed successfully!")
            return None
        
        print(f"[INFO] Successfully parsed {len(treatments_data)} treatments")
        return treatments_data
        
    except Exception as e:
        print(f"[ERROR] Error parsing PlantGro.OUT: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse_nitrogen_data(n_levels=None):
    """Parse PlantN.OUT for nitrogen dynamics
    
    Args:
        n_levels: Dictionary mapping treatment number to N applied (kg/ha)
    """
    
    if not Path('PlantN.OUT').exists():
        print("[WARNING] PlantN.OUT not found, skipping nitrogen data")
        return None
    
    try:
        with open('PlantN.OUT', 'r') as f:
            content = f.read()
        
        run_sections = re.split(r'\*RUN\s+\d+', content)
        
        nitrogen_data = {}
        
        # Generate treatment names using actual N levels from data
        fertilizer_types = {
            1: "Harnstoff", 2: "Harnstoff", 3: "Mixed",
            4: "AmmonSulf", 5: "Kalkamm", 6: "Kalkamm",
            7: "Kalkamm", 8: "Kalkamm", 9: "UAN",
            10: "Mixed", 11: "Kalkstick", 12: "Mixed",
            13: "UAN", 14: "UAN", 15: "Control"
        }
        
        treatment_names = {}
        for trt in range(1, 16):
            fert_type = fertilizer_types.get(trt, f"Trt{trt}")
            if n_levels and trt in n_levels:
                n_kg = n_levels[trt]
                if trt == 15:
                    treatment_names[trt] = f"Trt{trt}:Control-{n_kg}N"
                elif trt in [3, 10]:
                    treatment_names[trt] = f"Trt{trt}:{fert_type}-{n_kg}N*"
                else:
                    treatment_names[trt] = f"Trt{trt}:{fert_type}-{n_kg}N"
            else:
                treatment_names[trt] = f"Trt{trt}:{fert_type}"
        
        for run_num in range(1, min(16, len(run_sections))):
            section = run_sections[run_num]
            treatment_name = treatment_names.get(run_num, f"Treatment{run_num}")
            
            lines = section.split('\n')
            data_start = -1
            
            for i, line in enumerate(lines):
                if line.strip().startswith('@YEAR DOY'):
                    data_start = i + 1
                    break
            
            if data_start == -1:
                continue
            
            data_rows = []
            for i in range(data_start, len(lines)):
                line = lines[i].strip()
                if not line or line.startswith('*') or line.startswith('@'):
                    break
                
                parts = line.split()
                if len(parts) >= 6:  # Need at least columns 0-5 for GNAD
                    try:
                        data_rows.append({
                            'DAS': int(parts[2]),
                            'CNAD': float(parts[4]),  # Crop N (total: leaves+stems+grains)
                            'GNAD': float(parts[5]),  # Grain N (only grains) - CORRECT INDEX!
                            'nitrogen_uptake': float(parts[5]),  # Use GNAD for comparison with observed
                        })
                    except (ValueError, IndexError):
                        continue
            
            if data_rows:
                nitrogen_data[treatment_name] = pd.DataFrame(data_rows)
        
        return nitrogen_data
        
    except Exception as e:
        print(f"[WARNING] Could not parse nitrogen data: {e}")
        return None

def parse_weather_data():
    """Parse Weather.OUT for environmental variables"""
    
    if not Path('Weather.OUT').exists():
        print("[WARNING] Weather.OUT not found")
        return None
    
    try:
        with open('Weather.OUT', 'r') as f:
            content = f.read()
        
        # Split by RUN sections - just get first one (weather same for all)
        run_sections = re.split(r'\*RUN\s+\d+', content)
        
        if len(run_sections) < 2:
            return None
        
        section = run_sections[1]
        lines = section.split('\n')
        data_start = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('@YEAR DOY'):
                data_start = i + 1
                break
        
        if data_start == -1:
            return None
        
        data_rows = []
        for i in range(data_start, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith('*') or line.startswith('@'):
                break
            
            parts = line.split()
            if len(parts) >= 12:
                try:
                    data_rows.append({
                        'DAS': int(parts[2]),
                        'PRED': float(parts[3]),  # Precipitation
                        'SRAD': float(parts[6]),  # Solar radiation (SRAD column 6)
                        'TMAX': float(parts[9]),  # Max temp (TMXD column 9)
                        'TMIN': float(parts[10]),  # Min temp (TMND column 10)
                    })
                except (ValueError, IndexError):
                    continue
        
        if data_rows:
            return pd.DataFrame(data_rows)
        
    except Exception as e:
        print(f"[WARNING] Could not parse weather: {e}")
        return None

def parse_observed_data(n_levels=None):
    """Parse observed data (yield, grain weight, grain nitrogen) for validation
    
    Args:
        n_levels: Dictionary mapping treatment number to N applied (kg/ha)
    
    Returns:
        Dictionary with treatment names as keys, containing:
        - yield: mean harvest yield (kg/ha)
        - grain_weight: mean grain weight (mg) if available
        - grain_nitrogen: mean grain N (kg/ha) if available
        - std_yield, std_grain_weight, std_grain_nitrogen: standard deviations
        - n: number of replications
    """
    
    try:
        # Try .WHT file first (has more data: yield + grain weight + grain nitrogen)
        wht_file = Path('TUDU1501.WHT')
        wha_file = Path('TUDU1501.WHA')
        
        observed_raw = {}
        has_grain_data = False
        
        if wht_file.exists():
            print("  [OK] Using TUDU1501.WHT (detailed data: yield + grain weight + grain N)")
            with open('TUDU1501.WHT', 'r') as f:
                lines = f.readlines()
            
            # Parse .WHT format: TRNO DATE HWAD GWGD GNAD
            for line in lines:
                if line.strip() and not line.startswith('@') and not line.startswith('*') and not line.startswith('!'):
                    parts = line.split()
                    if len(parts) >= 5:  # Need all 5 columns
                        try:
                            treatment = int(parts[0])
                            hwad_obs = int(parts[2])      # Harvest weight (kg/ha)
                            gwgd_obs = int(parts[3])      # Grain weight (mg/grain)
                            gnad_obs = int(parts[4])      # Grain nitrogen (kg N/ha)
                            
                            if treatment not in observed_raw:
                                observed_raw[treatment] = {
                                    'yield': [],
                                    'grain_weight': [],
                                    'grain_nitrogen': []
                                }
                            observed_raw[treatment]['yield'].append(hwad_obs)
                            observed_raw[treatment]['grain_weight'].append(gwgd_obs)
                            observed_raw[treatment]['grain_nitrogen'].append(gnad_obs)
                            has_grain_data = True
                        except (ValueError, IndexError):
                            continue
        
        elif wha_file.exists():
            print("  [OK] Using TUDU1501.WHA (yield only)")
            with open('TUDU1501.WHA', 'r') as f:
                lines = f.readlines()
            
            # Parse .WHA format: TRNO HDAT HWAM
            for line in lines:
                if line.strip() and not line.startswith('@') and not line.startswith('*') and not line.startswith('!'):
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            treatment = int(parts[0])
                            hwam_obs = int(parts[2])
                            
                            if treatment not in observed_raw:
                                observed_raw[treatment] = {
                                    'yield': [],
                                    'grain_weight': [],
                                    'grain_nitrogen': []
                                }
                            observed_raw[treatment]['yield'].append(hwam_obs)
                        except (ValueError, IndexError):
                            continue
        
        else:
            print("  [WARNING] No observed data file found (TUDU1501.WHT or .WHA)")
            return None
        
        # Generate treatment names using actual N levels from data
        fertilizer_types = {
            1: "Harnstoff", 2: "Harnstoff", 3: "Mixed",
            4: "AmmonSulf", 5: "Kalkamm", 6: "Kalkamm",
            7: "Kalkamm", 8: "Kalkamm", 9: "UAN",
            10: "Mixed", 11: "Kalkstick", 12: "Mixed",
            13: "UAN", 14: "UAN", 15: "Control"
        }
        
        # Calculate means and standard deviations
        observed_means = {}
        for treatment, data in observed_raw.items():
            fert_type = fertilizer_types.get(treatment, f"Trt{treatment}")
            
            if n_levels and treatment in n_levels:
                n_kg = n_levels[treatment]
                if treatment == 15:
                    trt_name = f"Trt{treatment}:Control-{n_kg}N"
                elif treatment in [3, 10]:
                    trt_name = f"Trt{treatment}:{fert_type}-{n_kg}N*"
                else:
                    trt_name = f"Trt{treatment}:{fert_type}-{n_kg}N"
            else:
                trt_name = f"Trt{treatment}:{fert_type}"
            
            observed_means[trt_name] = {
                'yield': np.mean(data['yield']),
                'std_yield': np.std(data['yield']),
                'n': len(data['yield'])
            }
            
            # Add grain weight data if available
            if has_grain_data and len(data['grain_weight']) > 0:
                observed_means[trt_name]['grain_weight'] = np.mean(data['grain_weight'])
                observed_means[trt_name]['std_grain_weight'] = np.std(data['grain_weight'])
            
            # Add grain nitrogen data if available
            if has_grain_data and len(data['grain_nitrogen']) > 0:
                observed_means[trt_name]['grain_nitrogen'] = np.mean(data['grain_nitrogen'])
                observed_means[trt_name]['std_grain_nitrogen'] = np.std(data['grain_nitrogen'])
        
        # Maintain backward compatibility with 'std' key for yield
        for trt_name in observed_means:
            observed_means[trt_name]['std'] = observed_means[trt_name]['std_yield']
        
        if has_grain_data:
            print(f"  [OK] Loaded yield + grain weight + grain nitrogen for {len(observed_means)} treatments")
        else:
            print(f"  [OK] Loaded yield data for {len(observed_means)} treatments")
        
        return observed_means
        
    except Exception as e:
        print(f"[WARNING] Could not parse observed data: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_treatment_names(n_levels):
    """Generate treatment names using actual N levels from data
    
    Args:
        n_levels: Dictionary mapping treatment number to N applied (kg/ha)
    
    Returns:
        Dictionary mapping treatment number to display name
    """
    fertilizer_types = {
        1: "Harnstoff", 2: "Harnstoff", 3: "Mixed",
        4: "AmmonSulf", 5: "Kalkamm", 6: "Kalkamm",
        7: "Kalkamm", 8: "Kalkamm", 9: "UAN",
        10: "Mixed", 11: "Kalkstick", 12: "Mixed",
        13: "UAN", 14: "UAN", 15: "Control"
    }
    
    treatment_names = {}
    for trt in range(1, 16):
        fert_type = fertilizer_types.get(trt, f"Trt{trt}")
        if n_levels and trt in n_levels:
            n_kg = n_levels[trt]
            if trt == 15:
                treatment_names[trt] = f"Trt{trt}:Control-{n_kg}N"
            elif trt in [3, 10]:
                treatment_names[trt] = f"Trt{trt}:{fert_type}-{n_kg}N*"
            else:
                treatment_names[trt] = f"Trt{trt}:{fert_type}-{n_kg}N"
        else:
            treatment_names[trt] = f"Trt{trt}:{fert_type}"
    
    return treatment_names

def get_treatment_styles(treatment_names_dict):
    """Define visual styles for 15 treatments
    
    Args:
        treatment_names_dict: Dictionary mapping treatment numbers to names
    """
    
    # Use color palette and line styles to differentiate 15 treatments
    colors = plt.cm.tab20(np.linspace(0, 1, 15))
    
    styles = {}
    
    for i, (trt_num, trt_name) in enumerate(treatment_names_dict.items()):
        # Control treatment - distinct style (thicker to stand out)
        if trt_num == 15:
            styles[trt_name] = {
                'color': 'black',
                'linestyle': ':',
                'linewidth': 2.0,  # Reduced from 3.0
                'alpha': 0.85,     # Slightly more transparent
                'marker': 'o'
            }
        # Problematic treatments - dashed (stand out)
        elif trt_num in [3, 10]:
            styles[trt_name] = {
                'color': colors[i],
                'linestyle': '--',
                'linewidth': 1.2,  # Reduced from 1.5
                'alpha': 0.75,     # Slightly more transparent
                'marker': 'x'
            }
        # Normal treatments - solid thin lines for clarity
        else:
            styles[trt_name] = {
                'color': colors[i],
                'linestyle': '-',
                'linewidth': 0.9,  # Much thinner from 1.8
                'alpha': 0.7,      # More transparent for better overlap visibility
                'marker': None
            }
    
    return styles

def create_comprehensive_visualization(treatments_data, phenology_stages, consensus_stages, 
                                     weather_data=None, nitrogen_data=None, observed_data=None, n_levels=None):
    """Create comprehensive 15-panel visualization for Duernast"""
    
    if not treatments_data:
        print("[ERROR] No treatment data available!")
        return None
    
    print(f"\n[INFO] Creating visualization for {len(treatments_data)} treatments...")
    
    # Generate treatment names from N levels
    if n_levels:
        treatment_names_dict = generate_treatment_names(n_levels)
    else:
        # Fallback to extracting from treatment keys
        treatment_names_dict = {int(k.split('Trt')[1].split(':')[0]): k 
                               for k in treatments_data.keys() if 'Trt' in k}
    
    treatment_styles = get_treatment_styles(treatment_names_dict)
    
    # Create figure with 16 vertical panels (weather, stress, growth, validation)
    fig, axes = plt.subplots(16, 1, figsize=(18, 48))
    fig.suptitle('Duernast 2015 Spring Wheat - Comprehensive Seasonal Analysis\n' + 
                 '15 Treatments × Multiple Variables', 
                 fontsize=20, fontweight='bold', y=0.995)
    
    # Get consensus stages for vertical lines
    if consensus_stages:
        emergence_das = consensus_stages['emergence_das']
        anthesis_das = consensus_stages['anthesis_das']
        maturity_das = consensus_stages['maturity_das']
        print(f"[INFO] Phenology: Emergence={emergence_das}, Anthesis={anthesis_das}, Maturity={maturity_das}")
    else:
        emergence_das, anthesis_das, maturity_das = 7, 101, 144
    
    # Define plot configurations
    # Reordered: Weather/Environmental drivers first, then crop responses, then summaries
    plot_configs = [
        # SECTION 1: Environmental Drivers (most important - drive everything)
        {'idx': 0, 'var': 'weather', 'title': 'a) Weather Pattern (Tmax, Tmin, Rain, Solar Rad)', 'ylabel': 'Multiple'},
        {'idx': 1, 'var': 'TMEAN', 'title': 'b) Mean Temperature', 'ylabel': 'Temperature (°C)'},
        {'idx': 2, 'var': 'daily_water_stress', 'title': 'c) Water Stress Factor (1=optimal, 0=stressed)', 'ylabel': 'Water Stress Factor'},
        {'idx': 3, 'var': 'cumulative_water_stress', 'title': 'd) Cumulative Water Stress (sum of daily stress)', 'ylabel': 'Cumulative Stress'},
        {'idx': 4, 'var': 'nitrogen_stress_level', 'title': 'e) Nitrogen Stress Level (0=optimal, 1=stressed)', 'ylabel': 'N Stress Level (inverted)'},
        {'idx': 5, 'var': 'cumulative_nitrogen_stress', 'title': 'f) Cumulative Nitrogen Stress (sum of daily)', 'ylabel': 'Cumulative N Stress'},
        
        # SECTION 2: Crop Growth Responses
        {'idx': 6, 'var': 'HWAD', 'title': 'g) Grain Yield (lines=simulated, circles=observed)', 'ylabel': 'Grain Yield (kg/ha)'},
        {'idx': 7, 'var': 'CWAD', 'title': 'h) Total Biomass Development', 'ylabel': 'Biomass (kg/ha)'},
        {'idx': 8, 'var': 'HIAD', 'title': 'i) Harvest Index', 'ylabel': 'Harvest Index (0-1)'},
        {'idx': 9, 'var': 'H#AD', 'title': 'j) Grain Number', 'ylabel': 'Grains/m²'},
        {'idx': 10, 'var': 'grain_size_mg', 'title': 'k) Grain Weight (lines=simulated, circles=observed)', 'ylabel': 'mg/grain'},
        {'idx': 11, 'var': 'RDPD', 'title': 'l) Root Depth', 'ylabel': 'Root Depth (cm)'},
        {'idx': 12, 'var': 'nitrogen_uptake', 'title': 'm) Grain Nitrogen (lines=simulated, circles=observed)', 'ylabel': 'Grain N (kg/ha)'},
        
        # SECTION 3: Summary & Validation
        {'idx': 13, 'var': 'phenology_timeline', 'title': 'n) Phenological Stages', 'ylabel': 'Treatments'},
        {'idx': 14, 'var': 'yield_comparison', 'title': 'o) Simulated vs Observed Yields', 'ylabel': 'Yield (kg/ha)'},
        {'idx': 15, 'var': 'fertilizer_response', 'title': 'p) Nitrogen Response Curve', 'ylabel': 'Yield (kg/ha)'},
    ]
    
    # Create each panel
    for config in plot_configs:
        ax = axes[config['idx']]
        var = config['var']
        
        # Special panels
        if var == 'weather':
            # Combined weather plot
            if weather_data is not None:
                ax2 = ax.twinx()
                ax3 = ax.twinx()
                ax3.spines['right'].set_position(('outward', 60))
                
                ax.plot(weather_data['DAS'], weather_data['TMAX'], 
                       color='red', linewidth=1.2, label='Tmax', alpha=0.8)
                ax.plot(weather_data['DAS'], weather_data['TMIN'],
                       color='blue', linewidth=1.2, label='Tmin', alpha=0.8)
                ax2.bar(weather_data['DAS'], weather_data['PRED'],
                       color='skyblue', alpha=0.3, label='Rain', width=1.0)
                ax3.plot(weather_data['DAS'], weather_data['SRAD'],
                        color='orange', linewidth=1.0, label='Solar Rad', alpha=0.7)
                
                ax.set_ylabel('Temperature (°C)', color='red')
                ax2.set_ylabel('Precipitation (mm)', color='blue')
                ax3.set_ylabel('Solar Rad (MJ/m²)', color='orange')
                ax.legend(loc='upper left', fontsize=8)
            
        elif var == 'nitrogen_uptake':
            # Grain nitrogen uptake from PlantN data (GNAD - grain N only, matches observed)
            if nitrogen_data:
                for trt_name, df in nitrogen_data.items():
                    style = treatment_styles.get(trt_name, {})
                    ax.plot(df['DAS'], df['GNAD'],  # Use GNAD (grain N) to match observed! 
                           color=style.get('color', 'black'),
                           linestyle=style.get('linestyle', '-'),
                           linewidth=style.get('linewidth', 0.9),
                           alpha=style.get('alpha', 0.7),
                           label=trt_name if len(nitrogen_data) <= 6 else '')
                
                # Add observed grain nitrogen points at maturity
                if observed_data and consensus_stages:
                    maturity_das = consensus_stages.get('maturity_das', 144)
                    for trt_name in nitrogen_data.keys():
                        if trt_name in observed_data and 'grain_nitrogen' in observed_data[trt_name]:
                            style = treatment_styles.get(trt_name, {})
                            obs_grain_n = observed_data[trt_name]['grain_nitrogen']
                            obs_std_n = observed_data[trt_name].get('std_grain_nitrogen', 0)
                            
                            # Plot observed point at maturity with matching color
                            ax.scatter([maturity_das], [obs_grain_n], 
                                     color=style.get('color', 'black'),
                                     marker='o', s=80, alpha=0.9,
                                     edgecolors='white', linewidth=1.5,
                                     zorder=10)
                            
                            # Add error bars if available
                            if obs_std_n > 0:
                                ax.errorbar([maturity_das], [obs_grain_n], 
                                          yerr=[obs_std_n],
                                          color=style.get('color', 'black'),
                                          fmt='none', capsize=4, alpha=0.6,
                                          linewidth=1.5, zorder=9)
                    
                    # Add legend entry
                    ax.scatter([], [], color='none', marker='o', s=80, 
                             edgecolors='black', linewidth=1.5,
                             label='Observed grain N (circles)', alpha=0.9)
        
        elif var == 'phenology_timeline':
            # Phenology timeline for all treatments
            y_positions = list(range(len(phenology_stages)))
            
            for j, (treatment_num, stages) in enumerate(sorted(phenology_stages.items())):
                trt_name = treatment_names_dict.get(treatment_num, f"Trt{treatment_num}")
                style = treatment_styles.get(trt_name, {})
                
                y_pos = j
                
                # Plot stages
                ax.scatter([0], [y_pos], color=style['color'], s=40, marker='o', alpha=0.8)
                if stages['emergence_das'] != -99:
                    ax.scatter([stages['emergence_das']], [y_pos], color=style['color'], s=40, marker='s', alpha=0.8)
                if stages['anthesis_das'] != -99:
                    ax.scatter([stages['anthesis_das']], [y_pos], color=style['color'], s=40, marker='^', alpha=0.8)
                if stages['maturity_das'] != -99:
                    ax.scatter([stages['maturity_das']], [y_pos], color=style['color'], s=40, marker='D', alpha=0.8)
                
                # Connect with line
                if stages['maturity_das'] != -99:
                    ax.plot([0, stages['maturity_das']], [y_pos, y_pos], 
                           color=style['color'], alpha=0.3, linewidth=2)
            
            ax.set_yticks(y_positions)
            ax.set_yticklabels([treatment_names_dict.get(t, f"T{t}") for t in sorted(phenology_stages.keys())], fontsize=8)
            ax.set_xlim(-10, 170)
            
            # Add observed harvest line
            ax.axvline(x=160, color='red', linestyle=':', linewidth=2, label='Observed Harvest (DOY 237, 160 DAS)', alpha=0.8)
            ax.legend(fontsize=8)
        
        elif var == 'yield_comparison':
            # Simulated vs Observed comparison
            if observed_data:
                sim_yields = []
                obs_yields = []
                trt_labels = []
                colors_list = []
                
                for trt_name in sorted(treatments_data.keys()):
                    if trt_name in observed_data:
                        sim_yield = treatments_data[trt_name]['HWAD'].iloc[-1]
                        obs_yield = observed_data[trt_name]['yield']
                        
                        sim_yields.append(sim_yield)
                        obs_yields.append(obs_yield)
                        trt_labels.append(trt_name.split(':')[0])  # Short name
                        
                        style = treatment_styles.get(trt_name, {})
                        colors_list.append(style.get('color', 'black'))
                
                x_pos = range(len(trt_labels))
                
                # Plot bars
                ax.bar([x - 0.2 for x in x_pos], obs_yields, width=0.4, 
                      color=colors_list, alpha=0.6, label='Observed')
                ax.bar([x + 0.2 for x in x_pos], sim_yields, width=0.4,
                      color=colors_list, alpha=0.9, label='Simulated')
                
                # Add error percentages
                for i, (obs, sim) in enumerate(zip(obs_yields, sim_yields)):
                    error_pct = ((sim - obs) / obs * 100)
                    ax.text(i, max(obs, sim) + 200, f'{error_pct:+.0f}%',
                           ha='center', fontsize=7, fontweight='bold')
                
                ax.set_xticks(x_pos)
                ax.set_xticklabels(trt_labels, rotation=45, ha='right', fontsize=8)
                ax.legend(fontsize=9)
                ax.grid(True, alpha=0.3)
        
        elif var == 'fertilizer_response':
            # N response curve using extracted N levels from Summary.OUT
            if observed_data and n_levels:
                # Group by N level (dynamically determined from data)
                unique_n_levels = sorted(set(n_levels.values()))
                n_levels_sim = {n: [] for n in unique_n_levels}
                n_levels_obs = {n: [] for n in unique_n_levels}
                
                for trt_name in sorted(treatments_data.keys()):
                    trt_num = int(trt_name.split('Trt')[1].split(':')[0])
                    n_level = n_levels.get(trt_num, 0)  # Get from extracted data
                    
                    sim_yield = treatments_data[trt_name]['HWAD'].iloc[-1]
                    
                    if n_level in n_levels_sim:
                        n_levels_sim[n_level].append(sim_yield)
                    
                    if trt_name in observed_data:
                        obs_yield = observed_data[trt_name]['yield']
                        if n_level in n_levels_obs:
                            n_levels_obs[n_level].append(obs_yield)
                
                # Calculate means for each N level
                n_vals = [n for n in unique_n_levels if n_levels_sim[n]]
                sim_means = [np.mean(n_levels_sim[n]) for n in n_vals]
                obs_means = [np.mean(n_levels_obs[n]) for n in n_vals if n_levels_obs[n]]
                
                # Plot
                ax.plot(n_vals, sim_means, 'o-', color='blue', linewidth=1.8, 
                       markersize=8, label='Simulated', alpha=0.8)
                if len(obs_means) == len(n_vals):
                    ax.plot(n_vals, obs_means, 's-', color='green', linewidth=1.8,
                           markersize=8, label='Observed', alpha=0.8)
                
                # Add FUE line
                if len(sim_means) >= 2:
                    fue = (sim_means[1] - sim_means[0]) / (n_vals[1] - n_vals[0])
                    ax.text(0.5, 0.95, f'Simulated FUE: {fue:.1f} kg/kg',
                           transform=ax.transAxes, fontsize=10, ha='center',
                           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
                
                ax.set_xlabel('Nitrogen Applied (kg/ha)', fontsize=10)
                ax.legend(fontsize=10)
                ax.grid(True, alpha=0.3)
        
        else:
            # Regular variable plots
            # Special handling for TMEAN: plot only once (same for all treatments)
            if var == 'TMEAN':
                # Get TMEAN from first treatment (same for all)
                first_trt = list(treatments_data.values())[0]
                if 'TMEAN' in first_trt.columns:
                    ax.plot(first_trt['DAS'], first_trt['TMEAN'],
                           color='red', linewidth=2.0, alpha=0.9,
                           label='Mean Temperature')
                    ax.fill_between(first_trt['DAS'], first_trt['TMEAN'], 
                                   alpha=0.3, color='red')
                    # Set Y-axis limits to show full temperature range clearly
                    # Temperature varies from ~2°C (early spring) to ~26°C (summer)
                    ax.set_ylim(0, 28)
                    # Add horizontal reference lines
                    ax.axhline(y=15, color='gray', linestyle=':', alpha=0.4, linewidth=0.8)
                    ax.text(0.02, 15.5, '15°C', transform=ax.get_yaxis_transform(), 
                           fontsize=8, color='gray', alpha=0.7)
            else:
                # Plot all treatments for other variables
                for trt_name, df in treatments_data.items():
                    if var in df.columns:
                        style = treatment_styles.get(trt_name, {})
                        
                        # For clarity, only show labels for control and a few key treatments
                        # Show: Control (15), Problem treatments (3, 10), and representative high N (8, 9)
                        trt_num = int(trt_name.split('Trt')[1].split(':')[0])
                        show_label = trt_num in [3, 8, 9, 10, 15]
                        
                        ax.plot(df['DAS'], df[var],
                               color=style.get('color', 'black'),
                               linestyle=style.get('linestyle', '-'),
                               linewidth=style.get('linewidth', 0.9),
                               alpha=style.get('alpha', 0.7),
                               label=trt_name if show_label else '')
                
                # Set appropriate Y-axis limits for stress factors
                if var == 'daily_water_stress':
                    ax.set_ylim(-0.05, 1.05)  # 0-1 range with small padding
                    ax.axhline(y=1.0, color='green', linestyle=':', alpha=0.3, linewidth=0.8)
                    ax.axhline(y=0.5, color='orange', linestyle=':', alpha=0.3, linewidth=0.8)
                    ax.text(0.02, 1.02, 'Optimal', transform=ax.get_yaxis_transform(), 
                           fontsize=7, color='green', alpha=0.7)
                    ax.text(0.02, 0.52, 'Moderate', transform=ax.get_yaxis_transform(), 
                           fontsize=7, color='orange', alpha=0.7)
                elif var == 'nitrogen_stress_level':
                    # Inverted scale: 0=optimal, higher=more stress
                    # N-Wheat shows minimal stress (0-0.01 range), so zoom in
                    ax.set_ylim(-0.001, 0.015)  # Zoomed to show 0-1.5% stress range
                    ax.axhline(y=0.0, color='green', linestyle=':', alpha=0.3, linewidth=0.8)
                    ax.axhline(y=0.005, color='orange', linestyle=':', alpha=0.3, linewidth=0.8)
                    ax.axhline(y=0.01, color='red', linestyle=':', alpha=0.3, linewidth=0.8)
                    ax.text(0.02, 0.0005, 'Optimal (0%)', transform=ax.get_yaxis_transform(), 
                           fontsize=7, color='green', alpha=0.7)
                    ax.text(0.02, 0.0055, '0.5% stress', transform=ax.get_yaxis_transform(), 
                           fontsize=7, color='orange', alpha=0.7)
                    # Add note about scale
                    ax.text(0.98, 0.95, 'Note: N-Wheat shows minimal N stress\n(zoomed to 0-1.5% range)', 
                           transform=ax.transAxes, fontsize=8, ha='right', va='top',
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
                elif var == 'daily_nitrogen_stress':
                    ax.set_ylim(-0.05, 1.05)  # 0-1 range with small padding
                    ax.axhline(y=1.0, color='green', linestyle=':', alpha=0.3, linewidth=0.8)
                    ax.axhline(y=0.5, color='orange', linestyle=':', alpha=0.3, linewidth=0.8)
                    ax.text(0.02, 1.02, 'Optimal', transform=ax.get_yaxis_transform(), 
                           fontsize=7, color='green', alpha=0.7)
                    ax.text(0.02, 0.52, 'Moderate', transform=ax.get_yaxis_transform(), 
                           fontsize=7, color='orange', alpha=0.7)
            
            # Add observed data points at maturity for grain yield (HWAD)
            if var == 'HWAD' and observed_data:
                for trt_name in treatments_data.keys():
                    if trt_name in observed_data:
                        style = treatment_styles.get(trt_name, {})
                        obs_yield = observed_data[trt_name]['yield']
                        obs_std = observed_data[trt_name]['std']
                        
                        # Plot observed point at maturity with matching treatment color
                        ax.scatter([maturity_das], [obs_yield], 
                                 color=style.get('color', 'black'),
                                 marker='o', s=80, alpha=0.9,
                                 edgecolors='white', linewidth=1.5,
                                 zorder=10)
                        
                        # Add error bars if available
                        if obs_std > 0:
                            ax.errorbar([maturity_das], [obs_yield], 
                                      yerr=[obs_std],
                                      color=style.get('color', 'black'),
                                      fmt='none', capsize=4, alpha=0.6,
                                      linewidth=1.5, zorder=9)
                
                # Add single legend entry for observed data (using a neutral indicator)
                # Note: Actual points are colored to match their respective treatment lines
                ax.scatter([], [], color='none', marker='o', s=80, 
                         edgecolors='black', linewidth=1.5,
                         label='Observed (colored circles)', alpha=0.9)
            
            # Add observed data points for grain weight (grain_size_mg)
            if var == 'grain_size_mg' and observed_data and consensus_stages:
                maturity_das = consensus_stages.get('maturity_das', 144)
                for trt_name in treatments_data.keys():
                    if trt_name in observed_data and 'grain_weight' in observed_data[trt_name]:
                        style = treatment_styles.get(trt_name, {})
                        obs_grain_wt = observed_data[trt_name]['grain_weight']
                        obs_std_grain = observed_data[trt_name].get('std_grain_weight', 0)
                        
                        # Plot observed point at maturity with matching color
                        ax.scatter([maturity_das], [obs_grain_wt], 
                                 color=style.get('color', 'black'),
                                 marker='o', s=80, alpha=0.9,
                                 edgecolors='white', linewidth=1.5,
                                 zorder=10)
                        
                        # Add error bars if available
                        if obs_std_grain > 0:
                            ax.errorbar([maturity_das], [obs_grain_wt], 
                                      yerr=[obs_std_grain],
                                      color=style.get('color', 'black'),
                                      fmt='none', capsize=4, alpha=0.6,
                                      linewidth=1.5, zorder=9)
                
                # Add legend entry
                ax.scatter([], [], color='none', marker='o', s=80, 
                         edgecolors='black', linewidth=1.5,
                         label='Observed (colored circles)', alpha=0.9)
        
        # Standard formatting
        ax.set_title(config['title'], fontsize=11, fontweight='bold', pad=6)
        ax.set_ylabel(config['ylabel'], fontsize=10)
        ax.grid(True, alpha=0.3, linewidth=0.8)
        
        # CRITICAL: Set consistent x-axis limits for all panels (except special ones)
        if var not in ['phenology_timeline', 'yield_comparison', 'fertilizer_response', 'weather']:
            ax.set_xlim(0, 150)  # Force all panels to use the same x-axis scale
            # Set explicit x-axis tick marks at regular intervals and phenology points
            import numpy as np
            # Use actual phenology stages from data instead of hardcoded values
            if consensus_stages:
                xticks = [0, consensus_stages['emergence_das'], 20, 40, 60, 80, 
                         consensus_stages['anthesis_das'], 120, consensus_stages['maturity_das']]
            else:
                xticks = [0, 7, 20, 40, 60, 80, 101, 120, 144]  # Fallback
            ax.set_xticks(xticks)
        
        # Add phenology markers (except for special panels)
        if var not in ['phenology_timeline', 'yield_comparison', 'fertilizer_response', 'weather']:
            # Debug: print actual x-axis range for first plot
            if config['idx'] == 0:
                first_trt = list(treatments_data.values())[0]
                print(f"[DEBUG] X-axis (DAS) range in data: {first_trt['DAS'].min()} to {first_trt['DAS'].max()}")
                print(f"[DEBUG] Plotting vertical lines at: Emergence={emergence_das}, Anthesis={anthesis_das}, Maturity={maturity_das}")
            
            # Draw phenology lines with higher visibility
            ax.axvline(x=emergence_das, color='green', linestyle='--', alpha=0.6, linewidth=1.2, label=f'Emergence ({emergence_das})')
            ax.axvline(x=anthesis_das, color='deeppink', linestyle='--', alpha=0.6, linewidth=1.2, label=f'Anthesis ({anthesis_das})')
            ax.axvline(x=maturity_das, color='darkorange', linestyle='--', alpha=0.6, linewidth=1.2, label=f'Maturity ({maturity_das})')
            
            # Add text labels at top of plot for first panel only
            if config['idx'] == 0:
                y_max = ax.get_ylim()[1]
                ax.text(emergence_das, y_max * 0.95, f'E\n{emergence_das}', ha='center', fontsize=8, color='green', fontweight='bold')
                ax.text(anthesis_das, y_max * 0.95, f'A\n{anthesis_das}', ha='center', fontsize=8, color='deeppink', fontweight='bold')
                ax.text(maturity_das, y_max * 0.95, f'M\n{maturity_das}', ha='center', fontsize=8, color='darkorange', fontweight='bold')
        
        # Show x-axis labels on ALL panels for better readability
        # This is especially important for tall multi-panel plots
        if var not in ['phenology_timeline', 'yield_comparison', 'fertilizer_response', 'weather']:
            ax.set_xlabel('Days After Planting (DAS)', fontsize=9)
        
        # Only add bold label to the very last panel
        if config['idx'] == len(plot_configs) - 1:
            ax.set_xlabel('Days After Planting (DAS)', fontsize=12, fontweight='bold')
        
        # Add legend for select panels
        if config['idx'] in [0, 6, 13]:  # First, nitrogen panel, comparison panel
            if ax.get_legend_handles_labels()[0]:  # If there are labels
                ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=7)
    
    # Add overall phenology legend
    fig.text(0.02, 0.985, 'Phenology Markers:', fontsize=10, fontweight='bold')
    fig.text(0.02, 0.980, f'Green: Emergence ({emergence_das} DAS)', fontsize=9, color='green')
    fig.text(0.02, 0.975, f'Pink: Anthesis ({anthesis_das} DAS)', fontsize=9, color='deeppink')
    fig.text(0.02, 0.970, f'Orange: Maturity ({maturity_das} DAS)', fontsize=9, color='orange')
    fig.text(0.02, 0.965, f'Red Dash: Observed Harvest (160 DAS)', fontsize=9, color='red')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.96, right=0.88, left=0.08, bottom=0.02, hspace=0.35)
    
    return fig

def main():
    """Main execution function"""
    
    print("="*80)
    print("DUERNAST 2015 SPRING WHEAT - COMPREHENSIVE VISUALIZATION")
    print("="*80)
    print()
    print("Creating 15-panel vertical layout with:")
    print("  - 15 treatments (vs 6 in KSAS8101)")
    print("  - Grain yield, biomass, harvest index")
    print("  - Root development, grain components")
    print("  - Nitrogen and water stress")
    print("  - Weather patterns")
    print("  - Phenology timeline")
    print("  - Simulated vs observed comparison")
    print("  - Nitrogen response curve")
    print()
    
    # Check required files
    required_files = ['PlantGro.OUT', 'Summary.OUT']
    missing = [f for f in required_files if not Path(f).exists()]
    
    if missing:
        print(f"[ERROR] Missing required files: {missing}")
        print("Please run simulation first: DSCSM048.EXE A TUDU1501.WHX")
        return 1
    
    # Check for observed data (prefer .WHT, fallback to .WHA)
    if not (Path('TUDU1501.WHT').exists() or Path('TUDU1501.WHA').exists()):
        print("[WARNING] No observed data file found (TUDU1501.WHT or TUDU1501.WHA)")
        print("Visualization will proceed without observed data points.")
    
    # Parse all data
    print("[1/6] Parsing phenology stages and nitrogen levels...")
    phenology_stages, n_levels = parse_summary_phenology()
    if not phenology_stages:
        print("[ERROR] Failed to parse phenology!")
        return 1
    
    consensus_stages = get_consensus_stages(phenology_stages)
    print(f"[OK] Loaded phenology for {len(phenology_stages)} treatments")
    print(f"[OK] Loaded nitrogen levels for {len(n_levels)} treatments")
    
    print("[2/6] Parsing plant growth data...")
    treatments_data = parse_plantgro_data(n_levels)
    if not treatments_data:
        print("[ERROR] Failed to parse PlantGro.OUT!")
        return 1
    print(f"[OK] Loaded growth data for {len(treatments_data)} treatments")
    
    print("[3/6] Parsing nitrogen data...")
    nitrogen_data = parse_nitrogen_data(n_levels)
    if nitrogen_data:
        print(f"[OK] Loaded nitrogen data for {len(nitrogen_data)} treatments")
    
    print("[4/6] Parsing weather data...")
    weather_data = parse_weather_data()
    if weather_data is not None:
        print(f"[OK] Loaded weather data ({len(weather_data)} days)")
    
    print("[5/6] Parsing observed data...")
    observed_data = parse_observed_data(n_levels)
    if observed_data:
        print(f"[OK] Loaded observed data for {len(observed_data)} treatments")
    
    print("[6/6] Creating comprehensive visualization...")
    fig = create_comprehensive_visualization(
        treatments_data, phenology_stages, consensus_stages,
        weather_data, nitrogen_data, observed_data, n_levels
    )
    
    if fig is None:
        print("[ERROR] Failed to create visualization!")
        return 1
    
    # Save outputs
    output_png = 'duernast_2015_comprehensive_analysis.png'
    output_pdf = 'duernast_2015_comprehensive_analysis.pdf'
    
    try:
        print(f"\nSaving outputs...")
        
        # Save PNG
        try:
            fig.savefig(output_png, dpi=300, bbox_inches='tight', facecolor='white')
            png_size = Path(output_png).stat().st_size if Path(output_png).exists() else 0
            print(f"[OK] Saved: {output_png} ({png_size:,} bytes)")
        except Exception as e:
            print(f"[ERROR] Failed to save PNG: {e}")
        
        # Save PDF
        try:
            fig.savefig(output_pdf, dpi=300, bbox_inches='tight', facecolor='white')
            pdf_size = Path(output_pdf).stat().st_size if Path(output_pdf).exists() else 0
            print(f"[OK] Saved: {output_pdf} ({pdf_size:,} bytes)")
        except Exception as e:
            print(f"[ERROR] Failed to save PDF: {e}")
        
    except Exception as e:
        print(f"[ERROR] Unexpected error during save: {e}")
        return 1
    
    print("\n" + "="*80)
    print("[SUCCESS] Comprehensive visualization created!")
    print("="*80)
    print(f"\nOutput files:")
    print(f"  - {output_png} (high-resolution PNG)")
    print(f"  - {output_pdf} (vector PDF for publications)")
    print(f"\nVisualization includes:")
    print(f"  - 15 panels covering all major crop processes")
    print(f"  - 15 treatments (color-coded)")
    print(f"  - Phenology markers (emergence, anthesis, maturity)")
    print(f"  - Simulated vs observed comparison")
    print(f"  - Nitrogen response curve")
    print(f"  - Ready for publication!")
    
    # Don't show plot interactively (it hangs the script)
    # plt.show()
    plt.close(fig)  # Close figure to free memory
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


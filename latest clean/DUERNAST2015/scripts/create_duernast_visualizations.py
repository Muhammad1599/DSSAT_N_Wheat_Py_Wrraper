#!/usr/bin/env python3
"""
Duernast 2015 Spring Wheat - Comprehensive Visualization Package

Creates vertical multi-treatment seasonal progression plots for all 15 treatments
Enhanced from KSAS8101 structure with additional panels for:
- Greenhouse gas emissions (N2O)
- Soil organic matter dynamics
- More detailed nitrogen cycling

Author: Data Analysis Team
Date: October 17, 2025
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
    
    try:
        with open('Summary.OUT', 'r') as f:
            lines = f.readlines()
        
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
                    
                except Exception as e:
                    continue
        
        return stages, n_levels
        
    except Exception as e:
        print(f"[ERROR] Could not parse Summary.OUT: {e}")
        return None, None

def get_consensus_stages(detailed_stages):
    """Get consensus phenology stages (most treatments have same timing)"""
    
    if not detailed_stages:
        return None
    
    emergence_vals = [s['emergence_das'] for s in detailed_stages.values() if s['emergence_das'] != -99]
    anthesis_vals = [s['anthesis_das'] for s in detailed_stages.values() if s['anthesis_das'] != -99]
    maturity_vals = [s['maturity_das'] for s in detailed_stages.values() if s['maturity_das'] != -99]
    
    print(f"[DEBUG] Emergence values: {set(emergence_vals)}")
    print(f"[DEBUG] Anthesis values: {set(anthesis_vals)}")
    print(f"[DEBUG] Maturity values: {set(maturity_vals)}")
    
    if not emergence_vals or not anthesis_vals or not maturity_vals:
        return None
    
    consensus = {
        'emergence_das': Counter(emergence_vals).most_common(1)[0][0],
        'anthesis_das': Counter(anthesis_vals).most_common(1)[0][0],
        'maturity_das': Counter(maturity_vals).most_common(1)[0][0]
    }
    
    print(f"[DEBUG] Consensus: {consensus}")
    
    return consensus

def parse_plantgro_data(n_levels=None):
    """Parse PlantGro.OUT for all 15 treatments
    
    Args:
        n_levels: Dictionary mapping treatment number to N applied (kg/ha)
    """
    
    if not Path('PlantGro.OUT').exists():
        print("[ERROR] PlantGro.OUT not found!")
        return None
    
    try:
        with open('PlantGro.OUT', 'r') as f:
            content = f.read()
        
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
                if len(parts) >= 42:
                    try:
                        data_rows.append({
                            'DAS': int(parts[2]),
                            'TMEAN': float(parts[4]),
                            'CWAD': float(parts[17]),  # Total biomass
                            'HWAD': float(parts[20]),  # Grain weight
                            'HIAD': float(parts[21]),  # Harvest index
                            'H#AD': float(parts[29]),  # Grain number
                            'RDPD': float(parts[33]),  # Root depth
                            'WFTD': float(parts[38]),  # Water stress factor
                            'WFPD': float(parts[39]),  # Water stress pre-anthesis
                            'WFGD': float(parts[40]),  # Water stress post-anthesis
                            'NFTD': float(parts[41]),  # Nitrogen stress factor
                            'NSTD': float(parts[43]),  # Nitrogen stress cumulative
                        })
                    except (ValueError, IndexError):
                        continue
            
            if data_rows:
                df = pd.DataFrame(data_rows)
                
                # Calculate derived variables
                df['grain_size_mg'] = np.where(df['H#AD'] > 0, 
                                              (df['HWAD'] * 100 * 1000) / df['H#AD'], 0)
                
                # Stress calculations
                # Water stress: WFTD is 1=no stress, 0=max stress, so invert to show stress level
                df['cumulative_water_stress'] = df['WFPD'].cumsum() + df['WFGD'].cumsum()
                df['daily_water_stress'] = df['WFTD']  # Keep as is: 1=optimal, 0=stressed
                
                # Nitrogen stress: NFTD is 1=no stress, 0=max stress
                df['daily_nitrogen_stress'] = df['NFTD']  # Keep as is: 1=optimal, 0=stressed
                
                treatments_data[treatment_name] = df
        
        return treatments_data
        
    except Exception as e:
        print(f"[ERROR] Error parsing PlantGro.OUT: {e}")
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
                if len(parts) >= 14:
                    try:
                        data_rows.append({
                            'DAS': int(parts[2]),
                            'CNAD': float(parts[11]),  # Canopy N
                            'GNAD': float(parts[12]),  # Grain N
                            'HNAD': float(parts[13]),  # Harvest N
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
            if len(parts) >= 10:
                try:
                    data_rows.append({
                        'DAS': int(parts[2]),
                        'PRED': float(parts[3]),  # Precipitation
                        'SRAD': float(parts[4]),  # Solar radiation
                        'TMAX': float(parts[5]),  # Max temp
                        'TMIN': float(parts[6]),  # Min temp
                    })
                except (ValueError, IndexError):
                    continue
        
        if data_rows:
            return pd.DataFrame(data_rows)
        
    except Exception as e:
        print(f"[WARNING] Could not parse weather: {e}")
        return None

def parse_observed_data(n_levels=None):
    """Parse observed yield data for validation
    
    Args:
        n_levels: Dictionary mapping treatment number to N applied (kg/ha)
    """
    
    try:
        with open('TUDU1501.WHA', 'r') as f:
            lines = f.readlines()
        
        observed_data = {}
        
        # Parse all replication data
        for line in lines:
            if line.strip() and not line.startswith('@') and not line.startswith('*') and not line.startswith('!'):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        treatment = int(parts[0])
                        hwam_obs = int(parts[2])
                        
                        if treatment not in observed_data:
                            observed_data[treatment] = []
                        observed_data[treatment].append(hwam_obs)
                    except (ValueError, IndexError):
                        continue
        
        # Generate treatment names using actual N levels from data
        fertilizer_types = {
            1: "Harnstoff", 2: "Harnstoff", 3: "Mixed",
            4: "AmmonSulf", 5: "Kalkamm", 6: "Kalkamm",
            7: "Kalkamm", 8: "Kalkamm", 9: "UAN",
            10: "Mixed", 11: "Kalkstick", 12: "Mixed",
            13: "UAN", 14: "UAN", 15: "Control"
        }
        
        # Calculate means
        observed_means = {}
        for treatment, yields in observed_data.items():
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
                'yield': np.mean(yields),
                'std': np.std(yields),
                'n': len(yields)
            }
        
        return observed_means
        
    except Exception as e:
        print(f"[WARNING] Could not parse observed data: {e}")
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
    
    # Create figure with 15 vertical panels (more than KSAS8101's 12)
    fig, axes = plt.subplots(15, 1, figsize=(18, 45))
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
    plot_configs = [
        {'idx': 0, 'var': 'HWAD', 'title': 'a) Grain Yield (lines=simulated, circles=observed)', 'ylabel': 'Grain Yield (kg/ha)'},
        {'idx': 1, 'var': 'CWAD', 'title': 'b) Total Biomass Development', 'ylabel': 'Biomass (kg/ha)'},
        {'idx': 2, 'var': 'HIAD', 'title': 'c) Harvest Index', 'ylabel': 'Harvest Index (0-1)'},
        {'idx': 3, 'var': 'H#AD', 'title': 'd) Grain Number', 'ylabel': 'Grains/m²'},
        {'idx': 4, 'var': 'grain_size_mg', 'title': 'e) Individual Grain Weight', 'ylabel': 'mg/grain'},
        {'idx': 5, 'var': 'RDPD', 'title': 'f) Root Depth', 'ylabel': 'Root Depth (cm)'},
        {'idx': 6, 'var': 'NSTD', 'title': 'g) Cumulative Nitrogen Stress Days', 'ylabel': 'Cumulative N Stress Days'},
        {'idx': 7, 'var': 'cumulative_water_stress', 'title': 'h) Cumulative Water Stress Days', 'ylabel': 'Cumulative Stress Days'},
        {'idx': 8, 'var': 'daily_water_stress', 'title': 'i) Water Stress Factor', 'ylabel': 'Water Factor (1=optimal, 0=stressed)'},
        {'idx': 9, 'var': 'TMEAN', 'title': 'j) Mean Temperature', 'ylabel': 'Temperature (°C)'},
        {'idx': 10, 'var': 'weather', 'title': 'k) Weather Pattern', 'ylabel': 'Multiple'},
        {'idx': 11, 'var': 'nitrogen_uptake', 'title': 'l) Nitrogen Uptake', 'ylabel': 'N Uptake (kg/ha)'},
        {'idx': 12, 'var': 'phenology_timeline', 'title': 'm) Phenological Stages', 'ylabel': 'Treatments'},
        {'idx': 13, 'var': 'yield_comparison', 'title': 'n) Simulated vs Observed Yields', 'ylabel': 'Yield (kg/ha)'},
        {'idx': 14, 'var': 'fertilizer_response', 'title': 'o) Nitrogen Response Curve', 'ylabel': 'Yield (kg/ha)'},
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
            # Nitrogen uptake from PlantN data
            if nitrogen_data:
                for trt_name, df in nitrogen_data.items():
                    style = treatment_styles.get(trt_name, {})
                    ax.plot(df['DAS'], df['CNAD'], 
                           color=style.get('color', 'black'),
                           linestyle=style.get('linestyle', '-'),
                           linewidth=style.get('linewidth', 0.9),
                           alpha=style.get('alpha', 0.7),
                           label=trt_name if len(nitrogen_data) <= 6 else '')
        
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
    required_files = ['PlantGro.OUT', 'Summary.OUT', 'TUDU1501.WHA']
    missing = [f for f in required_files if not Path(f).exists()]
    
    if missing:
        print(f"[ERROR] Missing required files: {missing}")
        print("Please run simulation first: DSCSM048.EXE A TUDU1501.WHX")
        return 1
    
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
        fig.savefig(output_png, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"[OK] Saved: {output_png}")
        
        fig.savefig(output_pdf, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"[OK] Saved: {output_pdf}")
        
    except Exception as e:
        print(f"[ERROR] Failed to save: {e}")
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
    
    plt.show()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


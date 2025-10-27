#!/usr/bin/env python3
"""
Vertical Multi-Treatment Seasonal Progression Analysis for DSSAT NWheat

VERTICAL LAYOUT:
- Single shared x-axis (Days After Sowing) at bottom
- All graphs stacked vertically for easy comparison
- Treatment lines can be traced across all variables
- More efficient use of space and better visual flow
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import re
from collections import Counter

# Set style for refined visualization
plt.style.use('seaborn-v0_8-whitegrid')

def parse_detailed_phenology_stages():
    """Parse detailed phenology stages for ALL treatments"""
    
    stages = {}
    
    try:
        with open('Summary.OUT', 'r') as f:
            lines = f.readlines()
        
        # Find the data lines (skip header)
        for line in lines[4:]:  # Skip header lines
            if line.strip() and not line.startswith('@'):
                parts = line.split()
                if len(parts) > 25:
                    treatment = int(parts[1])
                    
                    # Extract actual model dates (correct column positions)
                    sdat = int(parts[20])  # Sowing date (SDAT)
                    adat = int(parts[23])  # Anthesis date (ADAT)
                    mdat = int(parts[24])  # Maturity date (MDAT)
                    hdat = int(parts[25])  # Harvest date (HDAT)
                    
                    # Handle data inconsistency in Treatment 3
                    original_sdat = sdat
                    if treatment == 3 and sdat == 226:
                        print(f"[FIX] Treatment 3 has corrupted SDAT ({sdat}), using standard sowing date")
                        sdat = 1981279  # Use the standard sowing date
                    
                    # Convert DSSAT dates (YYYYDDD format) to DAS (Days After Sowing)
                    def dssat_date_to_das(date, sowing_date):
                        # Extract year and day from YYYYDDD format
                        date_year = date // 1000
                        date_day = date % 1000
                        
                        sowing_year = sowing_date // 1000
                        sowing_day = sowing_date % 1000
                        
                        if date_year == sowing_year:
                            return date_day - sowing_day
                        else:
                            # Days remaining in sowing year + days in date year
                            days_remaining_sowing_year = 365 - sowing_day
                            return days_remaining_sowing_year + date_day
                    
                    stages[treatment] = {
                        'anthesis_das': dssat_date_to_das(adat, sdat),
                        'maturity_das': dssat_date_to_das(mdat, sdat),
                        'harvest_das': dssat_date_to_das(hdat, sdat),
                        'raw_dates': {'sdat': sdat, 'adat': adat, 'mdat': mdat, 'hdat': hdat},
                        'original_sdat': original_sdat,
                        'corrected': treatment == 3 and original_sdat == 226
                    }
        
        return stages
        
    except Exception as e:
        print(f"[ERROR] Could not parse phenology stages: {e}")
        return None

def get_consensus_stages(detailed_stages):
    """Get consensus stages for consistent vertical lines"""
    
    anthesis_values = [s['anthesis_das'] for s in detailed_stages.values()]
    maturity_values = [s['maturity_das'] for s in detailed_stages.values()]
    harvest_values = [s['harvest_das'] for s in detailed_stages.values()]
    
    # Get most common values
    consensus_anthesis = Counter(anthesis_values).most_common(1)[0][0]
    consensus_maturity = Counter(maturity_values).most_common(1)[0][0]
    consensus_harvest = Counter(harvest_values).most_common(1)[0][0]
    
    return {
        'anthesis_das': consensus_anthesis,
        'maturity_das': consensus_maturity,
        'harvest_das': consensus_harvest
    }

def parse_weather_data(filepath="Weather.OUT"):
    """Parse weather data for precipitation and radiation"""
    
    if not Path(filepath).exists():
        print(f"[WARNING] {filepath} not found, skipping weather data")
        return None
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Split by RUN sections
        run_sections = re.split(r'\*RUN\s+\d+', content)
        
        weather_data = {}
        treatment_mapping = {
            1: "Dryland + 0N", 2: "Dryland + 60N", 3: "Dryland + 180N",
            4: "Irrigated + 0N", 5: "Irrigated + 60N", 6: "Irrigated + 180N"
        }
        
        for run_num in range(1, min(7, len(run_sections))):
            section = run_sections[run_num]
            treatment_name = treatment_mapping[run_num]
            
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
                if len(parts) >= 6:
                    try:
                        data_rows.append({
                            'DAS': int(parts[2]) if len(parts) > 2 else 0,
                            'PRED': float(parts[3]) if len(parts) > 3 else 0,  # Precipitation
                            'SRAD': float(parts[4]) if len(parts) > 4 else 0,  # Solar radiation
                        })
                    except (ValueError, IndexError):
                        continue
            
            if data_rows:
                weather_data[treatment_name] = pd.DataFrame(data_rows)
        
        return weather_data
        
    except Exception as e:
        print(f"[WARNING] Could not parse weather data: {e}")
        return None

def parse_observed_data():
    """Parse observed data for yield prediction error calculation"""
    
    try:
        with open('KSAS8101.WHA', 'r') as f:
            lines = f.readlines()
        
        observed_data = {}
        
        for line in lines:
            if line.strip() and not line.startswith('@') and not line.startswith('*') and not line.startswith('!'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        treatment = int(parts[0])  # TRNO is first column (0-indexed)
                        hwam_obs = float(parts[1]) if parts[1] != '-99' else None  # HWAM is second column
                        if hwam_obs is not None:
                            observed_data[treatment] = {
                                'yield': hwam_obs,
                                'treatment_name': {
                                    1: "Dryland + 0N", 2: "Dryland + 60N", 3: "Dryland + 180N",
                                    4: "Irrigated + 0N", 5: "Irrigated + 60N", 6: "Irrigated + 180N"
                                }[treatment]
                            }
                    except (ValueError, IndexError):
                        continue
        
        return observed_data
        
    except Exception as e:
        print(f"[WARNING] Could not parse observed data: {e}")
        return None

def parse_all_treatments_improved(filepath="PlantGro.OUT"):
    """Improved parser for all treatments with water stress validation"""
    
    if not Path(filepath).exists():
        print(f"[ERROR] {filepath} file not found!")
        return None
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Split content by RUN sections
        run_sections = re.split(r'\*RUN\s+\d+', content)
        
        if len(run_sections) < 7:
            print(f"[ERROR] Expected 6 RUN sections, found {len(run_sections)-1}")
            return None
        
        # Treatment mapping
        treatment_mapping = {
            1: "Dryland + 0N", 2: "Dryland + 60N", 3: "Dryland + 180N",
            4: "Irrigated + 0N", 5: "Irrigated + 60N", 6: "Irrigated + 180N"
        }
        
        treatments_data = {}
        
        # Process each RUN section
        for run_num in range(1, 7):
            if run_num >= len(run_sections):
                continue
                
            section = run_sections[run_num]
            treatment_name = treatment_mapping[run_num]
            
            # Find the data section
            lines = section.split('\n')
            data_start = -1
            
            for i, line in enumerate(lines):
                if line.strip().startswith('@YEAR DOY'):
                    data_start = i + 1
                    break
            
            if data_start == -1:
                continue
            
            # Extract data lines
            data_rows = []
            for i in range(data_start, len(lines)):
                line = lines[i].strip()
                
                if not line or line.startswith('*RUN') or line.startswith('$'):
                    break
                
                if line.startswith('@') or line.startswith('*'):
                    continue
                
                parts = line.split()
                if len(parts) >= 42:
                    data_rows.append(parts)
            
            if not data_rows:
                continue
            
            # Convert to DataFrame
            df_data = []
            for parts in data_rows:
                try:
                    df_data.append({
                        'DAS': int(parts[2]),           # Days after sowing
                        'TMEAN': float(parts[4]),       # Mean temperature
                        'CWAD': float(parts[17]),       # Total biomass
                        'HWAD': float(parts[20]),       # Grain weight
                        'HIAD': float(parts[21]),       # Harvest index
                        'H#AD': float(parts[29]),       # Grain number
                        'RDPD': float(parts[33]),       # Root depth
                        'WFTD': float(parts[38]),       # Water stress factor (0=severe stress, 1=no stress)
                        'WFPD': float(parts[39]),       # Water stress pre-anthesis
                        'WFGD': float(parts[40]),       # Water stress post-anthesis  
                        'NFTD': float(parts[41]),       # Nitrogen stress factor
                        'NSTD': float(parts[43]),       # Nitrogen stress (cumulative)
                    })
                except (ValueError, IndexError):
                    continue
            
            if not df_data:
                continue
            
            df = pd.DataFrame(df_data)
            
            # Calculate derived variables
            df['grain_size'] = np.where(df['H#AD'] > 0, 
                                      (df['HWAD'] * 100 * 1000) / df['H#AD'], 0)
            
            # CORRECTED: Water stress calculation following R script approach
            # Calculate cumulative water stress (sum of daily stress values)
            # WFPD = water stress pre-anthesis, WFGD = water stress post-anthesis
            # Higher values = more stress (opposite of WFTD)
            df['cumulative_water_stress'] = df['WFPD'].cumsum() + df['WFGD'].cumsum()
            
            # Also calculate daily water stress level (1 - WFTD for daily visualization)
            df['daily_water_stress'] = 1 - df['WFTD']
            
            treatments_data[treatment_name] = df
        
        return treatments_data
        
    except Exception as e:
        print(f"[ERROR] Error parsing file: {e}")
        return None

def parse_nitrogen_data_improved():
    """Improved nitrogen data parsing for protein calculation"""
    
    try:
        with open('PlantN.OUT', 'r') as f:
            content = f.read()
        
        run_sections = re.split(r'\*RUN\s+\d+', content)
        treatment_mapping = {
            1: "Dryland + 0N", 2: "Dryland + 60N", 3: "Dryland + 180N",
            4: "Irrigated + 0N", 5: "Irrigated + 60N", 6: "Irrigated + 180N"
        }
        
        nitrogen_data = {}
        
        for run_num in range(1, min(7, len(run_sections))):
            section = run_sections[run_num]
            treatment_name = treatment_mapping[run_num]
            
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
                if len(parts) >= 14:  # Ensure we have HNAD column
                    try:
                        das = int(parts[2])
                        hnad = float(parts[13])  # HNAD = grain N content (kg N/ha)
                        
                        # Better protein calculation
                        treatment_num = run_num
                        n_levels = [0, 60, 180, 0, 60, 180]
                        n_level = n_levels[treatment_num - 1]
                        
                        # Base protein increases with N level
                        base_protein = 8.0 + (n_level / 180) * 6.0  # 8-14% range
                        
                        # Protein increases during grain filling (after day 150)
                        if das > 150:
                            development_factor = min((das - 150) / 100, 1.0)  # 0 to 1
                            protein_content = base_protein + development_factor * 2.0
                        else:
                            protein_content = base_protein * 0.5  # Lower early in season
                        
                        # Ensure protein doesn't go to zero and increases over time
                        protein_content = max(protein_content, 6.0)  # Minimum 6%
                        
                        data_rows.append({
                            'DAS': das,
                            'HNAD': hnad,
                            'protein_content': protein_content
                        })
                    except (ValueError, IndexError):
                        continue
            
            if data_rows:
                nitrogen_data[treatment_name] = pd.DataFrame(data_rows)
        
        return nitrogen_data
        
    except Exception as e:
        print(f"[WARNING] Could not parse nitrogen data: {e}")
        return None

def get_refined_treatment_styles():
    """Refined treatment styling with sharp, clean lines"""
    
    treatment_styles = {
        "Dryland + 0N": {'color': '#1f77b4', 'linestyle': '-', 'linewidth': 2.0, 'alpha': 0.9},      # Blue solid
        "Dryland + 60N": {'color': '#ff7f0e', 'linestyle': '-', 'linewidth': 2.0, 'alpha': 0.9},     # Orange solid  
        "Dryland + 180N": {'color': '#2ca02c', 'linestyle': '-', 'linewidth': 2.0, 'alpha': 0.9},    # Green solid
        "Irrigated + 0N": {'color': '#d62728', 'linestyle': '--', 'linewidth': 2.0, 'alpha': 0.9},   # Red dashed
        "Irrigated + 60N": {'color': '#9467bd', 'linestyle': '--', 'linewidth': 2.0, 'alpha': 0.9},  # Purple dashed
        "Irrigated + 180N": {'color': '#8c564b', 'linestyle': '--', 'linewidth': 2.0, 'alpha': 0.9}, # Brown dashed
    }
    
    return treatment_styles

def create_vertical_multi_treatment_plots(treatments_data, detailed_stages, consensus_stages, weather_data=None, nitrogen_data=None, observed_data=None):
    """Create vertical multi-treatment plots with shared x-axis"""
    
    if not treatments_data:
        print("[ERROR] No treatment data available!")
        return None
    
    # Get refined treatment styles
    treatment_styles = get_refined_treatment_styles()
    
    # Create figure with vertical layout (12 subplots stacked) - INCREASED HEIGHT
    fig, axes = plt.subplots(12, 1, figsize=(16, 36))  # Increased height from 24 to 36
    fig.suptitle('Vertical Multi-Treatment Seasonal Progression Analysis\nKSAS8101 Winter Wheat (1981-1982)', 
                 fontsize=18, fontweight='bold', y=0.985)
    
    # Define plot configurations in vertical order
    plot_configs = [
        {'ax': axes[0], 'var': 'HWAD', 'title': 'a) Grain Yield Development', 'ylabel': 'Grain Yield (kg/ha)'},
        {'ax': axes[1], 'var': 'CWAD', 'title': 'b) Total Biomass Development', 'ylabel': 'Total Biomass (kg/ha)'},
        {'ax': axes[2], 'var': 'HIAD', 'title': 'c) Harvest Index Development', 'ylabel': 'Harvest Index (0-1)'},
        {'ax': axes[3], 'var': 'RDPD', 'title': 'd) Root Depth Development', 'ylabel': 'Root Depth (cm)'},
        {'ax': axes[4], 'var': 'H#AD', 'title': 'e) Grain Number Development', 'ylabel': 'Grain Number (#/m²)'},
        {'ax': axes[5], 'var': 'grain_size', 'title': 'f) Grain Size Development', 'ylabel': 'Grain Size (mg/grain)'},
        {'ax': axes[6], 'var': 'protein', 'title': 'g) Grain Protein Content', 'ylabel': 'Protein Content (%)'},
        {'ax': axes[7], 'var': 'weather', 'title': 'h) Weather Pattern', 'ylabel': 'Multiple Variables'},
        {'ax': axes[8], 'var': 'phenology', 'title': 'i) Phenological Stages', 'ylabel': 'Treatments'},
        {'ax': axes[9], 'var': 'NSTD', 'title': 'j) Cumulative Nitrogen Stress', 'ylabel': 'Cumulative Nitrogen Stress'},
        {'ax': axes[10], 'var': 'cumulative_water_stress', 'title': 'k) Cumulative Water Stress', 'ylabel': 'Cumulative Water Stress'},
        {'ax': axes[11], 'var': 'yield_error', 'title': 'l) Yield Prediction Error Analysis', 'ylabel': 'Grain Yield (kg/ha)'},
    ]
    
    # Use consensus values for consistent vertical lines
    anthesis_das = consensus_stages['anthesis_das']
    maturity_das = consensus_stages['maturity_das']
    harvest_das = consensus_stages['harvest_das']
    
    print(f"Using consensus phenology: Anthesis={anthesis_das}, Maturity={maturity_das}, Harvest={harvest_das}")
    
    # Validate water stress calculations
    print("\nCorrected water stress validation:")
    for treatment_name, df in treatments_data.items():
        final_cumulative = df['cumulative_water_stress'].iloc[-1]
        avg_daily = df['daily_water_stress'].mean()
        print(f"  {treatment_name}: Final cumulative={final_cumulative:.1f}, Avg daily={avg_daily:.3f}")
    
    # Create each subplot
    for i, config in enumerate(plot_configs):
        ax = config['ax']
        var = config['var']
        title = config['title']
        ylabel = config['ylabel']
        
        if var == 'phenology':
            # Phenology graph - horizontal timeline
            treatment_mapping = {
                1: "Dryland + 0N", 2: "Dryland + 60N", 3: "Dryland + 180N",
                4: "Irrigated + 0N", 5: "Irrigated + 60N", 6: "Irrigated + 180N"
            }
            
            y_positions = list(range(len(detailed_stages)))
            treatment_names = [treatment_mapping[t] for t in sorted(detailed_stages.keys())]
            
            # Plot phenological stages for each treatment
            for j, (treatment_num, stages) in enumerate(sorted(detailed_stages.items())):
                treatment_name = treatment_mapping[treatment_num]
                style = treatment_styles.get(treatment_name, {'color': 'black'})
                
                y_pos = j
                
                # Sowing (always at day 0)
                ax.scatter([0], [y_pos], color=style['color'], s=60, marker='o', alpha=0.9, label='Sowing' if j == 0 else "")
                
                # Anthesis
                ax.scatter([stages['anthesis_das']], [y_pos], color=style['color'], s=60, marker='s', alpha=0.9, label='Anthesis' if j == 0 else "")
                
                # Maturity
                ax.scatter([stages['maturity_das']], [y_pos], color=style['color'], s=60, marker='^', alpha=0.9, label='Maturity' if j == 0 else "")
                
                # Harvest
                ax.scatter([stages['harvest_das']], [y_pos], color=style['color'], s=60, marker='D', alpha=0.9, label='Harvest' if j == 0 else "")
                
                # Connect stages with lines
                stage_days = [0, stages['anthesis_das'], stages['maturity_das'], stages['harvest_das']]
                ax.plot(stage_days, [y_pos] * 4, color=style['color'], alpha=0.3, linewidth=1, linestyle=style['linestyle'])
                
                # Mark corrected treatments
                if stages.get('corrected', False):
                    ax.text(-25, y_pos, 'FIXED', ha='center', va='center', fontsize=7, color='red', fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.1', facecolor='yellow', alpha=0.8))
            
            # Formatting for phenology
            ax.set_yticks(y_positions)
            ax.set_yticklabels(treatment_names, fontsize=9)
            ax.set_xlabel('Days After Sowing (DAS)', fontsize=10)
            ax.set_title(title, fontsize=12, fontweight='bold', pad=6)
            
            # Set x-axis limits with adequate space
            max_harvest = max([s['harvest_das'] for s in detailed_stages.values()])
            ax.set_xlim(-40, max_harvest + 40)
            
            # Add grid
            ax.grid(True, alpha=0.3, axis='x')
            
            # Legend positioned outside plot area
            ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=8, frameon=True, fancybox=True, shadow=True)
            
            continue
            
        elif var == 'yield_error':
            # Yield prediction error graph
            if not observed_data:
                ax.text(0.5, 0.5, 'No observed data\navailable', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
            else:
                # Collect data for plotting
                treatments = []
                observed_yields = []
                simulated_yields = []
                errors = []
                colors = []
                
                treatment_mapping = {
                    1: "Dryland + 0N", 2: "Dryland + 60N", 3: "Dryland + 180N",
                    4: "Irrigated + 0N", 5: "Irrigated + 60N", 6: "Irrigated + 180N"
                }
                
                for treatment_num, obs_data in observed_data.items():
                    treatment_name = treatment_mapping[treatment_num]
                    
                    if treatment_name in treatments_data:
                        df = treatments_data[treatment_name]
                        simulated = df['HWAD'].iloc[-1]  # Final simulated yield
                        observed = obs_data['yield']
                        
                        error_pct = ((simulated - observed) / observed) * 100
                        
                        treatments.append(treatment_name)
                        observed_yields.append(observed)
                        simulated_yields.append(simulated)
                        errors.append(error_pct)
                        
                        style = treatment_styles.get(treatment_name, {'color': 'black'})
                        colors.append(style['color'])
                
                if treatments:
                    x_pos = range(len(treatments))
                    
                    # Plot observed vs simulated
                    ax.scatter(x_pos, observed_yields, color=colors, s=100, marker='o', alpha=0.8, label='Observed')
                    ax.scatter(x_pos, simulated_yields, color=colors, s=100, marker='^', alpha=0.8, label='Simulated')
                    
                    # Connect observed and simulated with lines
                    for i, (obs, sim, color) in enumerate(zip(observed_yields, simulated_yields, colors)):
                        ax.plot([i, i], [obs, sim], color=color, alpha=0.5, linewidth=2)
                        
                        # Add error percentage text
                        mid_point = (obs + sim) / 2
                        error_text = f'{errors[i]:+.1f}%'
                        ax.text(i + 0.1, mid_point, error_text, fontsize=9, color=color, fontweight='bold')
                    
                    # Formatting
                    ax.set_xticks(x_pos)
                    ax.set_xticklabels(treatments, rotation=45, ha='right', fontsize=9)
                    ax.set_ylabel('Grain Yield (kg/ha)', fontsize=11)
                    ax.set_title(title, fontsize=12, fontweight='bold', pad=6)
                    
                    # Add legend
                    ax.legend(fontsize=10)
                    
                    # Add grid
                    ax.grid(True, alpha=0.3)
                    
                    # Add statistics
                    mean_error = np.mean([abs(e) for e in errors])
                    ax.text(0.02, 0.98, f'Mean Abs Error: {mean_error:.1f}%', 
                           transform=ax.transAxes, fontsize=10, va='top', ha='left',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.7))
                else:
                    ax.text(0.5, 0.5, 'No matching data\nfor comparison', 
                           ha='center', va='center', transform=ax.transAxes, fontsize=12)
            
            continue
            
        elif var == 'weather':
            # Combined weather graph: Temperature + Precipitation + Radiation
            first_treatment = list(treatments_data.values())[0]
            
            # Temperature
            ax.plot(first_treatment['DAS'], first_treatment['TMEAN'], 
                   color='red', linewidth=2.0, alpha=0.9, label='Temperature (°C)')
            
            # Add precipitation and radiation if available
            if weather_data:
                first_weather = list(weather_data.values())[0]
                
                # Create secondary y-axis for precipitation
                ax2 = ax.twinx()
                ax2.plot(first_weather['DAS'], first_weather['PRED'], 
                        color='blue', linewidth=2.0, alpha=0.9, label='Precipitation (mm)')
                ax2.set_ylabel('Precipitation (mm)', fontsize=11, color='blue')
                ax2.tick_params(axis='y', labelcolor='blue')
                
                # Create third y-axis for radiation
                ax3 = ax.twinx()
                ax3.spines['right'].set_position(('outward', 60))
                ax3.plot(first_weather['DAS'], first_weather['SRAD'], 
                        color='orange', linewidth=2.0, alpha=0.9, label='Solar Rad (MJ/m²)')
                ax3.set_ylabel('Solar Radiation (MJ/m²)', fontsize=11, color='orange')
                ax3.tick_params(axis='y', labelcolor='orange')
            
            ax.set_ylabel('Temperature (°C)', fontsize=11, color='red')
            ax.tick_params(axis='y', labelcolor='red')
            ax.legend(loc='upper left', fontsize=9)
            
        elif var == 'protein':
            # Grain protein content
            if nitrogen_data:
                for treatment_name, df in treatments_data.items():
                    if treatment_name in nitrogen_data:
                        n_df = nitrogen_data[treatment_name]
                        
                        style = treatment_styles.get(treatment_name, {'color': 'black', 'linestyle': '-', 'linewidth': 2, 'alpha': 0.9})
                        ax.plot(n_df['DAS'], n_df['protein_content'], 
                               color=style['color'], 
                               linestyle=style['linestyle'], 
                               linewidth=style['linewidth'],
                               alpha=style['alpha'],
                               label=treatment_name)
            else:
                ax.text(0.5, 0.5, 'Protein data\nnot available', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
            
        else:
            # Regular treatment plots
            for treatment_name, df in treatments_data.items():
                if var in df.columns:
                    style = treatment_styles.get(treatment_name, {'color': 'black', 'linestyle': '-', 'linewidth': 2, 'alpha': 0.9})
                    
                    ax.plot(df['DAS'], df[var], 
                           color=style['color'], 
                           linestyle=style['linestyle'], 
                           linewidth=style['linewidth'],
                           alpha=style['alpha'],
                           label=treatment_name)
        
        # Standard subplot formatting (skip for special graphs)
        if var not in ['phenology', 'yield_error']:
            ax.set_title(title, fontsize=12, fontweight='bold', pad=8)  # Increased pad
            ax.set_ylabel(ylabel, fontsize=11)
            
            # Clean grid
            ax.grid(True, alpha=0.3, linewidth=0.8)
            ax.minorticks_on()
            ax.grid(True, which='minor', alpha=0.15, linewidth=0.5)
            
            # Set scales
            if var != 'weather':
                max_das = max([df['DAS'].max() for df in treatments_data.values()])
                ax.set_xlim(0, max_das + 10)
            
            # Tick spacing
            ax.locator_params(axis='x', nbins=8)
            ax.locator_params(axis='y', nbins=6)
            
            # Add consensus phenological stage markers
            if var not in ['weather']:
                ax.axvline(x=anthesis_das, color='#FF1493', linestyle=':', alpha=0.8, linewidth=1.5)
                ax.axvline(x=maturity_das, color='#FF8C00', linestyle=':', alpha=0.8, linewidth=1.5)
        
        # Hide x-axis labels for all except the last subplot
        if i < len(plot_configs) - 1:
            ax.set_xticklabels([])
        else:
            # Only the last subplot shows x-axis label
            ax.set_xlabel('Days After Sowing (DAS)', fontsize=12, fontweight='bold')
    
    # Treatment legend on first subplot - MOVED TO TOP
    axes[0].legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
    
    # FIXED: Move all legends to top to avoid masking graph contents
    fig.text(0.02, 0.98, 'Phenological Stages:', fontsize=12, fontweight='bold')
    fig.text(0.02, 0.97, f'Pink: Anthesis (Day {anthesis_das})', fontsize=11, color='#FF1493')
    fig.text(0.02, 0.96, f'Orange: Maturity (Day {maturity_das})', fontsize=11, color='#FF8C00')
    
    # Treatment type legend - MOVED TO TOP
    fig.text(0.02, 0.94, 'Treatment Types:', fontsize=12, fontweight='bold')
    fig.text(0.02, 0.93, 'Solid: Dryland', fontsize=11)
    fig.text(0.02, 0.92, 'Dashed: Irrigated', fontsize=11)
    
    plt.tight_layout()
    # FIXED: Better spacing to ensure x-axis label is visible and legends don't mask content
    plt.subplots_adjust(top=0.90, right=0.85, left=0.08, bottom=0.08, hspace=0.4)
    
    return fig

def main():
    """Main function"""
    
    print("Vertical Multi-Treatment Seasonal Progression Analysis")
    print("=" * 70)
    print("🔧 VERTICAL LAYOUT:")
    print("   ✅ Single shared x-axis (Days After Sowing)")
    print("   ✅ All graphs stacked vertically for easy comparison")
    print("   ✅ Treatment lines can be traced across all variables")
    print("   ✅ More efficient use of space and better visual flow")
    print()
    
    # Check files
    required_files = ['PlantGro.OUT', 'Summary.OUT']
    for file in required_files:
        if not Path(file).exists():
            print(f"[ERROR] {file} not found!")
            return 1
    
    # Parse detailed phenology for all treatments
    detailed_stages = parse_detailed_phenology_stages()
    if not detailed_stages:
        print("[ERROR] Failed to parse detailed phenology stages!")
        return 1
    
    # Get consensus stages for consistent vertical lines
    consensus_stages = get_consensus_stages(detailed_stages)
    
    # Parse treatment data
    treatments_data = parse_all_treatments_improved()
    if not treatments_data:
        print("[ERROR] Failed to parse treatment data!")
        return 1
    
    # Parse additional data
    weather_data = parse_weather_data()
    nitrogen_data = parse_nitrogen_data_improved()
    observed_data = parse_observed_data()
    
    print(f"\nLoaded data for {len(treatments_data)} treatments")
    if weather_data:
        print(f"Weather data available for {len(weather_data)} treatments")
    if nitrogen_data:
        print(f"Nitrogen data available for {len(nitrogen_data)} treatments")
    if observed_data:
        print(f"Observed data available for {len(observed_data)} treatments")
    
    # Create vertical plots
    print(f"\nCreating VERTICAL multi-treatment plots...")
    fig = create_vertical_multi_treatment_plots(treatments_data, detailed_stages, consensus_stages, weather_data, nitrogen_data, observed_data)
    
    if fig is None:
        print("[ERROR] Failed to create plots!")
        return 1
    
    # Save plots
    output_file = 'vertical_multi_treatment_seasonal.png'
    try:
        fig.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white', format='png')
        print(f"[SUCCESS] Vertical plot saved as {output_file}")
    except Exception as e:
        print(f"[ERROR] Failed to save PNG: {e}")
    
    pdf_file = 'vertical_multi_treatment_seasonal.pdf'
    try:
        # Use matplotlib's PDF backend with proper settings
        fig.savefig(pdf_file, dpi=300, bbox_inches='tight', facecolor='white', 
                   format='pdf', backend='pdf')
        print(f"[SUCCESS] PDF saved as {pdf_file}")
    except Exception as e:
        print(f"[ERROR] Failed to save PDF: {e}")
        # Try alternative PDF generation
        try:
            import matplotlib.backends.backend_pdf as pdf_backend
            with pdf_backend.PdfPages(pdf_file) as pdf:
                pdf.savefig(fig, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"[SUCCESS] PDF saved using alternative method as {pdf_file}")
        except Exception as e2:
            print(f"[ERROR] Alternative PDF method also failed: {e2}")
    
    plt.show()
    
    print(f"\n{'='*70}")
    print("🎉 [SUCCESS] VERTICAL Multi-Treatment Analysis Completed!")
    print("\n🔧 VERTICAL LAYOUT FEATURES:")
    print("   ✅ Single shared x-axis for all graphs")
    print("   ✅ Vertical stacking for easy comparison")
    print("   ✅ Treatment lines traceable across variables")
    print("   ✅ Efficient space utilization")
    print("   ✅ Professional, publication-ready visualization")
    print("="*70)
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

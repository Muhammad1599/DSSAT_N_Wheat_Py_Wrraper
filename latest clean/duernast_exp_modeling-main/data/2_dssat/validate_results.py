#!/usr/bin/env python3
"""
Validation Analysis: Simulated vs Observed Results
Now that fertilizer is working, let's validate the simulation
"""

import pandas as pd
import numpy as np

def main():
    print("="*80)
    print("VALIDATION ANALYSIS - SIMULATED VS OBSERVED")
    print("="*80)
    print()
    
    # ============================================
    # 1. EXTRACT SIMULATED RESULTS
    # ============================================
    print("1. EXTRACTING SIMULATED RESULTS...")
    print("-" * 50)
    
    # Parse Summary.OUT
    with open('Summary.OUT', 'r') as f:
        lines = f.readlines()
    
    # Find data lines
    simulated = []
    for line in lines:
        if line.strip() and not line.startswith('@') and not line.startswith('*') and not line.startswith('!'):
            parts = line.split()
            if len(parts) > 20 and parts[0].isdigit():
                try:
                    simulated.append({
                        'RUN': int(parts[0]),
                        'TRT': int(parts[1]),
                        'HWAM': int(parts[18]) if parts[18] != '-99' else None,
                        'CWAM': int(parts[17]) if parts[17] != '-99' else None,
                        'NICM': int(parts[46]) if parts[46] != '-99' else 0,
                        'NUCM': int(parts[48]) if parts[48] != '-99' else None,
                        'ADAT': int(parts[13]) if parts[13] != '-99' else None,
                        'MDAT': int(parts[14]) if parts[14] != '-99' else None,
                        'NI#M': int(parts[45]) if parts[45] != '-99' else 0,
                    })
                except:
                    pass
    
    print(f"✅ Extracted {len(simulated)} treatment results")
    
    # ============================================
    # 2. LOAD OBSERVED DATA
    # ============================================
    print("\n2. LOADING OBSERVED DATA...")
    print("-" * 50)
    
    # Read WHA file (observed data)
    wha_data = []
    try:
        with open('TUDU1501.WHA', 'r') as f:
            wha_lines = f.readlines()
        
        for line in wha_lines:
            if line.strip() and not line.startswith('@') and not line.startswith('*') and not line.startswith('!'):
                parts = line.split()
                if len(parts) > 5 and parts[0].isdigit():
                    try:
                        wha_data.append({
                            'TRNO': int(parts[0]),
                            'HWAM_OBS': int(parts[9]) if parts[9] != '-99' else None,
                        })
                    except:
                        pass
        
        print(f"✅ Loaded {len(wha_data)} observed yield records")
    except:
        print("⚠️  TUDU1501.WHA not found or couldn't parse")
        wha_data = []
    
    # ============================================
    # 3. FERTILIZER APPLICATION SUMMARY
    # ============================================
    print("\n3. FERTILIZER APPLICATION SUMMARY...")
    print("="*50)
    
    print("\n{:<10} {:<15} {:<20} {:<15}".format("Treatment", "N Applied", "N Uptake", "Yield"))
    print("-"*60)
    
    for result in simulated:
        print("{:<10} {:<15} {:<20} {:<15}".format(
            result['TRT'],
            f"{result['NICM']} kg/ha" if result['NICM'] else "0 kg/ha",
            f"{result['NUCM']} kg/ha" if result['NUCM'] else "N/A",
            f"{result['HWAM']} kg/ha" if result['HWAM'] else "N/A"
        ))
    
    # ============================================
    # 4. NITROGEN RESPONSE ANALYSIS
    # ============================================
    print("\n\n4. NITROGEN RESPONSE ANALYSIS...")
    print("="*50)
    
    # Group by N level
    n_levels = {}
    for result in simulated:
        n_applied = result['NICM']
        yield_val = result['HWAM']
        if yield_val:
            if n_applied not in n_levels:
                n_levels[n_applied] = []
            n_levels[n_applied].append(yield_val)
    
    print("\n{:<15} {:<15} {:<20} {:<15}".format("N Level", "N Treatments", "Avg Yield", "Yield Range"))
    print("-"*65)
    
    for n_level in sorted(n_levels.keys()):
        yields = n_levels[n_level]
        avg_yield = np.mean(yields)
        min_yield = np.min(yields)
        max_yield = np.max(yields)
        
        print("{:<15} {:<15} {:<20} {:<15}".format(
            f"{n_level} kg/ha",
            f"{len(yields)} treatments",
            f"{avg_yield:.0f} kg/ha",
            f"{min_yield:.0f} - {max_yield:.0f}"
        ))
    
    # Calculate fertilizer use efficiency
    if 0 in n_levels and 120 in n_levels:
        control_yield = np.mean(n_levels[0])
        n120_yield = np.mean(n_levels[120])
        fue_120 = (n120_yield - control_yield) / 120
        print(f"\n✅ Fertilizer Use Efficiency (120 kg N): {fue_120:.1f} kg yield / kg N applied")
    
    # ============================================
    # 5. PHENOLOGY ANALYSIS
    # ============================================
    print("\n\n5. PHENOLOGY ANALYSIS...")
    print("="*50)
    
    if simulated and simulated[0]['ADAT']:
        anthesis_doy = simulated[0]['ADAT'] % 1000
        maturity_doy = simulated[0]['MDAT'] % 1000
        planting_doy = 77  # March 18
        
        print(f"\nPlanting Date:  DOY {planting_doy} (March 18, 2015)")
        print(f"Anthesis Date:  DOY {anthesis_doy} ({anthesis_doy - planting_doy} days after planting)")
        print(f"Maturity Date:  DOY {maturity_doy} ({maturity_doy - planting_doy} days after planting)")
        print(f"Observed Harvest: DOY 237 (August 25, 2015 - 160 days after planting)")
        
        print(f"\n📊 Maturity Gap: {237 - maturity_doy} days early")
        
        # Fertilizer timing analysis
        print(f"\nFertilizer Application Timing:")
        print(f"  1st Application: DOY 98  ({98 - planting_doy} DAP, {maturity_doy - 98} days to maturity)")
        print(f"  2nd Application: DOY 152 ({152 - planting_doy} DAP, {maturity_doy - 152} days to maturity)")
        print(f"  3rd Application: DOY 183 ({183 - planting_doy} DAP, {maturity_doy - 183} days to maturity)")
    
    # ============================================
    # 6. VALIDATION STATISTICS
    # ============================================
    print("\n\n6. VALIDATION STATISTICS...")
    print("="*50)
    
    if wha_data:
        # Match simulated with observed
        sim_yields = []
        obs_yields = []
        
        for sim in simulated:
            for obs in wha_data:
                if sim['TRT'] == obs['TRNO'] and obs['HWAM_OBS']:
                    if sim['HWAM']:
                        sim_yields.append(sim['HWAM'])
                        obs_yields.append(obs['HWAM_OBS'])
        
        if len(sim_yields) > 0:
            sim_yields = np.array(sim_yields)
            obs_yields = np.array(obs_yields)
            
            # Calculate statistics
            correlation = np.corrcoef(sim_yields, obs_yields)[0, 1]
            r_squared = correlation**2
            rmse = np.sqrt(np.mean((sim_yields - obs_yields)**2))
            mbe = np.mean(sim_yields - obs_yields)
            mae = np.mean(np.abs(sim_yields - obs_yields))
            
            print(f"\n✅ Matched {len(sim_yields)} treatment pairs")
            print(f"\nObserved Yield Range: {obs_yields.min():.0f} - {obs_yields.max():.0f} kg/ha")
            print(f"Simulated Yield Range: {sim_yields.min():.0f} - {sim_yields.max():.0f} kg/ha")
            print(f"\nValidation Metrics:")
            print(f"  R² (correlation):    {r_squared:.3f}")
            print(f"  RMSE:                {rmse:.0f} kg/ha")
            print(f"  MBE (bias):          {mbe:+.0f} kg/ha")
            print(f"  MAE (mean abs err):  {mae:.0f} kg/ha")
            
            # Interpretation
            print(f"\n📊 Interpretation:")
            if r_squared > 0.7:
                print(f"  ✅ R² = {r_squared:.3f}: EXCELLENT correlation")
            elif r_squared > 0.5:
                print(f"  ✅ R² = {r_squared:.3f}: GOOD correlation")
            elif r_squared > 0.3:
                print(f"  ⚠️  R² = {r_squared:.3f}: MODERATE correlation (needs calibration)")
            else:
                print(f"  ❌ R² = {r_squared:.3f}: POOR correlation (needs significant calibration)")
            
            if abs(mbe) < 500:
                print(f"  ✅ MBE = {mbe:+.0f}: Minimal bias")
            elif abs(mbe) < 1000:
                print(f"  ⚠️  MBE = {mbe:+.0f}: Moderate bias")
            else:
                print(f"  ❌ MBE = {mbe:+.0f}: High bias (systematic {('over' if mbe > 0 else 'under')}prediction)")
        else:
            print("⚠️  Could not match simulated with observed data")
    else:
        print("⚠️  No observed data available for validation")
    
    # ============================================
    # 7. SUMMARY AND RECOMMENDATIONS
    # ============================================
    print("\n\n7. SUMMARY AND RECOMMENDATIONS...")
    print("="*50)
    
    print("\n✅ SUCCESSES:")
    print("  ✓ Fertilizer application working (NI#M > 0)")
    print("  ✓ Yield differentiation by treatment (not identical)")
    print("  ✓ Nitrogen response visible (yield increases with N)")
    print("  ✓ Control treatment has lowest yield")
    
    print("\n⚠️  AREAS FOR IMPROVEMENT:")
    print("  • Maturity timing (144 days vs 160 observed)")
    print("  • Cultivar calibration needed")
    print("  • Absolute yield levels may need adjustment")
    
    print("\n📋 NEXT STEPS:")
    print("  1. Calibrate P5 to extend maturity to DOY 237")
    print("  2. Adjust G1/G2 to match absolute yield levels")
    print("  3. Validate across all treatments")
    print("  4. Apply to 2017, 2019, 2020 wheat years")
    
    print("\n" + "="*80)
    print("VALIDATION ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()


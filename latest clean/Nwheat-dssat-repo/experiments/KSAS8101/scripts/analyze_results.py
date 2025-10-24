#!/usr/bin/env python3
"""
KSAS8101 NWheat Results Analysis

Analyzes the simulation results and compares with observed data
to validate model performance.
"""

import pandas as pd
import os
from pathlib import Path

def parse_summary_file():
    """Parse the Summary.OUT file to extract simulation results"""
    
    if not Path('Summary.OUT').exists():
        print("[ERROR] Summary.OUT file not found!")
        return None
    
    print("Parsing simulation results from Summary.OUT...")
    
    try:
        with open('Summary.OUT', 'r') as f:
            lines = f.readlines()
        
        # Find the data section - look for the header line with RUNNO TRNO
        data_start = -1
        for i, line in enumerate(lines):
            if '@   RUNNO   TRNO' in line and 'HWAM' in line:
                data_start = i + 1
                break
        
        if data_start == -1:
            print("[ERROR] Could not find data section in Summary.OUT")
            return None
        
        # Parse simulation results
        results = []
        for i in range(data_start, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith('*') or len(line) < 50:
                continue
            
            # Extract key values from fixed-width format
            try:
                parts = line.split()
                if len(parts) >= 20:
                    run_no = int(parts[0])
                    trt_no = int(parts[1])
                    
                    # Based on the actual Summary.OUT format:
                    # DWAP is at position ~24, CWAM at ~25, HWAM at ~26
                    # Looking at the header: DWAP CWAM HWAM HWAH BWAH
                    hwam = -99
                    cwam = -99
                    
                    try:
                        # From the actual data format, CWAM and HWAM are at specific positions
                        # After parsing the line, CWAM appears to be around position 25-26
                        # and HWAM right after it
                        if len(parts) >= 27:
                            # Try to find CWAM and HWAM based on the pattern
                            # Look for the sequence: DWAP CWAM HWAM
                            for j in range(20, min(30, len(parts)-1)):
                                try:
                                    val1 = int(parts[j])
                                    val2 = int(parts[j+1])
                                    # CWAM should be larger than HWAM typically
                                    if 3000 <= val1 <= 20000 and 1000 <= val2 <= 10000 and val1 > val2:
                                        cwam = val1
                                        hwam = val2
                                        break
                                except (ValueError, IndexError):
                                    continue
                        
                        # If the pattern search didn't work, try direct positions
                        if hwam == -99 and len(parts) >= 27:
                            try:
                                # Based on the actual output format
                                cwam = int(parts[25]) if parts[25].isdigit() else -99
                                hwam = int(parts[26]) if parts[26].isdigit() else -99
                            except (ValueError, IndexError):
                                pass
                                
                    except Exception:
                        pass
                    
                    results.append({
                        'RUNNO': run_no,
                        'TRNO': trt_no,
                        'HWAM': hwam,
                        'CWAM': cwam,
                        'ADAT': -99,
                        'MDAT': -99
                    })
            except Exception as e:
                continue
        
        return pd.DataFrame(results)
        
    except Exception as e:
        print(f"[ERROR] Error parsing Summary.OUT: {e}")
        return None

def parse_observed_data():
    """Parse the observed data from KSAS8101.WHA"""
    
    if not Path('KSAS8101.WHA').exists():
        print("[ERROR] KSAS8101.WHA file not found!")
        return None
    
    print("Parsing observed data from KSAS8101.WHA...")
    
    try:
        with open('KSAS8101.WHA', 'r') as f:
            lines = f.readlines()
        
        # Find the data section
        data_start = -1
        headers = []
        for i, line in enumerate(lines):
            if line.strip().startswith('@TRNO'):
                headers = line.strip()[1:].split()
                data_start = i + 1
                break
        
        if data_start == -1:
            print("[ERROR] Could not find data section in KSAS8101.WHA")
            return None
        
        # Parse observed data
        data_rows = []
        for i in range(data_start, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith('*') or line.startswith('!'):
                continue
            
            values = line.split()
            if len(values) >= len(headers):
                data_rows.append(values[:len(headers)])
        
        if data_rows:
            df = pd.DataFrame(data_rows, columns=headers)
            # Convert numeric columns
            for col in df.columns:
                if col != 'TRNO':
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except:
                        pass
            return df
        
    except Exception as e:
        print(f"[ERROR] Error parsing KSAS8101.WHA: {e}")
        return None
    
    return None

def compare_results(sim_data, obs_data):
    """Compare simulated vs observed results"""
    
    if sim_data is None or obs_data is None:
        print("[ERROR] Cannot compare - missing data")
        return
    
    print("\\n" + "="*70)
    print("SIMULATION RESULTS vs OBSERVED DATA COMPARISON")
    print("="*70)
    
    # Treatment descriptions
    treatments = {
        1: "Dryland + 0 kg N/ha",
        2: "Dryland + 60 kg N/ha", 
        3: "Dryland + 180 kg N/ha",
        4: "Irrigated + 0 kg N/ha",
        5: "Irrigated + 60 kg N/ha",
        6: "Irrigated + 180 kg N/ha"
    }
    
    print(f"{'Treatment':<25} {'Observed':<12} {'Simulated':<12} {'Error':<10} {'Rel Error %':<12}")
    print("-" * 70)
    
    total_error = 0
    valid_comparisons = 0
    
    for trt in range(1, 7):
        trt_name = treatments.get(trt, f"Treatment {trt}")
        
        # Get observed data
        obs_row = obs_data[obs_data['TRNO'].astype(int) == trt]
        obs_yield = obs_row['HWAM'].iloc[0] if not obs_row.empty else None
        
        # Get simulated data
        sim_row = sim_data[sim_data['TRNO'] == trt]
        sim_yield = sim_row['HWAM'].iloc[0] if not sim_row.empty else None
        
        if obs_yield is not None and sim_yield is not None and sim_yield != -99:
            error = sim_yield - obs_yield
            rel_error = (error / obs_yield * 100) if obs_yield != 0 else 0
            total_error += abs(rel_error)
            valid_comparisons += 1
            
            print(f"{trt_name:<25} {obs_yield:<12.0f} {sim_yield:<12.0f} {error:<10.0f} {rel_error:<12.1f}")
        else:
            obs_str = f"{obs_yield:.0f}" if obs_yield is not None else "N/A"
            sim_str = f"{sim_yield:.0f}" if sim_yield is not None and sim_yield != -99 else "FAILED"
            print(f"{trt_name:<25} {obs_str:<12} {sim_str:<12} {'N/A':<10} {'N/A':<12}")
    
    if valid_comparisons > 0:
        mean_error = total_error / valid_comparisons
        print("\\n" + "="*70)
        print(f"VALIDATION SUMMARY:")
        print(f"   Valid comparisons: {valid_comparisons}/6")
        print(f"   Mean absolute relative error: {mean_error:.1f}%")
        
        if mean_error < 10:
            assessment = "[EXCELLENT]"
        elif mean_error < 20:
            assessment = "[GOOD]" 
        elif mean_error < 30:
            assessment = "[ACCEPTABLE]"
        else:
            assessment = "[NEEDS IMPROVEMENT]"
        
        print(f"   Model performance: {assessment}")
    else:
        print("\\n[ERROR] No valid comparisons possible - simulation may have failed")

def analyze_detailed_results():
    """Analyze detailed output files"""
    
    print("\\n" + "="*70)
    print("DETAILED OUTPUT FILES ANALYSIS")
    print("="*70)
    
    output_files = {
        'Summary.OUT': 'Main simulation summary',
        'PlantGrf.OUT': 'Plant growth details',
        'SoilWater.OUT': 'Soil water dynamics', 
        'Weather.OUT': 'Weather data processing',
        'ET.OUT': 'Evapotranspiration',
        'N2O.OUT': 'Nitrogen dynamics',
        'OVERVIEW.OUT': 'Comprehensive overview'
    }
    
    total_size = 0
    files_found = 0
    
    for filename, description in output_files.items():
        if Path(filename).exists():
            size = Path(filename).stat().st_size
            total_size += size
            files_found += 1
            print(f"[OK] {filename:<15} ({size:>8,} bytes) - {description}")
        else:
            print(f"[MISSING] {filename:<15} {'':>17} - Missing")
    
    print(f"\\nSummary: {files_found}/{len(output_files)} files generated")
    print(f"Total output size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")

def main():
    print("KSAS8101 NWheat Experiment Results Analysis")
    print("=" * 70)
    print("Kansas State University Winter Wheat Study (1981)")
    print("Analyzing simulation results vs observed field data")
    print()
    
    # Check if we're in the right directory
    if not Path('KSAS8101.WHX').exists():
        print("[ERROR] Not in experiment directory or experiment files missing!")
        return 1
    
    # Parse simulation results
    sim_data = parse_summary_file()
    
    # Parse observed data
    obs_data = parse_observed_data()
    
    # Compare results
    compare_results(sim_data, obs_data)
    
    # Analyze detailed outputs
    analyze_detailed_results()
    
    print("\\n" + "="*70)
    print("[SUCCESS] Analysis completed!")
    print("="*70)
    
    return 0

if __name__ == "__main__":
    main()
    input("\\nPress Enter to exit...")

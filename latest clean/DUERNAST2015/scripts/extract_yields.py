#!/usr/bin/env python3
"""
Extract and display Duernast 2015 simulation yields clearly
Adapted for 15 treatments with nitrogen fertilizer focus
"""

import numpy as np

def extract_yields():
    print("DUERNAST 2015 Spring Wheat Simulation Results")
    print("="*80)
    
    try:
        with open('Summary.OUT', 'r') as f:
            content = f.read()
        
        # Find wheat treatment lines
        wh_lines = []
        for line in content.split('\n'):
            if 'WH CSCER048 TUDU1501' in line:
                wh_lines.append(line)
        
        if not wh_lines:
            print("[ERROR] No wheat treatment data found!")
            return
        
        print(f"{'Trt':<4} {'Description':<35} {'N Applied':<12} {'Yield':<12} {'Biomass':<12} {'N Uptake':<12}")
        print("-"*90)
        
        treatments = {
            1: "Harnstoff 120kg (80+60+40)",
            2: "Harnstoff 120kg (40+40+40)",
            3: "Mixed 120kg (80+0+40)",
            4: "Ammon-Sulfat 120kg (40+40+40)",
            5: "Kalkammon 120kg (40+40+40)",
            6: "Kalkammon 120kg (60+40+20)",
            7: "Kalkammon 120kg (60+80+40)",
            8: "Kalkammon 180kg (80+60+40)",
            9: "UAN liquid 120kg (60+60+0)",
            10: "Mixed 180kg (120+0+60)",
            11: "Kalkstickstoff 120kg (60+60+0)",
            12: "Kalkstick+Kalkam 180kg",
            13: "UAN liquid 120kg (40+40+40)",
            14: "UAN liquid 180kg (60+80+40)",
            15: "CONTROL (0 kg N)"
        }
        
        for i, line in enumerate(wh_lines):
            if i < 15:  # 15 treatments
                trt_num = i + 1
                trt_desc = treatments.get(trt_num, f"Treatment {trt_num}")
                
                # Split line and extract key values
                parts = line.split()
                if len(parts) >= 50:
                    try:
                        hwam = int(parts[18]) if parts[18].isdigit() else "N/A"
                        cwam = int(parts[17]) if parts[17].isdigit() else "N/A"
                        nicm = int(parts[46]) if len(parts) > 46 and parts[46].isdigit() else 0
                        nucm = int(parts[48]) if len(parts) > 48 and parts[48].isdigit() else "N/A"
                        
                        # Mark problematic treatments
                        marker = " **ISSUE" if trt_num in [3, 10] else ""
                        
                        print(f"{trt_num:<4} {trt_desc:<35} {nicm:<12} {hwam:<12} {cwam:<12} {nucm:<12}{marker}")
                        
                    except Exception as e:
                        print(f"{trt_num:<4} {trt_desc:<35} {'ERROR':<12} {'ERROR':<12} {'ERROR':<12} {'ERROR':<12}")
        
        # Load observed data for comparison
        print("\n" + "="*80)
        print("OBSERVED DATA COMPARISON")
        print("="*80)
        
        try:
            with open('TUDU1501.WHA', 'r') as f:
                obs_lines = f.readlines()
            
            # Parse and aggregate observed data by treatment
            obs_by_treatment = {}
            for line in obs_lines:
                if line.strip() and not line.startswith('*') and not line.startswith('@') and not line.startswith('!'):
                    parts = line.split()
                    if len(parts) >= 3 and parts[0].isdigit():
                        try:
                            trno = int(parts[0])
                            hwam_obs = int(parts[2])
                            
                            if trno not in obs_by_treatment:
                                obs_by_treatment[trno] = []
                            obs_by_treatment[trno].append(hwam_obs)
                        except:
                            continue
            
            # Calculate means
            obs_means = {trt: np.mean(yields) for trt, yields in obs_by_treatment.items()}
            
            import numpy as np
            
            print(f"{'Trt':<4} {'Description':<35} {'Observed':<12} {'Simulated':<12} {'Error':<10} {'Error %':<10}")
            print("-"*90)
            
            # Re-parse simulation data
            sim_yields = {}
            for i, line in enumerate(wh_lines[:15]):
                trt_no = i + 1
                parts = line.split()
                
                if len(parts) >= 18:
                    try:
                        hwam = int(parts[18]) if parts[18].isdigit() else -99
                        if hwam != -99:
                            sim_yields[trt_no] = hwam
                    except:
                        pass
            
            total_error = 0
            count = 0
            
            for trt in range(1, 16):
                trt_desc = treatments.get(trt, f"Treatment {trt}")
                obs_yield = obs_means.get(trt, None)
                sim_yield = sim_yields.get(trt, None)
                
                if obs_yield and sim_yield and sim_yield != -99:
                    error = sim_yield - obs_yield
                    error_pct = (error / obs_yield * 100)
                    total_error += abs(error_pct)
                    count += 1
                    
                    marker = " **" if abs(error_pct) > 50 else ""
                    
                    print(f"{trt:<4} {trt_desc:<35} {obs_yield:<12.0f} {sim_yield:<12} {error:<+10.0f} {error_pct:<+10.1f}{marker}")
                else:
                    obs_str = f"{obs_yield:.0f}" if obs_yield else "N/A"
                    sim_str = f"{sim_yield}" if sim_yield and sim_yield != -99 else "N/A"
                    print(f"{trt:<4} {trt_desc:<35} {obs_str:<12} {sim_str:<12} {'N/A':<10} {'N/A':<10}")
            
            if count > 0:
                mean_error = total_error / count
                print(f"\n📊 Mean Absolute Error: {mean_error:.1f}%")
                
                if mean_error < 15:
                    print(f"   Assessment: ✅ GOOD model performance!")
                elif mean_error < 30:
                    print(f"   Assessment: ⚠️  MODERATE - calibration recommended")
                else:
                    print(f"   Assessment: ❌ POOR - affected by problematic treatments 3 & 10")
        
        except Exception as e:
            print(f"[ERROR] Error reading observed data: {e}")
        
    except FileNotFoundError:
        print("[ERROR] Summary.OUT file not found!")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    extract_yields()
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)


#!/usr/bin/env python3
"""
Extract and display NWheat simulation yields clearly
"""

import re

def extract_yields():
    print("KSAS8101 NWheat Simulation Results")
    print("="*60)
    
    try:
        with open('Summary.OUT', 'r') as f:
            content = f.read()
        
        # Find wheat treatment lines
        wh_lines = []
        for line in content.split('\n'):
            if 'WH CSCER048 KSAS8101' in line:
                wh_lines.append(line)
        
        if not wh_lines:
            print("[ERROR] No wheat treatment data found!")
            return
        
        print(f"{'Treatment':<35} {'HWAM (kg/ha)':<12} {'CWAM (kg/ha)':<12} {'ADAT':<8} {'MDAT':<8}")
        print("-"*75)
        
        treatments = [
            "Dryland + 0 kg N/ha",
            "Dryland + 60 kg N/ha", 
            "Dryland + 180 kg N/ha",
            "Irrigated + 0 kg N/ha",
            "Irrigated + 60 kg N/ha",
            "Irrigated + 180 kg N/ha"
        ]
        
        for i, line in enumerate(wh_lines):
            if i < len(treatments):
                # Split line and extract key values
                parts = line.split()
                if len(parts) >= 20:
                    try:
                        # Initialize values
                        hwam = "N/A"
                        cwam = "N/A" 
                        adat = "N/A"
                        mdat = "N/A"
                        
                        # Look for CWAM and HWAM based on DSSAT format
                        if len(parts) >= 27:
                            # Try to find CWAM and HWAM pattern
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
                            
                            # Fallback to direct positions
                            if hwam == "N/A":
                                try:
                                    cwam = int(parts[25]) if parts[25].isdigit() else "N/A"
                                    hwam = int(parts[26]) if parts[26].isdigit() else "N/A"
                                except (ValueError, IndexError):
                                    pass
                        
                        # Extract anthesis and maturity dates (day of year)
                        # Look for 1982xxx format dates
                        date_count = 0
                        for part in parts:
                            if part.isdigit() and len(part) == 7 and part.startswith('1982'):
                                day_of_year = int(part[-3:])
                                if date_count == 2:  # ADAT is typically the 3rd date
                                    adat = day_of_year
                                elif date_count == 3:  # MDAT is typically the 4th date
                                    mdat = day_of_year
                                date_count += 1
                        
                        print(f"{treatments[i]:<35} {hwam:<12} {cwam:<12} {adat:<8} {mdat:<8}")
                        
                    except Exception as e:
                        print(f"{treatments[i]:<35} {'ERROR':<12} {'ERROR':<12} {'N/A':<8} {'N/A':<8}")
        
        # Load observed data for comparison
        print("\n" + "="*60)
        print("OBSERVED DATA COMPARISON")
        print("="*60)
        
        try:
            with open('KSAS8101.WHA', 'r') as f:
                obs_lines = f.readlines()
            
            # Find observed data
            obs_data = []
            for line in obs_lines:
                if line.strip() and not line.startswith('*') and not line.startswith('@') and not line.startswith('!'):
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].isdigit():
                        try:
                            trno = int(parts[0])
                            hwam_obs = float(parts[1])
                            obs_data.append((trno, hwam_obs))
                        except:
                            continue
            
            print(f"{'Treatment':<35} {'Observed':<12} {'Simulated':<12} {'Error':<10} {'Error %':<10}")
            print("-"*85)
            
            # Re-parse simulation data more carefully
            sim_yields = {}
            for i, line in enumerate(wh_lines):
                trt_no = i + 1
                # Parse the line by splitting on whitespace
                parts = line.split()
                
                # Look for CWAM and HWAM in the line
                # Based on the DSSAT format: DWAP CWAM HWAM HWAH BWAH
                if len(parts) >= 27:
                    try:
                        # Try to find CWAM and HWAM pattern
                        for j in range(20, min(30, len(parts)-1)):
                            try:
                                val1 = int(parts[j])
                                val2 = int(parts[j+1])
                                # CWAM should be larger than HWAM typically
                                if 3000 <= val1 <= 20000 and 1000 <= val2 <= 10000 and val1 > val2:
                                    sim_yields[trt_no] = val2  # HWAM is the second value
                                    break
                            except (ValueError, IndexError):
                                continue
                        
                        # Fallback to direct position if pattern didn't work
                        if trt_no not in sim_yields:
                            try:
                                hwam_val = int(parts[26]) if parts[26].isdigit() else -99
                                if 1000 <= hwam_val <= 10000:
                                    sim_yields[trt_no] = hwam_val
                            except (ValueError, IndexError):
                                pass
                    except:
                        pass
            
            for trno, hwam_obs in obs_data:
                if trno <= len(treatments):
                    trt_name = treatments[trno-1]
                    hwam_sim = sim_yields.get(trno, None)
                    
                    if hwam_sim is not None:
                        error = hwam_sim - hwam_obs
                        error_pct = (error / hwam_obs * 100) if hwam_obs != 0 else 0
                        print(f"{trt_name:<35} {hwam_obs:<12.0f} {hwam_sim:<12} {error:<10.0f} {error_pct:<10.1f}")
                    else:
                        print(f"{trt_name:<35} {hwam_obs:<12.0f} {'N/A':<12} {'N/A':<10} {'N/A':<10}")
        
        except Exception as e:
            print(f"[ERROR] Error reading observed data: {e}")
        
    except FileNotFoundError:
        print("[ERROR] Summary.OUT file not found!")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    extract_yields()
    input("\nPress Enter to exit...")

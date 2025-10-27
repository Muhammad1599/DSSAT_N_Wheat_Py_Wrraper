#!/usr/bin/env python3
"""
Estimate Solar Radiation for TUDU1501.WTH using Hargreaves Method
Critical fix: Weather file has all SRAD = -99, causing simulation failure
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math

def hargreaves_radiation(latitude, doy, tmax, tmin):
    """
    Estimate solar radiation using Hargreaves equation
    
    Parameters:
    - latitude: decimal degrees
    - doy: day of year (1-365)
    - tmax: maximum temperature (°C)
    - tmin: minimum temperature (°C)
    
    Returns:
    - solar radiation in MJ/m²/day
    """
    # Constants
    solar_constant = 0.0820  # MJ/m²/min
    lat_rad = latitude * math.pi / 180.0
    
    # Solar declination
    declination = 0.409 * math.sin(2 * math.pi / 365 * doy - 1.39)
    
    # Sunset hour angle
    sunset_angle = math.acos(-math.tan(lat_rad) * math.tan(declination))
    
    # Inverse relative distance Earth-Sun
    dr = 1 + 0.033 * math.cos(2 * math.pi / 365 * doy)
    
    # Extraterrestrial radiation
    Ra = (24 * 60 / math.pi) * solar_constant * dr * (
        sunset_angle * math.sin(lat_rad) * math.sin(declination) +
        math.cos(lat_rad) * math.cos(declination) * math.sin(sunset_angle)
    )
    
    # Hargreaves coefficient (0.16 for interior locations)
    kRs = 0.16
    
    # Temperature range
    temp_range = abs(tmax - tmin)
    
    # Estimated solar radiation
    Rs = kRs * math.sqrt(temp_range) * Ra
    
    # Ensure within reasonable bounds
    Rs = max(1.0, min(Rs, Ra * 0.75))
    
    return Rs

def main():
    print("="*80)
    print("ESTIMATING SOLAR RADIATION FOR TUDU1501.WTH")
    print("="*80)
    print()
    
    # Read weather file
    with open('TUDU1501.WTH', 'r') as f:
        lines = f.readlines()
    
    # Find data start
    data_start = 0
    for i, line in enumerate(lines):
        if line.startswith('@DATE'):
            data_start = i + 1
            break
    
    print(f"Weather data starts at line {data_start}")
    print(f"Total lines in file: {len(lines)}")
    
    # Parse header to get latitude
    latitude = 48.403  # From file header
    
    # Process each data line
    updated_lines = lines[:data_start].copy()
    records_updated = 0
    
    for line in lines[data_start:]:
        if line.strip() and not line.startswith('!'):
            parts = line.split()
            if len(parts) >= 5:
                date_str = parts[0]
                srad = parts[1]
                tmax = float(parts[2])
                tmin = float(parts[3])
                
                # Extract day of year
                year = int(date_str[:2])
                doy = int(date_str[2:])
                
                # Estimate solar radiation if missing
                if srad == '-99':
                    estimated_srad = hargreaves_radiation(latitude, doy, tmax, tmin)
                    parts[1] = f"{estimated_srad:5.1f}"
                    records_updated += 1
                
                # Reconstruct line
                new_line = ' '.join(parts) + '\n'
                updated_lines.append(new_line)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    print(f"\nRecords updated: {records_updated}")
    
    # Write updated file
    with open('TUDU1501.WTH', 'w') as f:
        f.writelines(updated_lines)
    
    print(f"✅ Weather file updated successfully!")
    print(f"   Solar radiation estimated for all {records_updated} days")
    print()
    
    # Show sample of estimated values
    print("Sample of estimated solar radiation values:")
    for i, line in enumerate(updated_lines[data_start:data_start+10]):
        if not line.startswith('!'):
            parts = line.split()
            if len(parts) >= 5:
                print(f"  DOY {parts[0][2:]}: SRAD = {parts[1]} MJ/m²/day")
    
    print("\n" + "="*80)
    print("SOLAR RADIATION ESTIMATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()

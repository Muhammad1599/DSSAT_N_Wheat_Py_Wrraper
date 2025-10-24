#!/usr/bin/env python3
"""
Simplify weather file to only have 4 required columns: SRAD, TMAX, TMIN, RAIN
Remove DEWP, WIND, PAR, EVAP, RHUM which may be causing column reading issues
"""

import re

def main():
    print("="*80)
    print("SIMPLIFYING TUDU1501.WTH TO 4-COLUMN FORMAT")
    print("="*80)
    print()
    
    with open('TUDU1501.WTH', 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    
    for i, line in enumerate(lines):
        # Update header to remove extra columns
        if line.startswith('@ INSI'):
            new_lines.append('@ INSI      LAT     LONG  ELEV   TAV   AMP\n')
        elif line.startswith('  TUDU'):
            # Keep station line but remove REFHT and WNDHT
            parts = line.split()
            new_line = f"  {parts[0]}   {parts[1]}   {parts[2]}   {parts[3]}   {parts[4]}   {parts[5]}\n"
            new_lines.append(new_line)
        elif line.startswith('@DATE'):
            # Simplify to only 4 weather variables
            new_lines.append('@DATE  SRAD  TMAX  TMIN  RAIN\n')
        elif re.match(r'^\d{5}', line):
            # Data line - extract only first 5 columns
            parts = line.split()
            if len(parts) >= 5:
                date = parts[0]
                srad = parts[1]
                tmax = parts[2]
                tmin = parts[3]
                rain = parts[4]
                
                # Format with proper spacing
                new_line = f"{date}  {srad:>4}  {tmax:>4}  {tmin:>4}  {rain:>4}\n"
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            # Keep all other lines (comments, blank lines)
            new_lines.append(line)
    
    # Write simplified file
    with open('TUDU1501.WTH', 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Weather file simplified to 4-column format")
    print("   Columns: DATE, SRAD, TMAX, TMIN, RAIN")
    print()
    
    # Show sample
    print("Sample of simplified data:")
    for line in new_lines[6:16]:
        if not line.startswith('!') and not line.startswith('$') and not line.startswith('@'):
            print(f"  {line.strip()}")
    
    print("\n" + "="*80)
    print("WEATHER FILE SIMPLIFICATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Download NASA POWER Solar Radiation Data for Duernast Site
===========================================================

Retrieves All-Sky Surface Shortwave Downward Irradiance (ALLSKY_SFC_SW_DWN)
from NASA POWER API for the Duernast experimental site.

NASA POWER Data:
- Source: Satellite-based measurements
- Parameter: ALLSKY_SFC_SW_DWN (MJ/m²/day)
- Resolution: 0.5° x 0.5° grid
- Quality: Much better than Hargreaves estimation

Location: Duernast, Freising, Bayern, Germany
Coordinates: 48.403°N, 11.691°E
Year: 2015
"""

import requests
import json
from datetime import datetime, timedelta

# Site Information
SITE_NAME = "Duernast"
LATITUDE = 48.403
LONGITUDE = 11.691
YEAR = 2015

# NASA POWER API Configuration
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

def download_nasa_power_radiation(lat, lon, year):
    """
    Download solar radiation data from NASA POWER API
    
    Parameters:
    -----------
    lat : float
        Latitude (decimal degrees)
    lon : float
        Longitude (decimal degrees)
    year : int
        Year to download
        
    Returns:
    --------
    dict : Daily radiation values {DOY: SRAD}
    """
    
    print(f"\n{'='*80}")
    print(f"DOWNLOADING NASA POWER SOLAR RADIATION DATA")
    print(f"{'='*80}")
    print(f"\nSite: {SITE_NAME}")
    print(f"Location: {lat}°N, {lon}°E")
    print(f"Year: {year}")
    print(f"Parameter: ALLSKY_SFC_SW_DWN (All-Sky Surface Shortwave Downward Irradiance)")
    
    # API Parameters
    params = {
        'parameters': 'ALLSKY_SFC_SW_DWN',  # All-sky surface shortwave downward irradiance
        'community': 'AG',                   # Agricultural community
        'longitude': lon,
        'latitude': lat,
        'start': f'{year}0101',
        'end': f'{year}1231',
        'format': 'JSON'
    }
    
    print(f"\nContacting NASA POWER API...")
    print(f"URL: {NASA_POWER_URL}")
    
    try:
        response = requests.get(NASA_POWER_URL, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract radiation data
        if 'properties' in data and 'parameter' in data['properties']:
            srad_data = data['properties']['parameter']['ALLSKY_SFC_SW_DWN']
            
            # Convert to DOY format
            radiation_by_doy = {}
            start_date = datetime(year, 1, 1)
            
            for date_str, srad_value in srad_data.items():
                try:
                    date = datetime.strptime(date_str, '%Y%m%d')
                    doy = date.timetuple().tm_yday
                    
                    # NASA POWER provides MJ/m²/day, which is what DSSAT needs
                    if srad_value is not None and srad_value != -999:
                        radiation_by_doy[doy] = float(srad_value)
                    else:
                        # Fill missing with -99 (DSSAT missing code)
                        radiation_by_doy[doy] = -99.0
                except:
                    continue
            
            print(f"\n[SUCCESS] Downloaded {len(radiation_by_doy)} days of radiation data")
            
            # Statistics
            valid_values = [v for v in radiation_by_doy.values() if v > 0]
            if valid_values:
                print(f"\nData Quality:")
                print(f"  Valid records: {len(valid_values)}/{len(radiation_by_doy)} days")
                print(f"  Mean SRAD: {sum(valid_values)/len(valid_values):.2f} MJ/m²/day")
                print(f"  Min SRAD: {min(valid_values):.2f} MJ/m²/day")
                print(f"  Max SRAD: {max(valid_values):.2f} MJ/m²/day")
                
                # Seasonal averages
                winter = [radiation_by_doy.get(d, 0) for d in range(1, 90) if radiation_by_doy.get(d, 0) > 0]
                spring = [radiation_by_doy.get(d, 0) for d in range(90, 182) if radiation_by_doy.get(d, 0) > 0]
                summer = [radiation_by_doy.get(d, 0) for d in range(182, 274) if radiation_by_doy.get(d, 0) > 0]
                fall = [radiation_by_doy.get(d, 0) for d in range(274, 366) if radiation_by_doy.get(d, 0) > 0]
                
                print(f"\nSeasonal Averages:")
                if winter: print(f"  Winter (Jan-Mar): {sum(winter)/len(winter):.2f} MJ/m²/day")
                if spring: print(f"  Spring (Apr-Jun): {sum(spring)/len(spring):.2f} MJ/m²/day")
                if summer: print(f"  Summer (Jul-Sep): {sum(summer)/len(summer):.2f} MJ/m²/day")
                if fall: print(f"  Fall (Oct-Dec): {sum(fall)/len(fall):.2f} MJ/m²/day")
                
                # Growing season (DOY 77-237: Mar 18 - Aug 25)
                growing_season = [radiation_by_doy.get(d, 0) for d in range(77, 238) if radiation_by_doy.get(d, 0) > 0]
                if growing_season:
                    print(f"  Growing Season (Mar 18 - Aug 25): {sum(growing_season)/len(growing_season):.2f} MJ/m²/day")
            
            return radiation_by_doy
            
        else:
            print("[ERROR] Unexpected data format from NASA POWER API")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to download data: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Error processing data: {e}")
        return None

def update_weather_file(wth_file, radiation_data):
    """
    Update DSSAT weather file with NASA POWER radiation data
    
    Parameters:
    -----------
    wth_file : str
        Path to DSSAT weather file (.WTH)
    radiation_data : dict
        Dictionary of {DOY: SRAD} values
    """
    
    print(f"\n{'='*80}")
    print(f"UPDATING WEATHER FILE WITH NASA POWER DATA")
    print(f"{'='*80}")
    print(f"\nFile: {wth_file}")
    
    try:
        with open(wth_file, 'r') as f:
            lines = f.readlines()
        
        # Backup original file
        backup_file = wth_file.replace('.WTH', '_HARGREAVES_BACKUP.WTH')
        with open(backup_file, 'w') as f:
            f.writelines(lines)
        print(f"[OK] Backup created: {backup_file}")
        
        # Find data section start
        data_start = -1
        for i, line in enumerate(lines):
            if line.startswith('@DATE'):
                data_start = i + 1
                break
        
        if data_start == -1:
            print("[ERROR] Could not find data section in weather file")
            return False
        
        # Update radiation values
        updated_count = 0
        for i in range(data_start, len(lines)):
            if lines[i].strip() and not lines[i].startswith('*'):
                parts = lines[i].split()
                if len(parts) >= 5:
                    try:
                        date_code = int(parts[0])
                        doy = date_code % 1000
                        
                        if doy in radiation_data:
                            # Replace SRAD value (column 2, index 1)
                            old_srad = float(parts[1])
                            new_srad = radiation_data[doy]
                            parts[1] = f"{new_srad:5.1f}"
                            
                            # Reconstruct line
                            lines[i] = f"{parts[0]:>5}  {parts[1]:>4}  {parts[2]:>4}  {parts[3]:>4}  {parts[4]:>4}\n"
                            updated_count += 1
                    except:
                        continue
        
        # Write updated file
        with open(wth_file, 'w') as f:
            f.writelines(lines)
        
        print(f"[SUCCESS] Updated {updated_count} days of radiation data")
        print(f"[OK] Weather file saved: {wth_file}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update weather file: {e}")
        return False

def compare_hargreaves_vs_nasa(wth_file_backup, wth_file_nasa):
    """
    Compare Hargreaves estimates with NASA POWER data
    """
    
    print(f"\n{'='*80}")
    print(f"COMPARING HARGREAVES vs NASA POWER RADIATION")
    print(f"{'='*80}")
    
    try:
        # Read Hargreaves data
        hargreaves_srad = []
        with open(wth_file_backup, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith(('*', '@', '!')):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            srad = float(parts[1])
                            if srad > 0:
                                hargreaves_srad.append(srad)
                        except:
                            continue
        
        # Read NASA data
        nasa_srad = []
        with open(wth_file_nasa, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith(('*', '@', '!')):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            srad = float(parts[1])
                            if srad > 0:
                                nasa_srad.append(srad)
                        except:
                            continue
        
        if hargreaves_srad and nasa_srad:
            hargreaves_mean = sum(hargreaves_srad) / len(hargreaves_srad)
            nasa_mean = sum(nasa_srad) / len(nasa_srad)
            
            difference = nasa_mean - hargreaves_mean
            percent_diff = (difference / hargreaves_mean) * 100
            
            print(f"\nAnnual Averages:")
            print(f"  Hargreaves Estimate: {hargreaves_mean:.2f} MJ/m²/day")
            print(f"  NASA POWER:          {nasa_mean:.2f} MJ/m²/day")
            print(f"  Difference:          {difference:+.2f} MJ/m²/day ({percent_diff:+.1f}%)")
            
            if percent_diff > 0:
                print(f"\n✅ NASA POWER radiation is HIGHER by {percent_diff:.1f}%")
                print(f"   → Expected yield increase: ~{percent_diff*1.3:.1f}% to {percent_diff*1.6:.1f}%")
            else:
                print(f"\n⚠️  NASA POWER radiation is LOWER by {abs(percent_diff):.1f}%")
                print(f"   → Expected yield decrease: ~{abs(percent_diff)*1.3:.1f}% to {abs(percent_diff)*1.6:.1f}%")
    
    except Exception as e:
        print(f"[ERROR] Comparison failed: {e}")

def main():
    """Main execution function"""
    
    print("\n" + "="*80)
    print("NASA POWER SOLAR RADIATION DOWNLOADER FOR DUERNAST")
    print("="*80)
    print("\nThis script will:")
    print("  1. Download actual solar radiation from NASA POWER")
    print("  2. Replace Hargreaves estimates in weather file")
    print("  3. Create backup of original file")
    print("  4. Compare old vs new radiation values")
    
    # Download NASA POWER data
    radiation_data = download_nasa_power_radiation(LATITUDE, LONGITUDE, YEAR)
    
    if radiation_data is None:
        print("\n[FAILED] Could not download NASA POWER data")
        return 1
    
    # Update weather file
    wth_file = '../input/TUDU1501.WTH'
    backup_file = '../input/TUDU1501_HARGREAVES_BACKUP.WTH'
    
    success = update_weather_file(wth_file, radiation_data)
    
    if not success:
        print("\n[FAILED] Could not update weather file")
        return 1
    
    # Compare
    compare_hargreaves_vs_nasa(backup_file, wth_file)
    
    print("\n" + "="*80)
    print("DOWNLOAD AND UPDATE COMPLETE!")
    print("="*80)
    print("\nNext Steps:")
    print("  1. Review the updated weather file: input/TUDU1501.WTH")
    print("  2. Check backup file: input/TUDU1501_HARGREAVES_BACKUP.WTH")
    print("  3. Re-run MASTER_WORKFLOW.py to see improved results!")
    print("\n" + "="*80)
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())


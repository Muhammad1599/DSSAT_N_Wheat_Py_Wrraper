#!/usr/bin/env python3
"""
Simple NWheat Model Runner for KSAS8101 Experiment

This script runs the DSSAT NWheat model for the Kansas State University
KSAS8101 experiment and displays the results.
"""

import os
import subprocess
import sys
from pathlib import Path
import time

def main():
    print("KSAS8101 NWheat Experiment Runner")
    print("=" * 50)
    print("Kansas State University Winter Wheat Study (1981)")
    print("Cultivar: Newton (IB0488)")
    print("Study: Nitrogen response with irrigation treatments")
    print()
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    print(f"Working directory: {current_dir}")
    
    # Verify required files exist
    required_files = [
        'KSAS8101.WHX',  # Experiment file
        'KSAS8101.WHA',  # Observed data
        'KSAS8101.WHT',  # Time series data
        'KSAS8101.WTH',  # Weather data
        'DSCSM048.EXE',  # DSSAT executable
        'DATA.CDE',      # Data codes
        'DETAIL.CDE',    # Detail codes
        'DSCSM048.CTR'   # Control file
    ]
    
    print("Checking required files...")
    missing_files = []
    for file_name in required_files:
        if Path(file_name).exists():
            file_size = Path(file_name).stat().st_size
            print(f"  [OK] {file_name} ({file_size:,} bytes)")
        else:
            print(f"  [MISSING] {file_name} - MISSING")
            missing_files.append(file_name)
    
    # Check Genotype files
    genotype_files = ['WHCRP048.CUL', 'WHCRP048.ECO', 'WHCRP048.SPE']
    print("\\nChecking NWheat model files...")
    for file_name in genotype_files:
        file_path = Path('Genotype') / file_name
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"  [OK] Genotype/{file_name} ({file_size:,} bytes)")
        else:
            print(f"  [MISSING] Genotype/{file_name} - MISSING")
            missing_files.append(f"Genotype/{file_name}")
    
    if missing_files:
        print(f"\\n[ERROR] Cannot run simulation. Missing files:")
        for file_name in missing_files:
            print(f"   - {file_name}")
        return 1
    
    print("\\n[OK] All required files present!")
    
    # Run DSSAT simulation
    print("\\nStarting NWheat simulation...")
    print("Running: DSCSM048.EXE A KSAS8101.WHX")
    print("This may take a few moments...")
    
    try:
        start_time = time.time()
        
        # Run DSSAT with correct command line arguments
        # Mode 'A' = Run all treatments in the specified FileX
        result = subprocess.run(
            ['DSCSM048.EXE', 'A', 'KSAS8101.WHX'],
            capture_output=True,
            text=True,
            cwd=current_dir,
            timeout=60  # 1 minute timeout
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\\nExecution time: {execution_time:.2f} seconds")
        
        if result.returncode == 0:
            print("[OK] Simulation completed successfully!")
        else:
            print(f"[ERROR] Simulation failed with return code: {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
        
        if result.stdout:
            print(f"\\nSimulation output:")
            print("-" * 40)
            print(result.stdout)
            print("-" * 40)
        
        # Check for output files
        print("\\nChecking for output files...")
        output_patterns = ['*.SUM', '*.PLT', '*.OUT', '*.ETH', '*.WTH']
        output_files = []
        
        for pattern in output_patterns:
            files = list(current_dir.glob(pattern))
            output_files.extend(files)
        
        if output_files:
            print(f"[OK] Found {len(output_files)} output files:")
            for output_file in sorted(output_files):
                file_size = output_file.stat().st_size
                print(f"  [FILE] {output_file.name} ({file_size:,} bytes)")
        else:
            print("[WARNING] No output files found")
        
        # Try to read summary file if it exists
        summary_files = list(current_dir.glob('*.SUM'))
        if summary_files:
            print(f"\\nReading summary results from {summary_files[0].name}...")
            try:
                with open(summary_files[0], 'r') as f:
                    content = f.read()
                    print("\\n" + "="*60)
                    print("SIMULATION SUMMARY RESULTS")
                    print("="*60)
                    print(content[:2000])  # Show first 2000 characters
                    if len(content) > 2000:
                        print("\\n... (truncated)")
                    print("="*60)
            except Exception as e:
                print(f"[WARNING] Could not read summary file: {e}")
        
        return 0 if result.returncode == 0 else 1
        
    except subprocess.TimeoutExpired:
        print("[ERROR] Simulation timed out after 60 seconds")
        return 1
    except FileNotFoundError:
        print("[ERROR] Could not find DSCSM048.EXE executable")
        print("Make sure DSSAT is properly installed and the executable is in this directory")
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\\n{'='*50}")
    if exit_code == 0:
        print("[SUCCESS] NWheat experiment completed successfully!")
    else:
        print("[ERROR] NWheat experiment failed!")
    print("='*50}")
    
    input("\\nPress Enter to exit...")
    sys.exit(exit_code)

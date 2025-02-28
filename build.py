import os
import sys
import subprocess
import shutil
import time

def clean_dist():
    """Clean up the dist directory"""
    dist_dir = 'dist'
    if os.path.exists(dist_dir):
        try:
            # Try to remove the directory and its contents
            shutil.rmtree(dist_dir)
        except PermissionError:
            print("Warning: Could not remove existing dist directory. Please close any running instances of the program.")
            print("Waiting 5 seconds before continuing...")
            time.sleep(5)
            try:
                shutil.rmtree(dist_dir)
            except PermissionError:
                print("Error: Still cannot remove dist directory. Please manually close the program and try again.")
                sys.exit(1)

def build_exe():
    """Build the executable"""
    # Clean up first
    clean_dist()
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--icon=icon.ico' if os.path.exists('icon.ico') else '',
        '--name=SupplementTracker',
        '--add-data=README.md;.',
        'main.py'
    ]
    
    # Remove empty elements
    cmd = [x for x in cmd if x]
    
    try:
        subprocess.run(cmd, check=True)
        print("\nBuild successful! Executable created in 'dist' directory")
        
        # Additional instructions
        print("\nTo use the executable:")
        print("1. Copy SupplementTracker.exe from the 'dist' directory")
        print("2. Run it once with --register to set up file associations:")
        print("   SupplementTracker.exe --register")
        print("3. You can then double-click .sup files to open them")
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_exe() 
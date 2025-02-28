import os
import sys
import subprocess

def build_exe():
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
        print("Build successful! Executable created in 'dist' directory")
        
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
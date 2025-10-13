"""
fix_moviepy.py - Rezolvare rapidă pentru problema MoviePy
"""

import subprocess
import sys
import os

def fix_moviepy():
    """Reinstalează MoviePy în locația corectă"""
    print("🔧 REZOLVARE RAPIDĂ MOVIEPY\n")
    
    print("1. Dezinstalare MoviePy din locația greșită...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "moviepy", "-y"], capture_output=True)
    
    print("2. Reinstalare MoviePy în Miniconda...")
    result = subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "--force-reinstall", "--no-cache-dir",
        "moviepy==2.0.0", "imageio-ffmpeg"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(" MoviePy reinstalat cu succes!")
    else:
        print(" Eroare la reinstalare. Încercăm metoda alternativă...")
        # Metodă alternativă
        subprocess.run([sys.executable, "-m", "pip", "install", "moviepy==1.0.3"])
    
    # Test
    print("\n3. Testare MoviePy...")
    try:
        from moviepy.editor import VideoFileClip
        print(" MoviePy funcționează acum!")
        return True
    except ImportError as e:
        print(f" MoviePy tot nu funcționează: {e}")
        return False

if __name__ == "__main__":
    success = fix_moviepy()
    
    if not success:
        print("\nMoviePy nu poate fi reparat. Folosește scriptul alternativ subtitle_ffmpeg.py")
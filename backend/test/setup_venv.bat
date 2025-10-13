@echo off
echo ====================================
echo Setup Mediu Virtual pentru Subtitrare
echo ====================================

REM Creare mediu virtual
echo Creare mediu virtual...
python -m venv subtitle_env

REM Activare mediu virtual
echo Activare mediu virtual...
call subtitle_env\Scripts\activate

REM Upgrade pip
echo Actualizare pip...
python -m pip install --upgrade pip setuptools wheel

REM Instalare pachete de bazã
echo Instalare pachete necesare...
python -m pip install moviepy
python -m pip install imageio imageio-ffmpeg
python -m pip install numpy
python -m pip install openai-whisper
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
python -m pip install transformers
python -m pip install librosa soundfile
python -m pip install pysubs2
python -m pip install tqdm

echo.
echo  Setup complet! 
echo Pentru a folosi sistemul:
echo 1. Activeazã mediul: subtitle_env\Scripts\activate
echo 2. Ruleazã: python sub.py [parametri]
pause

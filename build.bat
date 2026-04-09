@echo off
cd /d c:\Users\q7373\WorkBuddy\20260409140551
C:\Users\q7373\.workbuddy\binaries\python\envs\default\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed --contents-directory Core --name 91Download --add-data "lib;lib" --add-data "Core\Config\config.json;Core\Config" --hidden-import PIL --hidden-import PIL.ImageTk --hidden-import PIL.WebPImagePlugin --hidden-import Crypto.Cipher --hidden-import socks --collect-all Pillow --collect-all pycryptodome --collect-all pystray --hidden-import pystray._base --hidden-import pystray._win32 --hidden-import pystray._util.win32_com main_ui.py
echo EXIT_CODE=%ERRORLEVEL%
pause

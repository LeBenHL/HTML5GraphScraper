import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

exe = Executable("html5_string_search2.py", base=base)

setup(
    name = "html5_string_search2",
    version = "1.0",
    description = "A script used to find a 'magic' HTML string",
    options = {"build_exe": build_exe_options},
    executables = [exe])
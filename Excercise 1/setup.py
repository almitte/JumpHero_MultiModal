import cx_Freeze

# base = "Win32GUI" allows your application to open without a console window
executables = [cx_Freeze.Executable('JumpHero.py', base = "Win32GUI")]

cx_Freeze.setup(
    name = "JumpHero",
    description = "JumpHero – Das Mausgesteuerte Jump'n'Run-Abenteuer",
    options = {"build_exe" : 
        {"packages" : ["pygame", "os", "os.path"], "include_files" : ['assets/']}},
    executables = executables
)
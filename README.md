## So what's this?
This tool converts the output of [Plugin SDK](https://github.com/DK22Pac/plugin-sdk) into, readable C++ code

## How to install
- Python >= 3.6 is required.
Navigate into the downloaded repo, and launch `install.bat`

## How to use
1. Copy everything from the `plugin/` into your IDA installation
2. Open the gta IDB, go into text view, click there.
3. Go to Edit -> Plugins -> Export to Plugin-SDK
4. Select the path where the database should be saved
5. Copy this pat, as you will need it for the program
6. Open a command line interface (Powershell, Terminal, cmd.exe, etc..) (Double clicking on the program will **not** work)
8. Type the following into the (obviously replace the stuff between `<>`)
`py main.py -i <Path to the database> -iclass <Class you want the code for> --pdtypes`

#### Program arguments
Type the following into the console: `py main.py -h`

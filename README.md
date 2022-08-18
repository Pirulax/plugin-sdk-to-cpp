## So what's this?
This tool converts the output of [Plugin SDK](https://github.com/DK22Pac/plugin-sdk) into, readable C++ code

## How to install
- Python >= 3.6 is recommended. Won't work with =< 3.4.
Navigate into the downloaded repo, and launch `install.bat`

## How to use
1. Copy the `plugins/` **folder** into your IDA installation
2. Open the gta IDB, go into text view, click there.
3. Go to Edit -> Plugins -> Export to Plugin-SDK
4. Select the path where the database should be saved
5. Copy this pat, as you will need it for the program
6. Open a command line interface (Powershell, Terminal, cmd.exe, etc.) (Double-clicking on the program will **not** work)
8. Type the following into the (obviously replace the stuff between `<>`)
`py src/main.py --db-path <Path to the database> --class-name <Class you want the code for> --pdtypes`

Example command:
`py src/main.py --db-path C:/Users/Public/reversing/gta_sa_izzotop_12_04_2022 --assumed-cc --use-static-inline --class-name CBouncingPanel`

**Note: It is recommended you run clang-format. Go into the document in VS, and press CTRL+K + CTRL+D**

#### Program arguments
Type the following into the console: `py src/main.py -h`

## Special thanks to:
- [Izzotop](https://github.com/Izzotop) for inspiring me to use Jinja2
- [Codenulls](https://github.com/codenulls) for the modified plugins, and similar program (from which I took the inspiration)
- All [Plugin SDK](https://github.com/DK22Pac/plugin-sdk) contributors for their hard work

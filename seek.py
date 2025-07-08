from SeekClass import Seek
import pyfiglet
import sys

s = Seek()

#title
red_title = pyfiglet.figlet_format("Seek", font="bloody")
red = "\033[38;2;220;0;60m"
green =  "\033[92m"
reset =  "\033[0m"
print(red + red_title + reset)
print(green + "Version 1" + reset)



s.show_greeting()
try:
    while True:
        option = input("Enter 1 or 2: ").strip()
        if option == '1':
            installed_names = s.list_installed_programs()
            break
        elif option == '2':
            while True:
                program_name = input("Enter program name and extension. (enter 'exit' one you are done): ").strip()
                if program_name.lower() == 'exit':
                    break
                s.store_program(program_name)

            s.list_programs()

            result_list = [] #list for optional exporting

            for i in s.programs:
                entry = {"name": i}
                program_path = s.find_executable(i)
                if program_path:
                    version = s.program_version(program_path)
                    entry["version"] = version
                    entry["path"] = str(program_path)
                    print(f"{i} found at:", program_path, "✅")
                    print(f"↳ Version: {version}")

                    ports = s.program_ports(i)
                    entry["ports"] = ports if isinstance(ports, list) else [ports]
                    purple = "\033[35m"
                    reset = "\033[0m"
                    if isinstance(ports, list):
                        for port in ports:
                            print(f"↳ Listening on: {purple}{port}{reset}")
                    else:
                        print(f"↳ {ports}")
                else:
                    print(f"{i} not found.❌")
                    entry["version"] = "Not found"
                    entry["path"] = "Not found"
                    entry["ports"] = ["Not found"]

                result_list.append(entry)



            while True:
                export = input("Would you like to export these results to a CSV file? (y/n): ").strip().lower()
                if export == "y":
                    s.export_results(result_list)
                    break
                elif export == "n":
                    break
                else:
                    print("Invalid input, please enter 'y' or 'n'.")
            break
        else:
            print("Invalid input, please try again.")
except KeyboardInterrupt:
    print("\nExiting SEEK...")
    sys.exit(0)
except Exception as e:
    print(f"Unexpected error occured: {e}")
    sys.exit(1)

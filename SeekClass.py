import platform
from pathlib import Path
import subprocess
import csv
from datetime import datetime
import re

class Seek:
    def __init__(self):
        self.programs = []

    def strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)
    
    def show_greeting(self):
        print("\nSEEK is a cross platform recon and utility tool used for software enumeration, \nretrieving version info, and checking for network port activity.")
        print("Instructions: \n[-] Enter '1' to get a full list of installed programs. \n[-] Enter '2' to search for specific programs.")
  
    def store_program(self, program):
        if program and program.lower() != 'exit':
            self.programs.append(program)

    def list_programs(self):
        print("\nPrograms to find:")
        if not self.programs:
            print("No programs were entered.")
        else:
            for program in self.programs:
                print(f"- {program}")
        print("\n")

    def find_executable(self, name):
        operatingsys = platform.system()
        if operatingsys == "Linux":
            paths = [
                Path("/mnt/c/Program Files"),
                Path("/mnt/c/Program Files (x86)"),
                Path("/mnt/c/Windows/system32"),
                Path("/usr/bin"),
                Path("/usr/local/bin"),
                Path("/opt"),
                Path("/snap/bin"),
                Path("/bin"),
                Path("/sbin"),
                Path("/usr/sbin")
            ]

        elif operatingsys == "Windows":
            paths = [
             Path("C:/Program Files"),
             Path("C:/Program Files (x86)"),
             Path("C:/Windows/System32")
             ]

        for path in paths:
            for file in path.rglob(name):
                return file
        return None

    def program_version(self,program_path):
        operatingsys = platform.system()
        red = "\033[38;2;220;0;60m"
        reset =  "\033[0m"

        if operatingsys == "Windows":
            try:
                import win32api
                info = win32api.GetFileVersionInfo(str(program_path), "\\")
                ms = info['FileVersionMS']
                ls = info['FileVersionLS']
                version = f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
                light_blue = "\033[94m"
                reset = "\033[0m"
                return (f"{light_blue}{version}{reset}")
            except Exception as e:
                return f"Version info not available. ({red}{e}{reset})"

        elif operatingsys == "Linux":
            program_name = Path(program_path).stem

            try:
                output = subprocess.check_output(["dpkg", "-s", program_name], stderr=subprocess.DEVNULL, text=True)
                for line in output.splitlines():
                    if line.startswith("Version:"):
                        return line.split(":", 1)[1].strip()
            except subprocess.CalledProcessError:
                return "Version info not found (not installed via dpkg)"

        return "Unsupported OS"


    def program_ports(self, program_name):
        operatingsys = platform.system()
        red = "\033[38;2;220;0;60m"
        reset =  "\033[0m"

        if operatingsys == "Windows":
            try:
                tasklist = subprocess.check_output(["tasklist"], text=True)
                pids = []
                for line in tasklist.splitlines():
                    if program_name.lower() in line.lower():
                        parts = line.split()
                        if len(parts) > 1:
                            pids.append(parts[1])

                if not pids:
                    return "Program is not currently running"

                netstat = subprocess.check_output(["netstat", "-ano"], text=True)
                ports = []
                for line in netstat.splitlines():
                    for pid in pids:
                        if line.strip().endswith(pid) and "LISTENING" in line:
                            parts = line.split()
                            ports.append(parts[1])
                return ports if ports else "Running but not listening on any ports"
            except Exception as e:
                return f"Error checking ports:{red}{e}{reset}"

        elif operatingsys == "Linux":
            try:
                # Get all PIDs for matching process names
                ps_output = subprocess.check_output(["ps", "-eo", "pid,comm"], text=True)
                pids = []
                for line in ps_output.splitlines():
                    if program_name.lower() in line.lower():
                        parts = line.strip().split(None, 1)
                        if len(parts) == 2:
                            pids.append(parts[0])

                if not pids:
                    return "Program is not currently running"

                # Use ss to list listening ports with PID
                ss_output = subprocess.check_output(["ss", "-ltnp"], stderr=subprocess.DEVNULL, text=True)
                ports = []
                for line in ss_output.splitlines():
                    for pid in pids:
                        if f"pid={pid}," in line:
                            parts = line.split()
                            local_address = parts[3]
                            ports.append(local_address)
                return ports if ports else "Running but not listening on any ports"
            except Exception as e:
                return f"Error checking ports:{red}{e}{reset}"

        return "Unsupported OS"

    def list_installed_programs(self):
        operatingsys = platform.system()

        if operatingsys == "Windows":
            try:
                import winreg
            except ImportError:
                print("winreg module not available.")
                return
            program_list = []

            locations = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"), #registry path for system wide software installs
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"), #where 32bit applications on a 64 bit windows os are stored
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall") #path for software installed only for the current user
            ]
            for hive, path in locations:
                try:
                    with winreg.OpenKey(hive, path) as key:
                        num_subkeys = winreg.QueryInfoKey(key)[0]
                        for i in range(num_subkeys):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    program_list.append(name)
                            except (FileNotFoundError, PermissionError, OSError):
                                continue
                except FileNotFoundError:
                    continue
            print("\nInstalled Programs:")
            for program in sorted(set(program_list)):
                print(f"- {program}")


        elif operatingsys == "Linux":
            try:
                output = subprocess.check_output(["dpkg-query", "-W", "-f=${Package}\n"], text=True)
                print("\nInstalled Programs (Debian):")
                for line in output.strip().splitlines():
                    print(f"- {line}")
            except subprocess.CalledProcessError:
                    print("Could not determine installed programs.")
        else:
            print("Unsupported operating system.")


    def export_results(self, results, filename="seek_results.csv"):
       """
       Exports results to a CSV file. Supports full install list or specific scan results.
       `results` should be a list of dicts with keys: name, path (optional), version (optional), ports (optional)
       """

       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
       full_filename = f"{timestamp}_{filename}"

       try:
           with open(full_filename, mode="w", newline='', encoding='utf-8') as csvfile:
               fieldnames = ['Program Name', 'Path', 'Version', 'Listening Ports']
               writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
               writer.writeheader()

               for entry in results:
                   writer.writerow({
                       'Program Name': str(entry.get('name', 'N/A')),
                       'Path': str(entry.get('path', 'N/A')),
                       'Version': self.strip_ansi(entry.get('version', 'N/A')),
                       'Listening Ports': ", ".join(entry['ports']) if isinstance(entry.get('ports'), list) else entry.get('ports', 'N/A')
                   })

               print(f"\n✅ Results exported to {full_filename}")
       except Exception as e:
            print(f"\n❌ Failed to export CSV: {e}")

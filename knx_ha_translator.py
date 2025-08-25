# ──────────────────────────────────────────────────────────────────────────────
# Author: Tim Matejek
# License: MIT
# Version: 0.0.1
# Date: 2025-07-06
#
# KNX ESF to Home Assistant Translator
# 
# This script converts KNX ESF (Engineering Support File) exports into formats 
# directly usable in Home Assistant (YAML/config/buttons) or for further 
# processing (CSV/Excel). It is intended for users who want to migrate or 
# integrate their KNX-based home automation system into Home Assistant.
# ──────────────────────────────────────────────────────────────────────────────

import sys
import os
import csv

# FIXME: dachkuppel not recognized

#### Constants ####
CONSTANTS = {
    # General
    "DEFAULT_OUTPUT_FORMAT": "ha",
    "DEFAULT_JUNK_FIRST_COL": 1,
    # KNX Addresses
    "KNX_CLASSIFIER_LIGHT": "beleuchtung",
    "KNX_CLASSIFIER_COVER": "jalousien",
    "KNX_CLASSIFIER_JALOUSIE": "jal",
    "KNX_CLASSIFIER_ROLLO": "rollo",
    # TODO: Add more KNX classifiers as needed
    "MOVE_LONG_ADDRESS": "Auf/Ab",
    "STOP_ADDRESS": "Stopp",
    "POSITION_STATE_ADDRESS": "Status Position",
    "POSITION_ADDRESS": "Position",
    "ANGLE_STATE_ADDRESS": "Status Lamelle",
    "ANGLE_ADDRESS": "Lamelle",
    "STANDARD_TRAVELLING_TIME_LONG": 60, # Default travelling time for long covers in seconds, can be overridden in config
    "STANDARD_TRAVELLING_TIME_SHORT": 30, # Default travelling time for short covers in seconds, can be overridden in config
}
config = {}

##### Guiding ######
# Function to print the logo
def print_logo():
    logo = r"""
 _ __ _ _ __  _                                                    
| / /| \ |\ \/                                                     
|  \ |   | \ \                                                     
|_\_\|_\_|_/\_\                                                    
 _ _                    ___          _        _                _   
| | | ___ ._ _ _  ___  | . | ___ ___<_> ___ _| |_  ___ ._ _  _| |_ 
|   |/ . \| ' ' |/ ._> |   |<_-<<_-<| |<_-<  | |  <_> || ' |  | |  
|_|_|\___/|_|_|_|\___. |_|_|/__//__/|_|/__/  |_|  <___||_|_|  |_|  
 ___                     _         _                               
|_ _| _ _  ___ ._ _  ___| | ___  _| |_  ___  _ _                   
 | | | '_><_> || ' |<_-<| |<_> |  | |  / . \| '_>                  
 |_| |_|  <___||_|_|/__/|_|<___|  |_|  \___/|_|           
"""
    print(logo)

# Function to display usage instructions
def usage():
    print("Usage: python convert_esf_to_csv.py <inputfile.esf> [outputfile] [csv|ha|yaml]")
    print("  <inputfile.esf> : Input ESF file (required, must end with .esf)")
    print("  [outputfile]    : Output file name (optional, ends with .csv for csv mode, .txt for ha, .yaml for yaml mode, .txt for buttons mode)")
    print("  [csv|ha|yaml|buttons]   : Output format (optional, default is ha)")
    print("  [namesfile]     : Custom names file (optional, must be .csv file and called names.csv)")
    print("  [configfile]    : Custom configuration file (optional, must be .csv file and called config.csv)")
    print()
    print("Modes:")
    print("  Command Line Mode: Provide arguments as shown above to run the conversion directly.")
    print("  Interactive Mode:  If no arguments are given, you will be prompted to enter them interactively.")
    sys.exit(1)
    
# Handle interactive configuration
def handle_interactive_config():
    choice = input("Do you want to load a configuration file? (f for file/i for interactive/N): ").strip().lower()
    if choice == 'f':
        config_file = input("Enter path to configuration file (must be .csv): ").strip()
        return load_config(config_file)
    elif choice == 'i':
        print("Interactive configuration mode (enter value to override or leave blank to keep default):")
        prod_constants = {}
        for key, default_value in CONSTANTS.items():
            value = input(f"{key} (default: {default_value}): ").strip()
            if value:
                prod_constants[key] = value
            else:
                prod_constants[key] = default_value
        return prod_constants
    else:
        print("No configuration file will be loaded. Using default values.")
        return CONSTANTS.copy()

#### Input Functionality ######
# Function to validate the input file
def validate_input_file(input_path):
    if not input_path.lower().endswith('.esf'):
        print("Error: Input file must have .esf extension.")
        return False, None
    if not os.path.isfile(input_path):
        print(f"Error: File '{input_path}' does not exist.")
        return False, None
    base = os.path.splitext(os.path.basename(input_path))[0]
    return True, base

# Function to validate the names file
def validate_names_file(names_file_path):
    if not names_file_path.lower().endswith('.csv'):
        print("Error: Names file must have .csv extension.")
        return None
    if not os.path.isfile(names_file_path):
        print(f"Error: File '{names_file_path}' does not exist.")
        return None
    
    # Check if the names file has exactly two columns per row and correct header
    names_content = []
    with open(names_file_path, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        try:
            first_row = next(reader)
        except StopIteration:
            print("Error: Names file is empty.")
            return None
        
        # Remove BOM from the first column if present
        first_row = [col.lstrip('\ufeff').strip() for col in first_row] 
        if first_row != ["ID", "Name"]:
            print("Error: The first row of the names file must be: ID, Name")
            return None
        for row in reader:
            if len(row) != 2:
                print("Error: Names file must have exactly two columns per row.")
                return None
            names_content.append(row)
            
    return names_content

# Function to parse the ESF file and extract address and name pairs
def parse_esf(input_path, valid_names=None):
    global config
    
    rows = []
    
    # Try to open the file with different encodings
    encodings_to_try = ["utf-8", "utf-8-sig", "latin1"]
    esf_file = None
    for enc in encodings_to_try:
        try:
            esf_file = open(input_path, encoding=enc)
            # Try reading a line to check if decoding works
            esf_file.readline()
            esf_file.seek(0)
            break
        except UnicodeDecodeError:
            if esf_file:
                esf_file.close()
            esf_file = None
            continue
    if esf_file is None:
        print(f"Error: Could not decode file '{input_path}' with utf-8, utf-8-sig, or latin1.")
        return rows
    
    counter = 0
    for line in esf_file:
        counter += 1
        line = line.strip()
        
        # Skip the first DEFAULT_JUNK_FIRST_COL lines
        if counter <= config["DEFAULT_JUNK_FIRST_COL"]:
            continue
        parts = line.split('\t')
        
        # Skip lines that do not have enough parts
        if len(parts) < 3:
            continue
        
        # Extract address, name, classification, and action
        first_col = parts[0].split('.')
        if len(first_col) < 2:
            continue
        
        # Determine classification based on rules
        second_col = parts[1].lower() if len(parts) > 1 else ""
        if config["KNX_CLASSIFIER_LIGHT"] in first_col[0].lower():
            # Skip if the original name starts with "st/"
            if any(parts[1].strip().lower().startswith(prefix) for prefix in ("w/", "rd/", "st/", "st_w/")):
                continue
            classification = "beleuchtung"
        elif config["KNX_CLASSIFIER_COVER"] in first_col[0].lower() and config["KNX_CLASSIFIER_JALOUSIE"] in second_col:
            classification = "jalousie"
        elif config["KNX_CLASSIFIER_COVER"] in first_col[0].lower() and config["KNX_CLASSIFIER_ROLLO"] in second_col:
            classification = "rollo"
        else:
            classification = "unknown"
        # TODO: Add more classification rules as needed
        
        address = first_col[-1]
        action = first_col[-2]
        
        # Determine name based on valid names or default
        def clean_name(name):
            # Remove leading and trailing spaces
            name = name.strip()
            # Remove underscores at the beginning and end
            name = name.lstrip('_').rstrip('_')
            
            # If 'jal' or 'rollo' is in the name, cut off after that word (inclusive)
            for keyword in ("jal", "rollo"):
                idx = name.find(keyword)
                if idx != -1:
                    name = name[:idx + len(keyword)]
                    break
            return name
        
        if valid_names is None:
            name = clean_name(parts[1])
        else:
            matches = [row for row in valid_names if row[0] == parts[0]]
            if len(matches) == 1:
                name = matches[0][1]
            else:
                name = clean_name(parts[1])
            
        rows.append((address, name, classification, action))
        
    esf_file.close()
    return rows
    
# Load configuration from a file or environment variables
def load_config(config_file):
    if not config_file.lower().endswith('.csv'):
        print("Error: Configuration file must have .csv extension.")
        return None
    if config_file.lower() != 'config.csv':
        print("Warning: Configuration file should be named 'config.csv' for consistency.")
    if not os.path.isfile(config_file):
        print(f"Error: File '{config_file}' does not exist.")
        return None
    
    with open(config_file, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        prod_constants = {}
        
        try:
            first_row = next(reader)
        except StopIteration:
            print("Error: Names file is empty.")
            return None
        
        # Remove BOM from the first column if present
        first_row = [col.lstrip('\ufeff').strip() for col in first_row] 
        if first_row != ["Key", "Value"]:
            print("Error: The first row of the config file must be: Key, Value")
            return None
        
        # Iterate through CONSTANTS and set default values
        for key in CONSTANTS:
            prod_constants[key] = CONSTANTS[key]

        # Now update with values from config file if present
        for row in reader:
            if len(row) != 2:
                print("Error: Config file must have exactly two columns per row.")
                return None
            else:
                key, value = row
                if key.strip() in CONSTANTS:
                    prod_constants[key.strip()] = value.strip()
                else:
                    prod_constants[key.strip()] = CONSTANTS.get(key.strip(), value.strip())
                
        return prod_constants

###### Option Functionality ######
# Function to write the extracted data to a CSV file
def write_csv(rows, output_path):
    with open(output_path, "w", newline='', encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Address", "Name", "Classification", "Action"])
        for address, name, classification, action in rows:
            writer.writerow([address, name, classification, action])
            
# Function to write the extracted data to Home Assistant YAML format
def create_ha_yaml(rows):
    global config
    
    yaml_content = "knx:\n"
    
    # Write the lights section
    lights = [(address, name) for address, name, classification, action in rows if classification == "beleuchtung"]
    if lights:
        yaml_content += "  light:\n"
        for address, name in lights:
            yaml_content += f'    - name: "{name}"\n'
            yaml_content += f'      address: "{address}"\n'
            
    yaml_content += "\n"
            
    # Write cover section
    covers = [(address, name, classification, action) for address, name, classification, action in rows if classification in ("jalousie", "rollo")]
    if covers:
        yaml_content += "  cover:\n"
        # Get unique names for covers
        def remove_last_word(name):
            return name.rsplit(' ', 1)[0] if ' ' in name else name

        unique_names = sorted(set(remove_last_word(name) for _, name, _, _ in covers))
        
        # Iterate over unique cover names
        for name in unique_names:
            # Find all rows for this cover name
            relevant_rows = [row for row in covers if name in row[1]]
            # Helper to find address by action substring
            def find_address(substring, notsubstring=None):
                for address, _, _, action in relevant_rows:
                    if substring in action and (not notsubstring or notsubstring not in action):
                        return address
                return "MISSING"
            
            move_long_address = find_address(config["MOVE_LONG_ADDRESS"])
            stop_address = find_address(config["STOP_ADDRESS"])
            position_state_address = find_address(config["POSITION_STATE_ADDRESS"])
            position_address = find_address(config["POSITION_ADDRESS"], notsubstring=config["POSITION_STATE_ADDRESS"])
            angle_state_address = find_address(config["ANGLE_STATE_ADDRESS"])
            angle_address = find_address(config["ANGLE_ADDRESS"], notsubstring=config["ANGLE_STATE_ADDRESS"])
            
            yaml_content += f'    - name: "{name}"\n'
            yaml_content += f'      move_long_address: "{move_long_address}"\n'
            yaml_content += f'      move_short_address: "{stop_address}"\n'
            yaml_content += f'      stop_address: "{stop_address}"\n'
            yaml_content += f'      position_address: "{position_address}"\n'
            yaml_content += f'      position_state_address: "{position_state_address}"\n'
            # Add angle addresses only for jalousie covers
            cover_classification = next((row[2] for row in relevant_rows), None)
            if cover_classification == "jalousie":
                yaml_content += f'      angle_address: "{angle_address}"\n'
                yaml_content += f'      angle_state_address: "{angle_state_address}"\n'
            # TODO: Add travelling time based on size
            yaml_content += f'      travelling_time_down: "{config["STANDARD_TRAVELLING_TIME_LONG"]}"\n'
            yaml_content += f'      travelling_time_up: "{config["STANDARD_TRAVELLING_TIME_LONG"]}"\n'
            
        # TODO: Add further knx entities if needed
    
    return yaml_content

# Function to write file with the extracted data to Home Assistant YAML format
def write_ha_yaml(rows, output_path):
    with open(output_path, "w", encoding="utf-8-sig", newline='\r\n') as txt_file:
        txt_file.write(create_ha_yaml(rows))

# Function to write the extracted data to Home Assistant config format
def write_ha_config(rows, output_path):
    with open(output_path, "w", encoding="utf-8-sig", newline='\r\n') as txt_file:
        txt_file.write(create_ha_yaml(rows))
        
# Function to write buttons for all KNX entities in yaml format
def write_buttons_file(rows, output_path):
    # Function to format button names as in Home Assistant config
    def format_button_name(name):
        # Format the name as in Home Assistant config, but convert German umlauts
        name = name.replace(' ', '_').lower()
        name = name.replace('.', '_')
        name = name.replace('/', '_')
        name = name.replace('ä', 'a').replace('ö', 'o').replace('ü', 'u')
        # If 'jal' or 'rollo' is in the name, cut off after that word (inclusive)
        for keyword in ("jal", "rollo"):
            idx = name.find(keyword)
            if idx != -1:
                name = name[:idx + len(keyword)]
                break
        return name
    
    with open(output_path, "w", encoding="utf-8-sig", newline='\r\n') as txt_file:
        txt_file.write("##### Buttons for KNX entities #####\n")
        
        # Write buttons for lights
        txt_file.write("\n# Buttons for lights\n")
        for address, name, classification, action in rows:
            if classification == "beleuchtung":
                txt_file.write(f'- type: button\n  show_icon: true\n  show_name: true\n  entity: light.{format_button_name(name)}\n')

        # Write buttons for unique covers (jalousie, rollo)
        txt_file.write("\n# Buttons for covers\n")
        covers = [(address, name, classification, action) for address, name, classification, action in rows if classification in ("jalousie", "rollo")]
        
        # Get unique names for covers
        def remove_last_word(name):
            return name.rsplit(' ', 1)[0] if ' ' in name else name

        unique_names = sorted(set(remove_last_word(name) for _, name, _, _ in covers))
        
        # Iterate over unique cover names and write buttons
        for name in unique_names:
            # Add cover specific buttons  
            # Find all rows for this cover name
            relevant_rows = [row for row in covers if remove_last_word(row[1]) == name]
            # Determine if any of the relevant rows is a jalousie
            cover_classification = next((row[2] for row in relevant_rows if row[2] == "jalousie"), "rollo")
            if cover_classification == "jalousie":
                txt_file.write(f'- type: tile\n  entity: cover.{format_button_name(name)}\n  features_position: bottom\n  vertical: false\n')
            else:
                txt_file.write(f'- type: entity\n  entity: cover.{format_button_name(name)}\n')
        
        # TODO: Add further knx entities if needed

###### Interactive Mode Functionality ######
def interactive_mode():
    global config

    # Print the logo and welcome message
    print_logo()
    print("Welcome to the KNX ↔ Home Assistant Translator interactive mode!\n")
    print("Please select an option:")
    print("1) Translate KNX ESF file to Home Assistant yaml format for manual copying.")
    print("2) Translate KNX ESF file to Home Assistant yaml config file for sub-config import.")
    print("3) Translate KNX ESF file to CSV.")
    print("4) Create buttons for all KNX entities in yaml format for manual copying.")
    # Add options here
    print("0) Exit.")
    
    # Loop until user chooses to exit
    try:
        while True:
            choice = input("\nEnter your choice (0-4): ").strip()
            
            # Exit option
            if choice == "0":
                print("Goodbye!")
                sys.exit(0)
                
            # Handle options
            elif choice in ("1", "2", "3", "4"):
                # Optional: Load configuration
                config = handle_interactive_config()
                
                # Get input file path
                input_path = input("Enter path to ESF file: ").strip()
                valid, base = validate_input_file(input_path)
                if not valid:
                    continue
                
                # Optional: Get names file
                names_file = input("Enter names file path (or leave blank for no names file): ").strip()
                valid_names = None
                if names_file:
                    valid_names = validate_names_file(names_file)
                    if not valid_names:
                        continue
                
                # Determine output file name based on choice
                # Option: Translate KNX ESF file to Home Assistant yaml format for manual copying.
                if choice == "1":
                    output_path = input("Enter output file name (or leave blank for default): ").strip()
                    if not output_path:
                        output_path = os.path.join(os.path.dirname(input_path), f"{base}_config.txt")
                    elif not output_path.lower().endswith('.txt'):
                        print("Error: Output file must have .txt extension for yaml mode.")
                        continue
                    
                    # Parse the ESF file and write to the specified output format
                    rows = parse_esf(input_path, valid_names) if valid_names else parse_esf(input_path)
                    
                    write_ha_yaml(rows, output_path)
                    print(f"Conversion complete. Output written to: {output_path}")
                    continue
                
                # Option: Translate KNX ESF file to Home Assistant yaml config file for sub-config import.
                elif choice == "2":
                    output_path = input("Enter output file name (or leave blank for default): ").strip()
                    if not output_path:
                        output_path = os.path.join(os.path.dirname(input_path), f"knx_config.yaml")
                    elif not output_path.lower().endswith('.yaml'):
                        print("Error: Output file must have .yaml extension for config mode.")
                        continue
                    
                    # Parse the ESF file and write to the specified output format
                    rows = parse_esf(input_path, valid_names) if valid_names else parse_esf(input_path)
                    
                    write_ha_config(rows, output_path)
                    print(f"Conversion complete. Output written to: {output_path}\n")
                    print(f"You can now import the yaml file into your main Home Assistant yaml using: 'scene: !include {output_path}'\n")
                    continue
                
                # Option: Translate KNX ESF file to CSV.
                elif choice == "3":
                    output_path = input("Enter output file name (or leave blank for default): ").strip()
                    if not output_path:
                        output_path = os.path.join(os.path.dirname(input_path), f"{base}_translated.csv")
                    elif not output_path.lower().endswith('.csv'):
                        print("Error: Output file must have .csv extension for csv mode.")
                        continue
                    
                    # Parse the ESF file and write to the specified output format
                    rows = parse_esf(input_path, valid_names) if valid_names else parse_esf(input_path)
                    
                    write_csv(rows, output_path)
                    print(f"Conversion complete. Output written to: {output_path}")
                    continue
                
                # Option: Create buttons for all KNX entities in yaml format.
                elif choice == "4":
                    output_path = input("Enter output file name (or leave blank for default): ").strip()
                    if not output_path:
                        output_path = os.path.join(os.path.dirname(input_path), f"{base}_buttons.txt")
                    elif not output_path.lower().endswith('.txt'):
                        print("Error: Output file must have .txt extension for buttons mode.")
                        continue
                    
                    # Parse the ESF file and write to the specified output format
                    rows = parse_esf(input_path, valid_names) if valid_names else parse_esf(input_path)
                    
                    write_buttons_file(rows, output_path)
                    print(f"Creation complete. Output written to: {output_path}")
                    continue
            
            # If the choice is invalid, prompt again
            else:
                print("Invalid choice. Please enter an offered option.")
                
    # Handle keyboard interrupt gracefully
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt detected. Goodbye!")
        sys.exit(0)

###### Command Line Arguments Handling ######      
def manual_mode():
    global config

    # Check if the input file is provided and valid
    input_path = sys.argv[1]
    valid, base = validate_input_file(input_path)
    if not valid:
        sys.exit(1)

    # Defaults
    output_format = None
    output_path = None
    names_file = None
    config_file = None

    # Parse optional arguments in any order
    for arg in sys.argv[2:]:
        arg_lower = arg.lower()
        if arg_lower in ("csv", "ha", "yaml", "buttons"):
            output_format = arg_lower
        elif arg_lower == "names.csv":
            names_file = arg
        elif arg_lower == "config.csv":
            config_file = arg
        else:
            output_path = arg
            
    # Load configuration if needed
    if config_file:
        config = load_config(config_file)
    else:
        config = CONSTANTS.copy()
        
    # Set default output format if not specified
    if not output_format:
        output_format = config["DEFAULT_OUTPUT_FORMAT"]

    # Set output file name if not given
    base = os.path.splitext(os.path.basename(input_path))[0]
    if not output_path:
        if output_format == "csv":
            output_path = os.path.join(os.path.dirname(input_path), f"{base}_translated.csv")
        elif output_format == "ha":
            output_path = os.path.join(os.path.dirname(input_path), f"{base}_config.txt")
        elif output_format == "buttons":
            output_path = os.path.join(os.path.dirname(input_path), f"{base}_buttons.txt")
        else:  # yaml
            output_path = os.path.join(os.path.dirname(input_path), f"knx_config.yaml")
    else:
        if output_format == "csv" and not output_path.lower().endswith('.csv'):
            print("Error: Output file must have .csv extension for csv mode.")
            sys.exit(1)
        if output_format == "ha" and not output_path.lower().endswith('.txt'):
            print("Error: Output file must have .txt extension for config mode.")
            sys.exit(1)
        if output_format == "yaml" and not output_path.lower().endswith('.yaml'):
            print("Error: Output file must have .yaml extension for yaml mode.")
            sys.exit(1)
        if output_format == "buttons" and not output_path.lower().endswith('.txt'):
            print("Error: Output file must have .txt extension for buttons mode.")
            sys.exit(1)
            
    # Validate names file if provided
    valid_names = None
    if names_file:
        valid_names = validate_names_file(names_file)
        if not valid_names:
            sys.exit(1)
    
    # Parse the ESF file and write to the specified output format
    rows = parse_esf(input_path, valid_names) if valid_names else parse_esf(input_path)
    
    # Write to the specified output format
    if output_format == "csv":
        write_csv(rows, output_path)
    elif output_format == "ha":
        write_ha_yaml(rows, output_path)
    elif output_format == "yaml":
        write_ha_config(rows, output_path)
        print(f"You can now import the yaml file into your main Home Assistant yaml using: 'scene: !include {output_path}'\n")
    elif output_format == "buttons":
        write_buttons_file(rows, output_path)
    else:
        print(f"Error: Unsupported output format '{output_format}'. Supported formats are csv, ha, yaml, and buttons.")
        sys.exit(1)

    print(f"Conversion complete. Output written to: {output_path}")

def main():
    # If no arguments are provided, start interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
        return
    
    # Help mode
    if len(sys.argv) == 2 and sys.argv[1].lower() in ("-h", "--help"):
        usage()

    # Not enough arguments provided
    if len(sys.argv) < 2:
        usage()

    # If the first argument is an ESF file, proceed with manual mode
    manual_mode()

if __name__ == "__main__":
    main()
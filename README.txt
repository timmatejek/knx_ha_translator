# KNX ESF to Home Assistant Translator

## Introduction

This script helps you convert KNX ESF (Engineering Support File) exports into formats that are directly usable in [Home Assistant](https://www.home-assistant.io/) or for further processing (e.g., in Excel).  
If you have a KNX-based home automation system and want to integrate or migrate your KNX devices into Home Assistant, this tool will save you hours of manual work by generating YAML or CSV files from your ESF export.

---

## Features

- **CSV Export:** For further processing or import into Excel.
- **Home Assistant YAML Export:** For direct copy-paste into your `configuration.yaml`.
- **Home Assistant YAML Config Export:** For sub-config import or advanced Home Assistant setups.
- **Home Assistant YAML Buttons Export:** Simple buttons for all KNX entities in YAML.
- **Interactive Mode:** User-friendly, menu-driven interface if no command-line arguments are given.
- **Robust Error Handling:** Handles encoding issues and keyboard interrupts gracefully.

---

## Requirements

- Python 3.7 or newer
- No external dependencies (uses only the Python standard library)

---

## Usage

You can use the script in two ways:

### 1. Command-Line Mode

Run the script with parameters for quick conversion:

```sh
python knx_ha_translator.py <inputfile.esf> [outputfile] [csv|ha|yaml]
```

- `<inputfile.esf>`: **(required)** Path to your KNX ESF file (must end with `.esf`)
- `[outputfile]`: **(optional)** Output file name. Must end with `.csv` for CSV mode, `.txt` for YAML/HA modes. If omitted, a default name is generated.
- `[csv|ha|yaml]`: **(optional)** Output format:
  - `csv`: Standard CSV for Excel or further processing (default)
  - `ha`: Home Assistant YAML format for manual copy-paste
  - `yaml`: Home Assistant YAML config file for import

**Examples:**
```sh
python knx_ha_translator.py myproject.esf
python knx_ha_translator.py myproject.esf output.csv csv
python knx_ha_translator.py myproject.esf output.txt ha
python knx_ha_translator.py myproject.esf output.txt yaml
```

### 2. Interactive Mode

If you run the script without parameters, it will start in interactive mode:

```sh
python knx_ha_translator.py
```

You will see a menu with options:
```
KNX ↔ Home Assistant Translator

Welcome to the KNX ↔ Home Assistant Translator interactive mode!

Please select an option:
1) Translate KNX ESF file to Home Assistant yaml format for manual copying.
2) Translate KNX ESF file to Home Assistant yaml config file for sub-config import.
3) Translate KNX ESF file to CSV.
4) Create buttons for all KNX entities in yaml format for manual copying.
0) Exit.
```
Just enter the number of your choice and follow the prompts.

---

## Input Formats

- **names.csv:**  
  Two columns: ID and name including header (ID, Names).

- **config.csv:**  
  Two columns: Key and value including header (Key, Value).

- **knx.esf:**
  Four columns: ID, name, XX, XX without header (if header contained the DEFAULT_JUNK_FIRST_COL can be set accordingly).

---

## Output Formats

- **CSV:**  
  Two columns: KNX group address and entity name (spaces replaced with underscores).  
  Compatible with Excel (UTF-8 with BOM).

- **Home Assistant YAML:**  
  Generates a YAML section for `lights` and `cover` (jalousie/rollo) entities, ready to copy into your `configuration.yaml`.

- **Home Assistant YAML Config:**  
  Generates a YAML file suitable for importing as a sub-configuration in Home Assistant.

---

## Error Handling

- If the ESF file contains invalid characters, they are replaced with `?`.
- If you press `Ctrl+C` in interactive mode, the script exits gracefully.

---

## Author & License

**Author:** Tim Matejek  
**Copyright:** MIT License
**Version:** 0.0.1
**Date:** 2025-07-06

---

## When to Use

Use this script if you have a KNX home automation system and want to:
- Quickly migrate your KNX group addresses and device names into Home Assistant.
- Avoid manual YAML editing or error-prone copy-pasting.
- Generate CSVs for documentation or further processing.

---
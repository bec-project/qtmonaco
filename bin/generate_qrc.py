#!/usr/bin/env python3
"""
Generate QRC and RCC files from dist directory for PySide6.

This script creates a Qt Resource Collection (.qrc) file from the dist directory
and automatically compiles it to a binary RCC file for use in PySide6 applications.

Usage:
    python generate_qrc.py
"""

import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List


def get_file_list(build_dir: Path) -> List[Path]:
    """
    Get list of all files in build directory, excluding certain extensions.

    Args:
        build_dir: Path to build directory

    Returns:
        List of file paths relative to build_dir
    """
    exclude_extensions = {".map", ".txt", ".md"}

    files = []
    for root, dirs, filenames in os.walk(build_dir):
        # Skip hidden directories and common build artifacts
        dirs[:] = [
            d for d in dirs if not d.startswith(".") and d not in {"node_modules", "__pycache__"}
        ]

        for filename in filenames:
            file_path = Path(root) / filename
            relative_path = file_path.relative_to(build_dir)

            # Skip files with excluded extensions
            if relative_path.suffix.lower() not in exclude_extensions:
                files.append(relative_path)

    return sorted(files)


def create_qrc_content(files: List[Path], build_dir: Path) -> str:
    """
    Create QRC XML content from file list.

    Args:
        files: List of file paths relative to build directory
        build_dir: Build directory path to include in file paths

    Returns:
        QRC XML content as string
    """
    # Create root element
    root = ET.Element("RCC")
    root.set("version", "1.0")

    # Create qresource element
    qresource = ET.SubElement(root, "qresource")
    qresource.set("prefix", "/monaco")

    # Add each file with build directory prefix
    for file_path in files:
        file_element = ET.SubElement(qresource, "file")
        # Include build directory in the path
        full_path = build_dir / file_path
        file_element.text = str(full_path).replace("\\", "/")  # Use forward slashes for Qt

    # Pretty print the XML
    ET.indent(root, space="  ")

    # Create XML declaration and return
    xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}\n'


def compile_to_rcc(qrc_file: Path, rcc_file: Path) -> bool:
    """
    Compile QRC file to binary RCC file using pyside6-rcc.

    Args:
        qrc_file: Path to QRC file
        rcc_file: Path to output RCC file

    Returns:
        True if compilation was successful, False otherwise
    """
    try:
        cmd = ["pyside6-rcc", "-binary", str(qrc_file), "-o", str(rcc_file)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error compiling QRC to RCC: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: pyside6-rcc not found. Make sure PySide6 is installed.")
        return False


def main():
    build_dir = Path("dist")
    qrc_file = Path("monaco_resources.qrc")
    rcc_file = Path("monaco.rcc")

    # Validate build directory
    if not build_dir.exists():
        print(f"Error: Build directory '{build_dir}' does not exist")
        print("Make sure to run 'npm run build' first")
        return 1

    # Get file list
    files = get_file_list(build_dir)

    if not files:
        print(f"Warning: No files found in '{build_dir}'")
        return 1

    print(f"Found {len(files)} files in '{build_dir}':")
    for file_path in files[:5]:  # Show first 5 files
        print(f"  {file_path}")
    if len(files) > 5:
        print(f"  ... and {len(files) - 5} more files")

    # Generate QRC content
    qrc_content = create_qrc_content(files, build_dir)

    # Write QRC file
    with open(qrc_file, "w", encoding="utf-8") as f:
        f.write(qrc_content)

    print(f"\n✓ Generated QRC file: {qrc_file}")

    # Compile to RCC
    print(f"Compiling to RCC file...")
    if compile_to_rcc(qrc_file, rcc_file):
        print(f"✓ Generated RCC file: {rcc_file}")

        # Clean up QRC file since we only need the RCC
        qrc_file.unlink()
        print(f"✓ Cleaned up temporary QRC file")

        print(f"\n🎉 Success! Use {rcc_file} in your PySide6 application:")
        print(f"   QResource.registerResource('{rcc_file}')")
        print(f"   # Access resources with: qrc:/monaco/index.html")

        return 0
    else:
        print(f"✗ Failed to compile RCC file")
        return 1


if __name__ == "__main__":
    exit(main())

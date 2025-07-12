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
from typing import List


def get_file_list(build_dir: str) -> List[str]:
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
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, build_dir)

            # Skip files with excluded extensions
            if not any(relative_path.endswith(ext) for ext in exclude_extensions):
                files.append(relative_path)

    return sorted(files)


def create_qrc_content(files: List[str], build_dir: str) -> str:
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
        full_path = os.path.join(build_dir, file_path)
        file_element.text = str(full_path).replace("\\", "/")  # Use forward slashes for Qt

    # Pretty print the XML
    ET.indent(root, space="  ")

    # Create XML declaration and return
    xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}\n'


def compile_to_rcc(qrc_file: str, rcc_file: str) -> bool:
    """
    Compile QRC file to binary RCC file using pyside6-rcc.

    Args:
        qrc_file: Path to QRC file
        rcc_file: Path to output RCC file

    Returns:
        True if compilation was successful, False otherwise
    """
    try:
        cmd = ["pyside6-rcc", qrc_file, "-o", rcc_file]
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

    build_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
    rcc_build_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "qtmonaco")
    js_build_dir = os.path.join(rcc_build_dir, "js_build")
    qrc_file = os.path.join(rcc_build_dir, "monaco_resources.qrc")
    rcc_file = os.path.join(rcc_build_dir, "_monaco_rcc.py")

    # Validate build directory
    if not os.path.exists(build_dir):
        print(f"Error: Build directory '{build_dir}' does not exist")
        print("Make sure to run 'npm run build' first")
        return 1

    # Copy dist directory to qtmonaco
    if not os.path.exists(js_build_dir):
        os.makedirs(js_build_dir, exist_ok=True)
        os.system(f"cp -r {build_dir}/* {js_build_dir}/")

    # Get file list
    files = get_file_list(js_build_dir)

    if not files:
        print(f"Warning: No files found in '{js_build_dir}'")
        return 1

    print(f"Found {len(files)} files in '{js_build_dir}':")
    for file_path in files[:5]:  # Show first 5 files
        print(f"  {file_path}")
    if len(files) > 5:
        print(f"  ... and {len(files) - 5} more files")

    # Generate QRC content
    qrc_content = create_qrc_content(files, "js_build")

    # Write QRC file
    with open(qrc_file, "w", encoding="utf-8") as f:
        f.write(qrc_content)

    print(f"\n✓ Generated QRC file: {qrc_file}")

    # # Compile to RCC
    # print("Compiling to RCC file...")
    # os.makedirs(rcc_build_dir, exist_ok=True)  # Ensure build directory exists
    # if compile_to_rcc(qrc_file, rcc_file):
    #     print(f"✓ Generated RCC file: {rcc_file}")

    #     # Clean up QRC file since we only need the RCC
    #     os.remove(qrc_file)
    #     print("✓ Cleaned up temporary QRC file")

    #     print("\n🎉 Success!")
    #     return 0
    # print("✗ Failed to compile RCC file")
    return 0


if __name__ == "__main__":
    exit(main())

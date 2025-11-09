#!/usr/bin/env python3
"""
Helper script to download all starCAT reference files as .tar.gz
and save them in the starcat/references directory.
"""

import urllib.request
import os
import sys
from pathlib import Path

# URL of the TSV file containing reference information
TSV_URL = "https://raw.githubusercontent.com/immunogenomics/starCAT/main/src/starcat/current_references.tsv"

# Directory to save references
REFERENCES_DIR = Path(__file__).parent / "starcat" / "references"


def download_file(url, destination):
    """Download a file from URL to destination with progress indication."""
    print(f"Downloading: {url}")
    print(f"Saving to: {destination}")

    try:
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192

            with open(destination, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')

            print()  # New line after progress
            print(f"✓ Successfully downloaded: {destination.name}\n")
            return True

    except Exception as e:
        print(f"\n✗ Error downloading {url}: {e}\n")
        return False


def main():
    # Create references directory if it doesn't exist
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"References directory: {REFERENCES_DIR}\n")

    # Download and parse the TSV file
    print(f"Fetching reference list from: {TSV_URL}")
    try:
        with urllib.request.urlopen(TSV_URL) as response:
            lines = response.read().decode('utf-8').strip().split('\n')
    except Exception as e:
        print(f"Error fetching TSV file: {e}")
        sys.exit(1)

    # Skip comment lines and parse header
    data_lines = [line for line in lines if not line.startswith('#')]
    if len(data_lines) < 2:
        print("Error: TSV file appears to be empty or malformed")
        sys.exit(1)

    header = data_lines[0].split('\t')
    try:
        link_index = header.index('Link')
        name_index = header.index('Name')
    except ValueError as e:
        print(f"Error: Required column not found in TSV: {e}")
        sys.exit(1)

    print(f"Found {len(data_lines) - 1} reference(s) to download\n")

    # Download each reference
    successful = 0
    failed = 0

    for line in data_lines[1:]:
        columns = line.split('\t')
        if len(columns) <= max(link_index, name_index):
            print(f"Warning: Skipping malformed line: {line}")
            continue

        link = columns[link_index]
        name = columns[name_index]

        # Extract filename from URL
        filename = link.split('/')[-1]
        destination = REFERENCES_DIR / filename

        # Skip if already exists
        if destination.exists():
            print(f"⊙ Already exists: {filename} (skipping)\n")
            continue

        # Download the file
        if download_file(link, destination):
            successful += 1
        else:
            failed += 1

    # Summary
    print("=" * 50)
    print(f"Download complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped (already exists): {len(data_lines) - 1 - successful - failed}")
    print("=" * 50)


if __name__ == "__main__":
    main()

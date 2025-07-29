#!/usr/bin/env python3

import hashlib
from pathlib import Path

def get_file_hash(filepath):
    """Calculate SHA256 hash of a file."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except FileNotFoundError:
        return None

def get_platforms():
    """Get list of platform directories."""
    platforms_dir = Path('platforms')
    if not platforms_dir.exists():
        return []
    
    platforms = [d.name for d in platforms_dir.iterdir() 
                if d.is_dir() and (d / 'metadata').exists()]
    return sorted(platforms)

def get_metadata_files(platform):
    """Get list of metadata files for a platform."""
    metadata_dir = Path('platforms') / platform / 'metadata'
    if not metadata_dir.exists():
        return []
    
    files = [f.name for f in metadata_dir.iterdir() if f.is_file()]
    return sorted(files)

def compare_platforms():
    """Compare metadata files across all platforms."""
    platforms = get_platforms()
    if not platforms:
        print("No platforms found!")
        return
    
    # Get all unique metadata files across platforms
    all_files = set()
    for platform in platforms:
        files = get_metadata_files(platform)
        all_files.update(files)
    
    all_files = sorted(all_files)
    
    for filename in all_files:
        print(f"\nFile: {filename}")
        print("-" * (len(filename) + 6))
        
        # Calculate hashes for this file across all platforms
        file_hashes = {}
        for platform in platforms:
            filepath = Path('platforms') / platform / 'metadata' / filename
            file_hashes[platform] = get_file_hash(filepath)
        
        # Print platform headers
        print(f"{'':>12}", end="")
        for platform in platforms:
            print(f"{platform:>12}", end="")
        print()
        
        # Print comparison matrix
        for i, platform1 in enumerate(platforms):
            print(f"{platform1:>12}", end="")
            for j, platform2 in enumerate(platforms):
                if file_hashes[platform1] is None or file_hashes[platform2] is None:
                    # File missing in one or both platforms
                    if file_hashes[platform1] is None and file_hashes[platform2] is None:
                        symbol = "?"  # Both missing
                    else:
                        symbol = "✗"  # One missing
                elif file_hashes[platform1] == file_hashes[platform2]:
                    symbol = "✓"  # Match
                else:
                    symbol = "-"  # Different
                
                print(f"{symbol:>12}", end="")
            print()
        
if __name__ == "__main__":
    compare_platforms()

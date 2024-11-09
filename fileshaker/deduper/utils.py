import hashlib
import os

def get_file_hash(file_path):
    """Calculate the MD5 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def find_duplicates(directory_path):
    """Find duplicate files in a directory by comparing file hashes."""
    files_by_hash = {}
    for root, _, files in os.walk(directory_path):
        for file_name in files:
            full_path = os.path.join(root, file_name)
            file_hash = get_file_hash(full_path)
            if file_hash in files_by_hash:
                files_by_hash[file_hash].append(full_path)
            else:
                files_by_hash[file_hash] = [full_path]
    # Return only entries with more than one file (duplicates)
    return {k: v for k, v in files_by_hash.items() if len(v) > 1}

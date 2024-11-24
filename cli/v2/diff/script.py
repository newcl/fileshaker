import os
import hashlib
import argparse
import json
import logging
from collections import defaultdict
from tqdm import tqdm

def setup_logging(log_level=logging.INFO):
    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

def get_files_with_size(folder_path):
    logging.info(f"Indexing files in {folder_path}")
    files_by_size = defaultdict(list)
    for root, dirs, files in os.walk(folder_path):
        for name in files:
            filepath = os.path.join(root, name)
            try:
                filesize = os.path.getsize(filepath)
                files_by_size[filesize].append(filepath)
            except OSError as e:
                logging.error(f"Error accessing {filepath}: {e}")
                continue
    return files_by_size

def compute_hash(file_path, hash_algo=hashlib.sha256, block_size=65536):
    hasher = hash_algo()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(block_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f"Error hashing {file_path}: {e}")
        return None

def compare_files(file1, file2, block_size=65536):
    try:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            for b1, b2 in zip(iter(lambda: f1.read(block_size), b''), iter(lambda: f2.read(block_size), b'')):
                if b1 != b2:
                    return False
            return True
    except Exception as e:
        logging.error(f"Error comparing {file1} and {file2}: {e}")
        return False

def find_unique_files(folder_a, folder_b):
    files_a = get_files_with_size(folder_a)
    files_b = get_files_with_size(folder_b)
    
    unique_to_a = set()
    unique_to_b = set()
    matched_files_a = set()
    matched_files_b = set()

    # Sizes present in both folders
    common_sizes = set(files_a.keys()).intersection(files_b.keys())
    
    # Process files with sizes present in both folders
    for size in tqdm(common_sizes, desc='Processing common file sizes'):
        files_list_a = files_a[size]
        files_list_b = files_b[size]

        # Compute hashes for files in folder A
        hashes_a = defaultdict(list)
        for file_path in files_list_a:
            file_hash = compute_hash(file_path)
            if file_hash:
                hashes_a[file_hash].append(file_path)

        # Compute hashes for files in folder B
        hashes_b = defaultdict(list)
        for file_path in files_list_b:
            file_hash = compute_hash(file_path)
            if file_hash:
                hashes_b[file_hash].append(file_path)

        # Compare files with matching hashes
        common_hashes = set(hashes_a.keys()).intersection(hashes_b.keys())

        for file_hash in common_hashes:
            files_with_hash_a = hashes_a[file_hash]
            files_with_hash_b = hashes_b[file_hash]

            for file_a in files_with_hash_a:
                match_found = False
                for file_b in files_with_hash_b:
                    if compare_files(file_a, file_b):
                        matched_files_a.add(file_a)
                        matched_files_b.add(file_b)
                        match_found = True
                        logging.debug(f"Match found: {file_a} and {file_b}")
                        break
                if not match_found:
                    unique_to_a.add(file_a)
            for file_b in files_with_hash_b:
                if file_b not in matched_files_b:
                    unique_to_b.add(file_b)

        # Files with unique hashes
        unique_hashes_a = set(hashes_a.keys()) - common_hashes
        unique_hashes_b = set(hashes_b.keys()) - common_hashes

        for file_hash in unique_hashes_a:
            unique_to_a.update(hashes_a[file_hash])
        for file_hash in unique_hashes_b:
            unique_to_b.update(hashes_b[file_hash])

    # Files with sizes unique to each folder
    unique_sizes_a = set(files_a.keys()) - common_sizes
    unique_sizes_b = set(files_b.keys()) - common_sizes

    for size in unique_sizes_a:
        unique_to_a.update(files_a[size])
    for size in unique_sizes_b:
        unique_to_b.update(files_b[size])

    return list(unique_to_a), list(unique_to_b)

def main():
    parser = argparse.ArgumentParser(description='Compare two folders and list unique files.')
    parser.add_argument('folder_a', help='Path to the first folder.')
    parser.add_argument('folder_b', help='Path to the second folder.')
    parser.add_argument('-o', '--output', default='unique_files.json', help='Path to the output JSON file.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity.')
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    folder_a = args.folder_a
    folder_b = args.folder_b
    output_file = args.output

    unique_files_a, unique_files_b = find_unique_files(folder_a, folder_b)
    
    result = {
        'unique_to_folder_a': unique_files_a,
        'unique_to_folder_b': unique_files_b
    }

    # Write results to JSON file
    try:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=4)
        logging.info(f"Results written to {output_file}")
    except Exception as e:
        logging.error(f"Error writing to {output_file}: {e}")
        return

    print(f"\nComparison complete. Results saved to {output_file}.")

if __name__ == '__main__':
    main()

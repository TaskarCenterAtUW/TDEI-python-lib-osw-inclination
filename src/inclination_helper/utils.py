import os
import uuid
import shutil
import zipfile


def get_unique_id() -> str:
    return uuid.uuid1().hex[0:24]

def unzip(zip_file: str, output: str):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(output)
        extracted_files = zip_ref.namelist()
        optional_files = ['nodes', 'edges', 'points']
        file_locations = {}
        full_paths = []  # To store full paths of all extracted files

        for extracted_file in extracted_files:
            if '__MACOSX' in extracted_file:
                continue

            # Add full path for all extracted files
            full_paths.append(os.path.join(output, extracted_file))

            # Check if file matches any of the optional files (nodes, edges, points)
            for optional_file in optional_files:
                if optional_file in extracted_file:
                    file_locations[optional_file] = os.path.join(output, extracted_file)

        return file_locations, full_paths


def clean_up(path, download_dir=None):
    if os.path.isfile(path):
        os.remove(path)
    else:
        shutil.rmtree(path, ignore_errors=True)


def create_zip(files, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
        for file in files:
            if not os.path.isdir(file):
                # Add each file to the zip file
                zip_file.write(file, os.path.basename(file))

    return zip_file_path




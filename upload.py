# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///

import os
import zipfile
import argparse
import requests

def create_zip(zip_path, files_to_include):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_name in files_to_include:
            file_path = "patched/"+file_name
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=file_name)
            else:
                print(f"Warning: {file_path} does not exist and will be skipped.")

def upload_to_discord(webhook_url, file_path):
    with open(file_path, 'rb') as f:
        response = requests.post(
            webhook_url,
            files={"file": (os.path.basename(file_path), f, "application/zip")},
        )
    if response.status_code == 204:
        print("Upload successful.")
    else:
        print(f"Failed to upload. Status code: {response.status_code}, Response: {response.text}")

def main():
    parser = argparse.ArgumentParser(description="Zip specific files and upload to a Discord webhook.")
    parser.add_argument("webhook_url", help="The Discord webhook URL.")
    args = parser.parse_args()

    # Define the files and destination zip path
    files = [
        "data/npcs/npcs.pak",
        "data/europe/npcs/npcs.pak"
    ]
    zip_output_path = "patched/npcs_patch.zip"

    create_zip(zip_output_path, files)
    upload_to_discord(args.webhook_url, zip_output_path)

if __name__ == "__main__":
    main()

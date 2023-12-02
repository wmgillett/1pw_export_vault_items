# export_vault_details.py
"""
Exports all items in a 1password vault to a CSV file
requires 1password CLI to be installed and configured
"""
import os
import subprocess
import json
import csv
import pyminizip
import getpass

from dotenv import load_dotenv
load_dotenv()
# from encrypt_file import encrypt_csv

def run_command(command):
    """
    Runs a command in the shell and returns the output
    Args:
        command (list of str): Command to run as list of arguments
    Returns:
        str: Output of the command
    Raises:
        RuntimeError: If command execution fails
    """
    try:
        command_list = command.split()
        result = subprocess.run(command_list, capture_output=True, text=True, check=True)
       
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise RuntimeError(f'Command failed: {e}') from e

def get_login_items(vault):
    """
    Gets login items in a vault
    Args:
        vault (str): Name of the vault
    Returns:
        dict: JSON output of the command
    """
    command = f"op item list --categories Login --vault {vault} --format=json"
    output = run_command(command)
    try:
        output_json = json.loads(output)
        return output_json
    except json.JSONDecodeError as e:
        print(e)
        return {}

def get_vault_items(vault='', category=''):
    """
    Gets all items in a vault
    Args:
        vault (str): Name of the vault
    Returns:
        dict: JSON output of the command
    """
    if vault == '':
        if category == '':
            command = "op item list --format=json"
    else:
        if category == '':
            command = f"op item list --vault {vault} --format=json"
        else:
            command = f"op item list --categories {category} --vault {vault} --format=json"
    output = run_command(command)
    try:
        output_json = json.loads(output)
        return output_json
    except json.JSONDecodeError as e:
        print(e)
        return {}

def get_item_details(item_id):
    """
    Gets the username and password for an item
    Args:
        item_id (str): ID of the item 
    Returns:
        dict: Dictionary containing the username and password
    """
    command = f"op item get {item_id} --fields username,password"
    output = run_command(command)
    if output:
        username, password = output.strip().split(',', 1)
        return {'username': username, 'password': password}
    else:
        return {'username': '', 'password': ''}

def encrypt_file(input_file, output_file, password):
    """
    Encrypts a CSV file into a ZIP file using the given password
    Args:
        csv_file (str): Path to the CSV file
        zip_file (str): Path to the ZIP file
        password (str): Password to encrypt the ZIP file with
    Returns:
        bool: True if the file was successfully encrypted, False otherwise

    """
    compression_level = 5  # Compression level, from 0 to 9
    try:
        pyminizip.compress(input_file, None, output_file, password, compression_level)

        return True
    except (IOError, FileNotFoundError, PermissionError) as e:
        print(e)
        return False

def main():
    """
    Gets all items in a vault and writes them to a CSV file
    """
    vault_name = "Actualizers"  # Replace with your vault name
    category = "Login" # Replace with your category
    # run with blank vault_name to get all items
    # vault_name = ''
    items = get_vault_items(vault_name, category)
    msg = f"Found {len(items)} items in vault {vault_name}"
    print(msg)
    prefix1 = vault_name if vault_name else "all_vaults"
    prefix2 = category if category else "all_categories"
    prefix = f"{prefix1}_{prefix2}"
    output_filename = f"{prefix}_passwords.csv"
    print(f"Writing items to {output_filename}")
    if output_filename:
        with open(output_filename, "w", encoding='utf-8',newline="") as file:
            
            writer = csv.writer(file)
            writer.writerow(["Vault", "Username", "Password", "Category",
                             "Title", "additional_info", "url1", "urls", "item_json"])
            count = 0
            total = len(items)
            for item in items:
                # ic(item)
                count += 1
                details = get_item_details(item['id'])
                category = item.get('category','')
                title = item.get('title','')
                vault_name = item.get('vault', {}).get('name','')
                msg = f"[{vault_name}]: processing item #{count}/{total} {item['category']} {item['title']}"
                print(msg)
                urls = item.get('urls', {})
                if urls:
                    url1 = urls[0].get('href','')
                else:
                    url1 = ''
                additional_info = item.get('additional_information','')
                writer.writerow([vault_name, details.get('username', ''), details.get('password', ''),category, title, additional_info, url1, urls, item])
        zip_filename = "encrypted_"+output_filename+".zip"
        password = os.getenv('DEFAULT_PASSWORD')
        if not password: # prompt for password
            password = getpass.getpass("Enter password to encrypt file: ")
        encrypted = encrypt_file(output_filename, zip_filename, password)
        if (encrypted):
            print(f"Passwords exported and stored in encrypted zip file: {zip_filename}")
            os.remove(output_filename)
        else:
            print(f"File not encrypted: {zip_filename}")
    else:
        print("No output filename found in .env file")

if __name__ == "__main__":
    main()

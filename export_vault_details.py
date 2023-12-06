# export_vault_details.py
"""
Exports all items in a 1password vault to a CSV file
requires 1password CLI to be installed and configured
"""
import os
import subprocess
import json
import csv
import getpass
import shlex  # For safely handling command arguments
import pyminizip
from icecream import ic

from dotenv import load_dotenv
load_dotenv()

# set runtime parameters from envionment variables
skip_private_vault = os.getenv('SKIP_PRIVATE_VAULT', 'false').lower() == 'true'
summary_only = os.getenv('SUMMARY_ONLY', 'false').lower() == 'true'
print(f"skip_private_vault: {skip_private_vault}")
def run_command(command):
    """
    Runs a command in the shell and returns the output
    Args:
        command (list of str): Command to run as list of arguments
    Returns:
        str: Output of the command
        if command fails, returns empty string
    """
    try:
        command_list = command.split()
        result = subprocess.run(command_list, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e.stderr.splitlines()[0]}")
        return ""

def filter_vault_items(items, exclude_vaults=None):
    """
    Filters out items from a vault
    Args:
        items (list of dict): List of items
        filters (list of str): List of filters to apply
    Returns:
        list of dict: Filtered list of items
    """
    if exclude_vaults is None:
        exclude_vaults = ['Private']
    filtered_items = []
    print(f"filters: {exclude_vaults}")
    print(f"items before filtering: {len(items)}")
    for item in items:
        # ic(item)
        if item.get('vault', {}).get('name','') not in exclude_vaults:
            filtered_items.append(item)
    print(f"items after filtering: {len(filtered_items)}")
    return filtered_items

def get_vault_items(vault='', category=''):
    """
    Gets all items in a vault
    Args:
        vault (str): Name of the vault
        category (str): category filter
    Returns:
        dict: JSON output of the command
    """
    command = "op item list --format=json"


    if category:
        if category.lower() in ['secure_note', "secure_notes",'securenote', 'securenotes']:
            command += " --categories SecureNote"
        elif category.lower() in ['wireless_router', "wireless_routers",'wirelessrouters']:
            command += " --categories WirelessRouter"
        elif category.lower() in ['email_account', "email_accounts",'emailaccounts']:
            command += " --categories EmailAccount"
        elif category.lower() in ['api_credential', "api_credentials",'apicredentials']:
            command += " --categories ApiCredential"
        elif category.lower() in ['software_license', "software_licenses",'softwarelicenses']:
            command += " --categories SoftwareLicense"
        else:
            ic(category)
            ic({shlex.quote(category)})
            command += f" --categories {shlex.quote(category)}"
    if vault:
        if ' ' not in vault and not vault.isalnum():
            vault = shlex.quote(vault)
        command += f" --vault {vault}"
    output = run_command(command)
    if not output:
        return []
    try:
        output_json = json.loads(output)
        if skip_private_vault:
            exclude_vaults=['Private']
            output_json = filter_vault_items(output_json,exclude_vaults)
        return output_json
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []

def convert_multi_line_text(text):
    """
    Converts multi-line text into a single line
    Args:
        text (str): Multi-line text
    Returns:
        str: Single line text
    """
    # Split the text into lines and strip extra whitespace
    lines = [line.strip() for line in text.split('\n')]
    # Concatenate the lines into a single string, separated by a space
    processed_text = ' '.join(lines)
    return processed_text

def get_fields_details(item_details, purpose_list, label_list):
    """
    Extracts specified fields based on their purpose from the item details
    Args:
        item_details (dict): Details of the item.
        purpose_list (list): List of purpose values to extract.
        label_list (list): List of label values to extract.
    Returns:
        dict: Dictionary containing the requested fields and their values.
    """
    extracted_data = {}

    for field in item_details.get('fields', []):
        if field.get('purpose') in purpose_list:
            extracted_data[field['purpose'].lower()] = field.get('value', '')
            if field.get('purpose') == 'NOTES':
                extracted_data['notes'] = convert_multi_line_text(extracted_data['notes'])
                # ic(extracted_data['notes'][:50])
        if field.get('label') in label_list: # for example, '2FA Secret Key'
            extracted_data[field['label'].lower()] = field.get('value', '')
            # append label:value to notes
            extracted_data['notes'] += f" [{field['label']}]: {field.get('value', '')}"
            extracted_data['notes'] = convert_multi_line_text(extracted_data['notes'])
    return extracted_data

def get_item_details(item_id, category=''):
    """
    Gets the username and password for an item
    Args:
        item_id (str): ID of the item 
        category (str): Category of the item
    Returns:
        dict: Dictionary containing the username and password
    """
    category = category.lower()
    command = f"op item get {item_id} --format=json"
    output = run_command(command)

    if not output:
        return {}

    # Parse the JSON output
    try:
        item_details = json.loads(output)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}
    # specify purpose and label list based on category
    purpose_list = []
    label_list = []
    if category == "login":
        purpose_list = ['USERNAME', 'PASSWORD','NOTES']
    elif category in ["password", "server"]:
        purpose_list = ['USERNAME', 'PASSWORD','NOTES']
    elif category in ['secure_note', "wireless_router", "database"]:
        purpose_list = ['NOTES']
    elif category in ["email_account"]:
        purpose_list = ['USERNAME', 'PASSWORD','NOTES']
    elif category in ["api_credential"]:
        purpose_list = ['USERNAME', 'PASSWORD','NOTES']
        label_list = ['api key', 'api secret']
    elif category in ["software_license"]:
        purpose_list = ['USERNAME', 'PASSWORD','NOTES']
        label_list = ['version', 'license key']
    elif category in ["identity"]:
        purpose_list = ['USERNAME', 'PASSWORD','NOTES']
    if not purpose_list:
        print(f"Unknown category: {category}")
        return {}
    fields_details = get_fields_details(item_details, purpose_list, label_list)
    # store the entire item details in a separate field
    fields_details['item_details'] = item_details
    return fields_details

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

def count_items_by_category(items):
    """
    Counts the number of items in each category.
    Args:
        items (list): List of item dictionaries.
    Returns:
        dict: Dictionary with categories as keys and counts as values.
    """
    category_counts = {}

    for item in items:
         # Default to 'Unknown' if category is not present
        category = item.get('category', 'Unknown')
        category_counts[category] = category_counts.get(category, 0) + 1

    return category_counts

def count_items_by_vault_name(items):
    """
    Counts the number of items in each vault.
    Args:
        items (list): List of item dictionaries.
    Returns:
        dict: Dictionary with vault names as keys and counts as values.
    """
    vault_counts = {}

    for item in items:
        vault_name = item.get('vault', {}).get('name', 'Unknown')
        vault_counts[vault_name] = vault_counts.get(vault_name, 0) + 1

    return vault_counts





def main():
    """
    Gets all items in a vault and writes them to a CSV file
    """
    vault_name = os.getenv("VAULT_TO_EXPORT","").strip()
    category = os.getenv("CATEGORY_TO_EXPORT","").strip()
    items = get_vault_items(vault_name, category)
    if not items:
        print("No items found")
        return
    msg = f"Found {len(items)} items in vault {vault_name}"
    print(msg)
    if not summary_only:
        prefix1 = vault_name if vault_name else "all_vaults"
        prefix2 = category if category else "all_categories"
        prefix = f"{prefix1}_{prefix2}"
        output_filename = f"{prefix}_passwords.csv"
        print(f"Writing items to {output_filename}")
        if output_filename:
            with open(output_filename, "w", encoding='utf-8',newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Vault", "Username", "Password", "Category",
                                "Title", "additional_info", "url1","note_text",
                                "urls", "item_json","item_details_json"])
                count = 0
                total = len(items)
                for item in items:
                    # ic(item)
                    count += 1
                    category = item.get('category','')
                    vault_name = item.get('vault', {}).get('name','')
                    msg = f"[{vault_name}]: processing item #{count}/{total} {item['category']} {item['title']}"
                    print(msg)
                    title = item.get('title','')
                    # ic(item)
                    urls = item.get('urls', {})
                    if urls:
                        url1 = urls[0].get('href','')
                    else:
                        url1 = ''
                    additional_info = item.get('additional_information','')
                    details = get_item_details(item['id'], category)
                    writer.writerow([vault_name,
                                     details.get('username', ''),
                                     details.get('password', ''),
                                     category, title, additional_info,
                                     url1, details.get('notes', ''),
                                     urls, item,
                                     details.get('item_details', '')])
            zip_filename = "encrypted_"+output_filename+".zip"
            password = os.getenv('DEFAULT_PASSWORD')
            if not password: # prompt for password
                password = getpass.getpass("Enter password to encrypt file: ")
            encrypted = encrypt_file(output_filename, zip_filename, password)
            if encrypted:
                print(f"Passwords exported and stored in encrypted zip file: {zip_filename}")
                # os.remove(output_filename)
            else:
                print(f"File not encrypted: {zip_filename}")
        else:
            print("No output filename found in .env file")
    else:
        category_counts = count_items_by_category(items)
        for category, count in category_counts.items():
            print(f"Category: {category}, Count: {count}")
        vault_counts = count_items_by_vault_name(items)
        for vault_name, count in vault_counts.items():
            print(f"Vault Name: {vault_name}, Count: {count}")


        print("Skipping writing items to CSV file")


if __name__ == "__main__":
    main()

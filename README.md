# 1PW Export Vault Items

1PW Export Vault Items is a Python script that exports all items from a specified 1Password vault to a CSV file. It leverages the 1Password Command Line Interface (CLI) to access and retrieve vault contents. The script also provides the option to exclude certain vaults (like the private vault) during the export process and encrypts the output CSV file for enhanced security.

This script expanded the default exports in 1Password.

## Requirements
- Python 3.x
- [1Password CLI](https://marketplace.visualstudio.com/items?itemName=1Password.op-vscode) installed and configured on your system 
- Additional Python libraries: subprocess, json, csv, pyminizip, getpass
- .env file for environment variables

## Features
- Exports all items from the specified 1Password vault or all vaults in an account.
- Provides 9 output fields (Vault, category, title, username, password, primary url, urls (json), item details (json))
- Optionally filters items by category.
- Provides an option to exclude private vaults from the export.
- Encrypts the output CSV file using a specified password.
- Logs detailed information during the export process.
  
## Security
The script handles sensitive data and ensures that:
- Password inputs are securely handled using getpass.
- Temporary CSV files are securely deleted after encryption.
- The encryption of output files is done using pyminizip for added security.


## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/wmgillett/1pw_export_vault_items
   cd 1pw_export_vault_items
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```
   [1password vscode extention](https://marketplace.visualstudio.com/items?itemName=1Password.op-vscode)

3. Setup .env file from .env.example
   ```bash
   cp .env.example .env
   nano .env
   ```
 - .env settings
   ```
   DEFAULT_PASSWORD=123456  # leave blank to define dynamically
   SKIP_PRIVATE_VAULT=true  # set to True to filter out Private vault from output, False to leave in.
   VAULT_TO_EXPORT=       # set to specific vault for export or leave empty to export all vaults
   CATEGORY_TO_EXPORT=    # set to specific category (e.g. Login) or leave blank to export all categories
   ```
## Usage
1) Define vault and category for export in .env

2) Run application from command line
   ```bash
   python app.py
   ```
3) Access output file stored in encrypted zipfile
   default names
   ```
   # zip file
   encypted_[vault]_[category]_passwords.csv.zip

   # csv file
   [vault]_[category]_passwords.csv
   ```
   ### CSV Output format
      | Column Name     | Format | Description                                      |
      |-----------------|--------|--------------------------------------------------|
      | Vault           | String | The name of the 1Password vault.                 |
      | Username        | String | The username associated with the item.           |
      | Password        | String | The password associated with the item.           |
      | Category        | String | The category of the item (e.g., Login, Secure Note). |
      | Title           | String | The title of the item.                           |
      | additional_info | String | Additional information associated with the item. |
      | url1            | String | The primary URL associated with the item, if any. |
      | urls            | JSON   | A JSON array of all URLs associated with the item. |
      | item_json       | JSON   | A JSON representation of the entire item.        |


## Contributing
- Contributions to improve export_vault_details.py are welcome. Please ensure that your code adheres to the project's coding standards and includes appropriate tests.

## License
 - MIT License


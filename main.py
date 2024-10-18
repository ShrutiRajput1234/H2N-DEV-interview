import os
import xml.etree.ElementTree as ET
import json
import logging
import glob
import sqlite3

# Setup logging
log_file_path = 'process.log'
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s: %(message)s')

# Paths to XML files
xml_folder_path = r'xml-files'  # Path to the folder where your XML files are located

# Output JSON folder
json_folder_path = r'json-output'
os.makedirs(json_folder_path, exist_ok=True)

# SQLite Database setup
db_path = 'orders.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables for raw XML data and processed JSON data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS raw_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        xml_content TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        json_content TEXT
    )
''')
conn.commit()

# Function to store raw XML content in SQLite
def store_raw_data(file_name, xml_content):
    cursor.execute('INSERT INTO raw_data (file_name, xml_content) VALUES (?, ?)', (file_name, xml_content))
    conn.commit()

# Function to store processed JSON content in SQLite
def store_json_data(file_name, json_content):
    cursor.execute('INSERT INTO processed_data (file_name, json_content) VALUES (?, ?)', (file_name, json_content))
    conn.commit()

# Function to parse XML file and convert to JSON
def process_xml_file(file_path):
    try:
        with open(file_path, 'r') as file:
            xml_content = file.read()
            store_raw_data(os.path.basename(file_path), xml_content)  # Store raw XML data

        tree = ET.parse(file_path)
        root = tree.getroot()

        # Extract relevant fields
        order_data = {}
        order_data['OrderID'] = root.findtext('OrderID', default='N/A')
        customer_element = root.find('Customer')
        if customer_element is not None:
            order_data['Customer'] = {
                'CustomerID': customer_element.findtext('CustomerID', default='N/A'),
                'Name': customer_element.findtext('Name', default='N/A')
            }
        else:
            logging.error(f"Skipped {os.path.basename(file_path)} - Missing <Customer> element.")
            return None
        
        products = []
        products_element = root.find('Products')
        if products_element is not None:
            for product in products_element.findall('Product'):
                products.append({
                    'ProductID': product.findtext('ProductID', default='N/A'),
                    'Quantity': product.findtext('Quantity', default='N/A')
                })
        order_data['Products'] = products

        return order_data

    except ET.ParseError as e:
        logging.error(f"Parsing error in {os.path.basename(file_path)} - {e}.")
        return None
    except Exception as e:
        logging.error(f"Unknown error in {os.path.basename(file_path)} - {e}.")
        return None

# Function to retry processing a file up to 3 times
def process_with_retry(file_path, retries=3):
    for attempt in range(retries):
        json_data = process_xml_file(file_path)
        if json_data:
            return json_data
        logging.warning(f"Retrying {os.path.basename(file_path)} ({attempt + 1}/{retries})")
    logging.error(f"Failed to process {os.path.basename(file_path)} after {retries} retries.")
    return None

# Iterate through all XML files and process them
xml_files = glob.glob(os.path.join(xml_folder_path, '*.xml'))

for xml_file in xml_files:
    json_data = process_with_retry(xml_file)
    if json_data:
        # Store JSON data in SQLite
        store_json_data(os.path.basename(xml_file), json.dumps(json_data))

        # Save JSON to a file
        json_file_path = os.path.join(json_folder_path, os.path.basename(xml_file).replace('.xml', '.json'))
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

# After processing, close the SQLite connection
conn.close()

# After the script is done, you can check the 'process.log' file for error and status logging.

import sqlite3

# Connect to the database
conn = sqlite3.connect('orders.db')
cursor = conn.cursor()

# Query and display raw XML data
print("Raw XML Data:")
cursor.execute("SELECT * FROM raw_data")
rows = cursor.fetchall()
for row in rows:
    print(row)

# Query and display processed JSON data
print("\nProcessed JSON Data:")
cursor.execute("SELECT * FROM processed_data")
rows = cursor.fetchall()
for row in rows:
    print(row)

# Close the connection
conn.close()

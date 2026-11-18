import mysql.connector
from config import config

connection = None
cursor = None

try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    cursor.execute('SELECT company_id, company_name, industry, city FROM companies')
    companies = cursor.fetchall()

    print('=== All Companies ===')
    print(f'Total companies: {len(companies)}')
    print()

    for company_id, name, industry, city in companies:
        print(f'ID: {company_id} | {name} | {industry} | {city}')

except mysql.connector.Error as error:
    print(f'Error: {error}')

finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()
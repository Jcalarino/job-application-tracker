import mysql.connector
from config import config

connection = None
cursor = None

try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    company_name = 'Python Solutions LLC'

    cursor.execute('SELECT * FROM companies WHERE company_name = %s', (company_name,))
    to_delete = cursor.fetchall()

    if to_delete:
        print(f'About to delete: {to_delete}')

        delete_query = 'DELETE FROM companies WHERE company_name = %s'
        cursor.execute(delete_query, (company_name,))
        connection.commit()

        print(f'Deleted {cursor.rowcount} company(ies)')
    else:
        print('Company not found.')

except mysql.connector.Error as error:
    print(f'Error: {error}')
    if connection:
        connection.rollback()

finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()
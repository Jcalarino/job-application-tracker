import mysql.connector
from config import config

connection = None
cursor = None

try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    new_company = {
        'name': 'Python Solutions LLC',
        'industry': 'Software Development',
        'website': 'www.pythonsolutions.com',
        'city': 'Miami',
        'state': 'Florida'
    }

    insert_query = '''
        INSERT INTO companies (company_name, industry, website, city, state)
        VALUES (%s, %s, %s, %s, %s)
    '''

    values = (new_company['name'], new_company['industry'],
              new_company['website'], new_company['city'], new_company['state'])

    cursor.execute(insert_query, values)

    # Without this line, the insert is lost when the connection closes
    connection.commit()

    print('Company added successfully!')
    print(f'New company ID: {cursor.lastrowid}')

except mysql.connector.Error as error:
    print(f'Error: {error}')
    if connection:
        connection.rollback()

finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()
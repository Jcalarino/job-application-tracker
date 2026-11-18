import mysql.connector
from config import config

connection = None
cursor = None

try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    application_id = 1
    new_status = 'Offer Accepted'

    update_query = '''
        UPDATE applications
        SET status = %s
        WHERE application_id = %s
    '''

    cursor.execute(update_query, (new_status, application_id))
    connection.commit()

    if cursor.rowcount > 0:
        print(f'Updated {cursor.rowcount} application(s)')
        print(f'Application {application_id} status changed to: {new_status}')
    else:
        print('No applications were updated. Check the ID.')

except mysql.connector.Error as error:
    print(f'Error: {error}')
    if connection:
        connection.rollback()

finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()
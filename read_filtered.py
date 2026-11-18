import mysql.connector
from config import config

connection = None
cursor = None

try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    min_salary = 70000

    query = 'SELECT job_title, salary_min, salary_max FROM jobs WHERE salary_min >= %s'
    cursor.execute(query, (min_salary,))

    jobs = cursor.fetchall()

    print(f'=== Jobs with salary >= ${min_salary:,} ===')
    print(f'Found {len(jobs)} jobs')
    print()

    for title, sal_min, sal_max in jobs:
        print(f'{title}: ${sal_min:,.0f} - ${sal_max:,.0f}')

except mysql.connector.Error as error:
    print(f'Error: {error}')

finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()
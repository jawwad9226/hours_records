import datetime
import mysql.connector
import os

def write_to_db(date, hours):
    try:
        # Establish a connection to the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="pass123",
            database="abd-db"
        )
        
        cursor = conn.cursor()
        
        # Insert data into the working_hourse table
        insert_query = "INSERT INTO `working_hourse` (`date_time`, `hourse`) VALUES (%s, %s)"
        cursor.execute(insert_query, (date, hours))
        conn.commit()
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"An error occurred: {e}")

def read_from_db():
    try:
        # Establish a connection to the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="pass123",
            database="abd-db"
        )
        
        cursor = conn.cursor()
        
        # Select and fetch data from the working_hourse table
        select_query = "SELECT * FROM `working_hourse`"
        cursor.execute(select_query)
        rows = cursor.fetchall()
        
        row_count = len(rows)
        hours = sum(int(row[2]) for row in rows)  # Assuming `hourse` is the third column
        
        cursor.close()
        conn.close()
        
        return row_count, hours
    except mysql.connector.Error as e:
        print(f"An error occurred: {e}")
        return 0, 0

def print_table():
    try:
        # Establish a connection to the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="pass123",
            database="abd-db"
        )
        
        cursor = conn.cursor()
        
        # Select all data from the working_hourse table
        select_query = "SELECT * FROM `working_hourse`"
        cursor.execute(select_query)
        rows = cursor.fetchall()
        
        # Print the table header
        print(f"{'days '} {'Date Time':<20} {'Hours':<10}")
        print("-" * 30)
        
        # Print each row in the table
        for row in rows:
            # Print the entire row for debugging
            #print(f"DEBUG: Row data: {row}")  # Debugging line
            
            # Assuming row[0] is sr-no, row[1] is date_time, and row[2] is hourse
            day= row[0]
            date_time = row[1]
            hourse = int(row[2])  # Convert hourse to int to remove leading zeros
            
            # Print formatted output
            print(f"{day:<6}{date_time.strftime('%Y-%m-%d %H:%M:%S'):<20} {hourse:<10}")  # Format date_time and hourse
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"An error occurred: {e}")

while True:
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    while True:
        try:
            hours = int(input('Enter today\'s working hours and press enter: '))
            if hours < 0:
                print("Please enter a non-negative integer for hours.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter an integer.")

    write_to_db(current_time, hours)
    print('Recorded', hours, 'at', current_time)

    total_days, total_hours = read_from_db()
    print(f'Your total days are {total_days} and total hours are {total_hours}')

    if input("Do you want to see the working hours table? (yes/no): ").lower() == 'yes':
        print_table()

    if input("Do you want to continue? (yes/no): ").lower() != 'yes':
        break
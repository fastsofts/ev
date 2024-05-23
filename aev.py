import sqlite3
from datetime import datetime

# Database setup with context manager
def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return None

# Function to create tables
def create_tables(conn):
    with conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL)''')

        conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
                        booking_id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        station_id INTEGER NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(user_id))''')

        conn.execute('''CREATE TABLE IF NOT EXISTS negotiations (
                        negotiation_id INTEGER PRIMARY KEY,
                        requester_id INTEGER NOT NULL,
                        responder_id INTEGER NOT NULL,
                        original_booking_id INTEGER NOT NULL,
                        proposed_reward REAL NOT NULL,
                        status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'rejected')),
                        FOREIGN KEY(requester_id) REFERENCES users(user_id),
                        FOREIGN KEY(responder_id) REFERENCES users(user_id),
                        FOREIGN KEY(original_booking_id) REFERENCES bookings(booking_id))''')

# Function to add a new user
def add_user(conn, name):
    with conn:
        conn.execute('INSERT INTO users (name) VALUES (?)', (name,))
        print(f"{name} added")

# Function to book a charging station
def book_station(conn, user_id, station_id, start_time, end_time):
    with conn:
        if is_available(conn, station_id, start_time, end_time):
            conn.execute('INSERT INTO bookings (user_id, station_id, start_time, end_time) VALUES (?, ?, ?, ?)',
                         (user_id, station_id, start_time, end_time))
            print(f"Station {station_id} booked by user {user_id} from {start_time} to {end_time}")
        else:
            print(f"Station {station_id} is not available from {start_time} to {end_time}")

# Function to check availability of a charging station
def is_available(conn, station_id, start_time, end_time):
    cur = conn.cursor()
    cur.execute('''SELECT * FROM bookings WHERE station_id = ? AND 
                   (start_time < ? AND end_time > ?)''', (station_id, end_time, start_time))
    return len(cur.fetchall()) == 0

# Function to get user's current bookings
def get_user_bookings(conn, user_id):
    cur = conn.cursor()
    cur.execute('SELECT * FROM bookings WHERE user_id = ?', (user_id,))
    return cur.fetchall()

# Function to initiate a negotiation
def initiate_negotiation(conn, requester_id, responder_id, booking_id, reward):
    with conn:
        conn.execute('''INSERT INTO negotiations (requester_id, responder_id, original_booking_id, proposed_reward, status)
                        VALUES (?, ?, ?, ?, 'pending')''', (requester_id, responder_id, booking_id, reward))
        print(f"Negotiation initiated by user {requester_id} with user {responder_id} for booking {booking_id} with proposed reward {reward}")

# Function to respond to a negotiation
def respond_negotiation(conn, negotiation_id, response):
    with conn:
        conn.execute('UPDATE negotiations SET status = ? WHERE negotiation_id = ?', (response, negotiation_id))
        if response == 'accepted':
            cur = conn.cursor()
            cur.execute('SELECT original_booking_id FROM negotiations WHERE negotiation_id = ?', (negotiation_id,))
            booking_id = cur.fetchone()[0]
            conn.execute('UPDATE bookings SET user_id = (SELECT requester_id FROM negotiations WHERE negotiation_id = ?) WHERE booking_id = ?', 
                         (negotiation_id, booking_id))
        print(f"Negotiation {negotiation_id} responded with {response}")

# Function to calculate a simple reward based on time duration
def calculate_reward(start_time, end_time):
    duration = (datetime.strptime(end_time, '%Y-%m-%d %H:%M') - datetime.strptime(start_time, '%Y-%m-%d %H:%M')).total_seconds() / 3600
    return duration * 10  # $10 per hour

# Example usage
def main():
    database = "acharging_stations.db"
    conn = create_connection(database)
    
    if conn is not None:
        create_tables(conn)
        
        add_user(conn, 'Alice')
        add_user(conn, 'Bob')

        # Check availability and book a station
        if is_available(conn, 1, '2024-05-24 10:00', '2024-05-24 12:00'):
            book_station(conn, 1, 1, '2024-05-24 10:00', '2024-05-24 12:00')
        
        # Initiate and respond to a negotiation
        reward = calculate_reward('2024-05-24 10:00', '2024-05-24 12:00')
        initiate_negotiation(conn, 2, 1, 1, reward)
        respond_negotiation(conn, 1, 'accepted')

        # Print user bookings
        print(get_user_bookings(conn, 1))
        print(get_user_bookings(conn, 2))
        
        conn.close()
    else:
        print("Error! Cannot create the database connection.")

if __name__ == '__main__':
    main()
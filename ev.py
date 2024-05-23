import sqlite3
from datetime import datetime

# Database setup
conn = sqlite3.connect('charging_stations.db')
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS users (
             user_id INTEGER PRIMARY KEY,
             name TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS bookings (
             booking_id INTEGER PRIMARY KEY,
             user_id INTEGER,
             station_id INTEGER,
             start_time TEXT,
             end_time TEXT,
             FOREIGN KEY(user_id) REFERENCES users(user_id))''')

c.execute('''CREATE TABLE IF NOT EXISTS negotiations (
             negotiation_id INTEGER PRIMARY KEY,
             requester_id INTEGER,
             responder_id INTEGER,
             original_booking_id INTEGER,
             proposed_reward REAL,
             status TEXT,
             FOREIGN KEY(requester_id) REFERENCES users(user_id),
             FOREIGN KEY(responder_id) REFERENCES users(user_id),
             FOREIGN KEY(original_booking_id) REFERENCES bookings(booking_id))''')

# Add a user
def add_user(name):
    c.execute('INSERT INTO users (name) VALUES (?)', (name,))
    conn.commit()
    print(f"{name} added")

# Book a charging station
def book_station(user_id, station_id, start_time, end_time):
    c.execute('INSERT INTO bookings (user_id, station_id, start_time, end_time) VALUES (?, ?, ?, ?)',
              (user_id, station_id, start_time, end_time))
    conn.commit()
    print(f"Station {station_id} booked by user {user_id} from {start_time} to {end_time}")

# Check availability
def is_available(station_id, start_time, end_time):
    c.execute('''SELECT * FROM bookings WHERE station_id = ? AND 
                 (start_time < ? AND end_time > ?)''', (station_id, end_time, start_time))
    return len(c.fetchall()) == 0

# Get user's current booking
def get_user_booking(user_id):
    c.execute('SELECT * FROM bookings WHERE user_id = ?', (user_id,))
    return c.fetchall()

# Initiate a negotiation
def initiate_negotiation(requester_id, responder_id, booking_id, reward):
    c.execute('''INSERT INTO negotiations (requester_id, responder_id, original_booking_id, proposed_reward, status)
                 VALUES (?, ?, ?, ?, 'pending')''', (requester_id, responder_id, booking_id, reward))
    conn.commit()
    print(f"Negotiation initiated by user {requester_id} with user {responder_id} for booking {booking_id} with proposed reward {reward}")

# Respond to a negotiation
def respond_negotiation(negotiation_id, response):
    c.execute('UPDATE negotiations SET status = ? WHERE negotiation_id = ?', (response, negotiation_id))
    if response == 'accepted':
        c.execute('SELECT original_booking_id FROM negotiations WHERE negotiation_id = ?', (negotiation_id,))
        booking_id = c.fetchone()[0]
        c.execute('UPDATE bookings SET user_id = (SELECT requester_id FROM negotiations WHERE negotiation_id = ?) WHERE booking_id = ?', 
                  (negotiation_id, booking_id))
    conn.commit()
    print(f"Negotiation {negotiation_id} responded with {response}")

# Calculate fair reward (simple example)
def calculate_reward(start_time, end_time):
    # Example: reward based on time difference
    duration = (datetime.strptime(end_time, '%Y-%m-%d %H:%M') - datetime.strptime(start_time, '%Y-%m-%d %H:%M')).total_seconds() / 3600
    return duration * 10  # $10 per hour

# Example usage
add_user('Alice')
add_user('Bob')

if is_available(1, '2024-05-24 10:00', '2024-05-24 12:00'):
    book_station(1, 1, '2024-05-24 10:00', '2024-05-24 12:00')

reward = calculate_reward('2024-05-24 10:00', '2024-05-24 12:00')
initiate_negotiation(2, 1, 1, reward)
respond_negotiation(1, 'accepted')

# Close the database connection
conn.close()
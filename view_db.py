import sqlite3
from tabulate import tabulate  # Optional: to display data nicely in table format

# ---------------------------
# Function to view users
# ---------------------------
def view_users():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT id, firstname, lastname, email FROM users")
    users = c.fetchall()
    
    if users:
        print("\n===== Users Table =====\n")
        print(tabulate([tuple(u) for u in users], headers=users[0].keys(), tablefmt="grid"))
    else:
        print("No users found in the database.")
    
    conn.close()

# ---------------------------
# Helper function to check if column exists
# ---------------------------
def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

# ---------------------------
# Function to view predictions
# ---------------------------
def view_predictions():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check which columns exist
    has_year = column_exists(c, "predictions", "year")
    has_timestamp = column_exists(c, "predictions", "timestamp")
    
    # Build query based on available columns
    select_fields = ["p.id", "u.email"]
    
    if has_year:
        select_fields.append("p.year")
    else:
        print("Note: Year column not found in database.")
    
    select_fields.extend([
        "p.crop", "p.season", "p.state", "p.area", "p.production",
        "p.annual_rainfall", "p.fertilizer", "p.pesticide", "p.yield_value"
    ])
    
    if has_timestamp:
        select_fields.append("p.timestamp")
    else:
        print("Note: Timestamp column not found in database.")
    
    # Build the query
    query = f"""
    SELECT {', '.join(select_fields)}
    FROM predictions p
    JOIN users u ON p.user_id = u.id
    """
    
    # Add ORDER BY only if timestamp exists
    if has_timestamp:
        query += "ORDER BY p.timestamp DESC"
    else:
        query += "ORDER BY p.id DESC"
    
    try:
        c.execute(query)
        predictions = c.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Error querying predictions: {e}")
        predictions = []
    
    if predictions:
        print("\n===== Predictions Table =====\n")
        print(tabulate([tuple(p) for p in predictions], headers=predictions[0].keys(), tablefmt="grid"))
    else:
        print("No predictions found in the database.")
    
    conn.close()

# ---------------------------
# Function to view user sessions
# ---------------------------
def view_sessions():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = """
    SELECT us.id, u.firstname || ' ' || u.lastname as user_name, u.email, 
           us.login_time, us.logout_time,
           CASE WHEN us.logout_time IS NULL THEN 'Active' ELSE 'Completed' END as status
    FROM user_sessions us
    JOIN users u ON us.user_id = u.id
    ORDER BY us.login_time DESC
    """
    c.execute(query)
    sessions = c.fetchall()
    
    if sessions:
        print("\n===== User Sessions Table =====\n")
        print(tabulate([tuple(s) for s in sessions], headers=sessions[0].keys(), tablefmt="grid"))
    else:
        print("No sessions found in the database.")
    
    conn.close()

# ---------------------------
# Function to view users with statistics
# ---------------------------
def view_users_with_stats():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = """
    SELECT 
        u.id,
        u.firstname || ' ' || u.lastname as name,
        u.email,
        COUNT(DISTINCT us.id) as visit_count,
        COUNT(DISTINCT p.id) as prediction_count,
        MAX(us.login_time) as last_login
    FROM users u
    LEFT JOIN user_sessions us ON u.id = us.user_id
    LEFT JOIN predictions p ON u.id = p.user_id
    GROUP BY u.id, u.firstname, u.lastname, u.email
    ORDER BY u.id
    """
    c.execute(query)
    users = c.fetchall()
    
    if users:
        print("\n===== Users with Statistics =====\n")
        print(tabulate([tuple(u) for u in users], headers=users[0].keys(), tablefmt="grid"))
    else:
        print("No users found in the database.")
    
    conn.close()

# ---------------------------
# Main Function
# ---------------------------
def main():
    while True:
        print("\n===== DATABASE VIEWER =====")
        print("1. View Users")
        print("2. View Users with Statistics")
        print("3. View Predictions")
        print("4. View User Sessions")
        print("5. Exit")
        choice = input("Enter your choice (1/2/3/4/5): ").strip()
        
        if choice == "1":
            view_users()
        elif choice == "2":
            view_users_with_stats()
        elif choice == "3":
            view_predictions()
        elif choice == "4":
            view_sessions()
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please select 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()

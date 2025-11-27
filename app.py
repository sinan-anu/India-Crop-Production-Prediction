from flask import Flask, render_template, request, redirect, url_for, session, flash
import matplotlib.image as mpimg
import sqlite3
import joblib
import pandas as pd

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import os
import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------- ADMIN CREDENTIALS ----------
ADMIN_EMAIL = "sinankadukkuthi@gmail.com"  # Stored in lowercase for case-insensitive matching
ADMIN_PASSWORD = "Sinan@123"

# Custom Jinja2 filter for safe number formatting
@app.template_filter('safe_format')
def safe_format(value, format_str='%.2f'):
    """Safely format a number, returning 'N/A' if value is None"""
    if value is None:
        return 'N/A'
    try:
        return format_str % float(value)
    except (ValueError, TypeError):
        return str(value) if value else 'N/A'

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    """Safe SQLite connection with timeout + row factory."""
    conn = sqlite3.connect("database.db", timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- DATABASE SETUP ----------
def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()

        # ---------- USERS TABLE ----------
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL, 
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        # ---------- USER SESSIONS TABLE ----------
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_time TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # ---------- PREDICTIONS TABLE ----------
        c.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                year INTEGER,
                crop TEXT,
                season TEXT,
                state TEXT,
                area REAL,
                production REAL,
                annual_rainfall REAL,
                fertilizer REAL,
                pesticide REAL,
                yield_value REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Add year column if it doesn't exist (for existing databases)
        try:
            c.execute("ALTER TABLE predictions ADD COLUMN year INTEGER")
        except sqlite3.OperationalError:
            pass  # Column already exists

        conn.commit()
        print("✅ Database initialized successfully with 'timestamp' and 'year' in predictions table.")


# Run the setup when file executes
if __name__ == "__main__":
    init_db()


# ---------- LOAD MODEL ----------
loaded_model = joblib.load('models/random_forest_crop_yield.joblib')
loaded_pt = joblib.load('models/power_transformer_crop_yield.joblib')
feature_names = joblib.load('models/crop_yield_feature_names.joblib')

# ---------- DICTIONARIES ----------
crop_dict = {
    'Arecanut': 0, 'Arhar/Tur': 1, 'Bajra': 2, 'Banana': 3, 'Barley': 4,
    'Black pepper': 5, 'Cardamom': 6, 'Cashewnut': 7, 'Castor seed': 8,
    'Coconut ': 9, 'Coriander': 10, 'Cotton(lint)': 11, 'Cowpea(Lobia)': 12,
    'Dry chillies': 13, 'Garlic': 14, 'Ginger': 15, 'Gram': 16, 'Groundnut': 17,
    'Guar seed': 18, 'Horse-gram': 19, 'Jowar': 20, 'Jute': 21, 'Khesari': 22,
    'Linseed': 23, 'Maize': 24, 'Masoor': 25, 'Mesta': 26, 'Moong(Green Gram)': 27,
    'Moth': 28, 'Niger seed': 29, 'Oilseeds total': 30, 'Onion': 31,
    'Other  Rabi pulses': 32, 'Other Cereals': 33, 'Other Kharif pulses': 34,
    'Other Summer Pulses': 35, 'Peas & beans (Pulses)': 36, 'Potato': 37,
    'Ragi': 38, 'Rapeseed &Mustard': 39, 'Rice': 40, 'Safflower': 41,
    'Sannhamp': 42, 'Sesamum': 43, 'Small millets': 44, 'Soyabean': 45,
    'Sugarcane': 46, 'Sunflower': 47, 'Sweet potato': 48, 'Tapioca': 49,
    'Tobacco': 50, 'Turmeric': 51, 'Urad': 52, 'Wheat': 53, 'other oilseeds': 54
}

season_dict = {
    'Autumn     ': 0, 'Kharif     ': 1, 'Rabi       ': 2,
    'Summer     ': 3, 'Whole Year ': 4, 'Winter     ': 5
}

state_dict = {
    'Andhra Pradesh': 0, 'Arunachal Pradesh': 1, 'Assam': 2, 'Bihar': 3,
    'Chhattisgarh': 4, 'Delhi': 5, 'Goa': 6, 'Gujarat': 7, 'Haryana': 8,
    'Himachal Pradesh': 9, 'Jammu and Kashmir': 10, 'Jharkhand': 11,
    'Karnataka': 12, 'Kerala': 13, 'Madhya Pradesh': 14, 'Maharashtra': 15,
    'Manipur': 16, 'Meghalaya': 17, 'Mizoram': 18, 'Nagaland': 19, 'Odisha': 20,
    'Puducherry': 21, 'Punjab': 22, 'Sikkim': 23, 'Tamil Nadu': 24,
    'Telangana': 25, 'Tripura': 26, 'Uttar Pradesh': 27, 'Uttarakhand': 28,
    'West Bengal': 29
}

# ---------- ROUTES ----------
@app.route("/")
def home():
    return redirect(url_for("login"))

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()

        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if not user:
            flash("No account found. Please sign up first.")
            return redirect(url_for("signup"))

        stored_password = user["password"]
        if stored_password == password:
            session["user"] = email
            # Record login session
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO user_sessions (user_id, login_time)
                VALUES (?, CURRENT_TIMESTAMP)
            """, (user["id"],))
            conn.commit()
            conn.close()
            flash("Login successful!")
            return redirect(url_for("prediction"))
        else:
            flash("Incorrect password.")
            return redirect(url_for("login"))

    return render_template("login.html")

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        firstname = request.form["firstname"].strip()
        lastname  = request.form["lastname"].strip()
        email     = request.form["email"].strip().lower()
        password  = request.form["password"]
        confirm   = request.form["confirm"]

        if password != confirm:
            flash("Passwords do not match!")
            return redirect(url_for("signup"))

        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO users (firstname, lastname, email, password) VALUES (?, ?, ?, ?)",
                (firstname, lastname, email, password)
            )
            conn.commit()
            conn.close()
            flash("Account created successfully. Please log in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already exists!")
            return redirect(url_for("signup"))

    return render_template("signup.html")

# ---------- DASHBOARD (Prediction + Graphs) ----------
@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    # ----------------- Check if user is logged in -----------------
    if "user" not in session:
        return redirect(url_for("login"))

    prediction_result = None
    selected_x = None
    selected_y = None

    # ----------------- Get logged-in user info -----------------
    user_email = session["user"]
    conn = get_db_connection()
    user_data = conn.execute(
        "SELECT firstname, lastname, email FROM users WHERE email = ?",
        (user_email,)
    ).fetchone()
    conn.close()

    if user_data:
        user_name = f"{user_data['firstname']} {user_data['lastname']}"
    else:
        user_name = "Unknown User"

    # ----------------- Load dataset -----------------
    df = pd.read_csv("C:\\Users\\Sinan\\Desktop\\Projects\\Indian_crop_production_prediction1\\crop_yield.csv")
    df.columns = df.columns.str.strip()

    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    numerical_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

    # ----------------- POST request handling -----------------
    if request.method == "POST":
        # ----- Prediction -----
        if "predict" in request.form:
            try:
                # Validate year first
                try:
                    year = int(request.form.get('year', 0))
                except (ValueError, TypeError):
                    flash("Error: Year must be a valid number.", "danger")
                    return render_template(
                        "prediction.html",
                        crop_dict=crop_dict,
                        season_dict=season_dict,
                        state_dict=state_dict,
                        prediction_result=None,
                        x_options=categorical_cols,
                        y_options=numerical_cols,
                        selected_x=selected_x,
                        selected_y=selected_y,
                        name=user_name,
                        email=user_email
                    )
                
                if year < 1997 or year > 2030:
                    flash(f"Error: Year must be between 1997 and 2030. You entered {year}.", "danger")
                    return render_template(
                        "prediction.html",
                        crop_dict=crop_dict,
                        season_dict=season_dict,
                        state_dict=state_dict,
                        prediction_result=None,
                        x_options=categorical_cols,
                        y_options=numerical_cols,
                        selected_x=selected_x,
                        selected_y=selected_y,
                        name=user_name,
                        email=user_email
                    )
                
                # Parse and validate numeric inputs (must be non-negative)
                try:
                    area = float(request.form['area'])
                    production = float(request.form['production'])
                    annual_rainfall = float(request.form['annual_rainfall'])
                    fertilizer = float(request.form['fertilizer'])
                    pesticide = float(request.form['pesticide'])
                except (ValueError, KeyError) as e:
                    flash("Error: All numeric fields must be valid numbers.", "danger")
                    return render_template(
                        "prediction.html",
                        crop_dict=crop_dict,
                        season_dict=season_dict,
                        state_dict=state_dict,
                        prediction_result=None,
                        x_options=categorical_cols,
                        y_options=numerical_cols,
                        selected_x=selected_x,
                        selected_y=selected_y,
                        name=user_name,
                        email=user_email
                    )
                
                # Validate that all values are non-negative
                if area < 0 or production < 0 or annual_rainfall < 0 or fertilizer < 0 or pesticide < 0:
                    negative_fields = []
                    if area < 0:
                        negative_fields.append(f"Area ({area})")
                    if production < 0:
                        negative_fields.append(f"Production ({production})")
                    if annual_rainfall < 0:
                        negative_fields.append(f"Annual Rainfall ({annual_rainfall})")
                    if fertilizer < 0:
                        negative_fields.append(f"Fertilizer ({fertilizer})")
                    if pesticide < 0:
                        negative_fields.append(f"Pesticide ({pesticide})")
                    
                    flash(f"Error: The following fields cannot be negative: {', '.join(negative_fields)}. All values must be zero or positive.", "danger")
                    return render_template(
                        "prediction.html",
                        crop_dict=crop_dict,
                        season_dict=season_dict,
                        state_dict=state_dict,
                        prediction_result=None,
                        x_options=categorical_cols,
                        y_options=numerical_cols,
                        selected_x=selected_x,
                        selected_y=selected_y,
                        name=user_name,
                        email=user_email
                    )
                
                crop = request.form['crop']
                season = request.form['season']
                state = request.form['state']

                # Prepare input data
                input_data = pd.DataFrame({
                    'Area': [area],
                    'Production': [production],
                    'Annual_Rainfall': [annual_rainfall],
                    'Fertilizer': [fertilizer],
                    'Pesticide': [pesticide],
                    'Crop': [crop],
                    'Season': [season],
                    'State': [state]
                })

                # One-hot encode to match training features
                input_data = pd.get_dummies(input_data, columns=['Crop','Season','State'], drop_first=True)
                for col in feature_names:
                    if col not in input_data.columns:
                        input_data[col] = 0
                input_data = input_data[feature_names]

                # Predict
                x_test_transformed = loaded_pt.transform(input_data)
                result = loaded_model.predict(x_test_transformed)
                prediction_result = result[0]

                # Save prediction to DB
                conn = get_db_connection()
                c = conn.cursor()
                try:
                    c.execute("""
                        INSERT INTO predictions 
                        (user_id, year, crop, season, state, area, production, annual_rainfall, fertilizer, pesticide, yield_value)
                        VALUES ((SELECT id FROM users WHERE email = ?), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user_email, year, crop, season, state, area, production, annual_rainfall, fertilizer, pesticide, prediction_result))
                    conn.commit()
                    print(f"DEBUG: Prediction saved successfully for user {user_email}")
                except sqlite3.OperationalError as db_error:
                    # If year column doesn't exist, try without it
                    if "year" in str(db_error).lower() or "no such column" in str(db_error).lower():
                        try:
                            c.execute("""
                                INSERT INTO predictions 
                                (user_id, crop, season, state, area, production, annual_rainfall, fertilizer, pesticide, yield_value)
                                VALUES ((SELECT id FROM users WHERE email = ?), ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (user_email, crop, season, state, area, production, annual_rainfall, fertilizer, pesticide, prediction_result))
                            conn.commit()
                            print(f"DEBUG: Prediction saved successfully (without year) for user {user_email}")
                        except Exception as e2:
                            print(f"DEBUG: Error saving prediction (fallback): {e2}")
                            flash(f"Error saving prediction: {e2}", "danger")
                    else:
                        print(f"DEBUG: Error saving prediction: {db_error}")
                        flash(f"Error saving prediction: {db_error}", "danger")
                except Exception as e:
                    print(f"DEBUG: Error saving prediction: {e}")
                    flash(f"Error saving prediction: {e}", "danger")
                finally:
                    conn.close()

            except Exception as e:
                flash(f"Prediction error: {e}", "danger")

        # ----- Graph generation -----
        elif "graph" in request.form:
            selected_x = request.form.get("x_axis")
            selected_y = request.form.get("y_axis")

            if selected_x in df.columns and selected_y in df.columns:
                plt.figure(figsize=(10, 6))
                if os.path.exists("static/crop_bg.png"):
                    img = mpimg.imread("static/crop_bg.png")
                    plt.imshow(img, extent=[-0.5, len(df[selected_x])-0.5,
                                            df[selected_y].min()*0.9,
                                            df[selected_y].max()*1.1],
                               aspect='auto', alpha=0.2)

                grouped_df = df.groupby(selected_x)[selected_y].mean().reset_index()
                plt.bar(grouped_df[selected_x], grouped_df[selected_y], color='green')
                plt.xticks(rotation=45, ha='right')
                plt.xlabel(selected_x)
                plt.ylabel(selected_y)
                plt.title(f"{selected_y} vs {selected_x}")
                plt.tight_layout()
                plt.savefig("static/feature_plot.png")
                plt.close()

    # ----------------- Render template -----------------
    return render_template(
        "prediction.html",
        crop_dict=crop_dict,
        season_dict=season_dict,
        state_dict=state_dict,
        prediction_result=prediction_result,
        x_options=categorical_cols,
        y_options=numerical_cols,
        selected_x=selected_x,
        selected_y=selected_y,
        name=user_name,     # <-- user name for template
        email=user_email    # <-- user email for template
    )

# About Page----------------------------
@app.route("/about")
def about():
    return render_template("about.html")

# ---------- ADMIN LOGIN ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()

        # Check admin credentials
        if email == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
            session["admin"] = True
            session["admin_email"] = email
            flash("Admin login successful!", "success")
            return redirect(url_for("admin"))
        else:
            flash("Invalid admin credentials. Access denied.", "error")
            return redirect(url_for("admin_login"))

    return render_template("admin_login.html")

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin")
def admin():
    # Check if admin is authenticated
    if "admin" not in session or not session.get("admin"):
        flash("Please login as admin to access this page.", "error")
        return redirect(url_for("admin_login"))
    
    try:
        conn = get_db_connection()
        
        # Get only users who have made predictions (entered prediction dashboard)
        try:
            users_data = conn.execute("""
                SELECT 
                    u.id,
                    u.firstname,
                    u.lastname,
                    u.email,
                    COUNT(DISTINCT us.id) as visit_count,
                    MAX(us.login_time) as last_login,
                    COUNT(DISTINCT p.id) as prediction_count
                FROM users u
                INNER JOIN predictions p ON u.id = p.user_id
                LEFT JOIN user_sessions us ON u.id = us.user_id
                GROUP BY u.id, u.firstname, u.lastname, u.email
                ORDER BY u.id
            """).fetchall()
        except Exception as e:
            print(f"Error fetching users: {e}")
            users_data = []
        
        # Get all predictions with user details
        predictions_data = []
        try:
            # First check if predictions table exists and has data
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM predictions")
            prediction_count = c.fetchone()[0]
            print(f"DEBUG: Total predictions in database: {prediction_count}")
            
            if prediction_count > 0:
                # Check which columns exist
                c.execute("PRAGMA table_info(predictions)")
                columns_info = c.fetchall()
                column_names = [col[1] for col in columns_info]
                print(f"DEBUG: Available columns: {column_names}")
                
                has_year = "year" in column_names
                has_timestamp = "timestamp" in column_names
                
                # Build query based on available columns
                select_fields = [
                    "p.id",
                    "u.firstname || ' ' || u.lastname as user_name",
                    "u.email"
                ]
                
                if has_year:
                    select_fields.append("p.year")
                else:
                    select_fields.append("NULL as year")
                
                select_fields.extend([
                    "p.crop", "p.season", "p.state", "p.area", "p.production",
                    "p.annual_rainfall", "p.fertilizer", "p.pesticide", "p.yield_value"
                ])
                
                if has_timestamp:
                    select_fields.append("p.timestamp")
                else:
                    select_fields.append("NULL as timestamp")
                
                # Build the query
                query = f"""
                    SELECT {', '.join(select_fields)}
                    FROM predictions p
                    JOIN users u ON p.user_id = u.id
                """
                
                # Add ORDER BY
                if has_timestamp:
                    query += " ORDER BY p.timestamp DESC"
                else:
                    query += " ORDER BY p.id DESC"
                
                print(f"DEBUG: Executing query: {query[:100]}...")
                predictions_data = conn.execute(query).fetchall()
                print(f"DEBUG: Successfully fetched {len(predictions_data)} predictions")
            else:
                print("DEBUG: No predictions found in database")
                
        except Exception as e:
            print(f"Error fetching predictions: {e}")
            import traceback
            traceback.print_exc()
            predictions_data = []
        
        # Get all user sessions
        try:
            sessions_data = conn.execute("""
                SELECT 
                    us.id,
                    u.firstname || ' ' || u.lastname as user_name,
                    u.email,
                    us.login_time,
                    us.logout_time,
                    CASE 
                        WHEN us.logout_time IS NULL THEN 'Active'
                        ELSE 'Completed'
                    END as status
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                ORDER BY us.login_time DESC
            """).fetchall()
        except Exception as e:
            print(f"Error fetching sessions: {e}")
            sessions_data = []
        
        # Generate crop prediction graph
        crop_graph_path = None
        try:
            if prediction_count > 0:
                # Get crop prediction counts
                crop_counts_query = """
                    SELECT crop, COUNT(*) as count
                    FROM predictions
                    GROUP BY crop
                    ORDER BY count DESC
                    LIMIT 10
                """
                crop_data = conn.execute(crop_counts_query).fetchall()
                
                if crop_data:
                    crops = [row[0] for row in crop_data]
                    counts = [row[1] for row in crop_data]
                    
                    # Create the graph
                    plt.figure(figsize=(12, 6))
                    colors = plt.cm.Set3(range(len(crops)))
                    bars = plt.barh(crops, counts, color=colors)
                    
                    # Add value labels on bars
                    for i, (crop, count) in enumerate(zip(crops, counts)):
                        plt.text(count, i, f' {count}', va='center', fontweight='bold')
                    
                    plt.xlabel('Number of Predictions', fontsize=12, fontweight='bold')
                    plt.ylabel('Crop', fontsize=12, fontweight='bold')
                    plt.title('Most Predicted Crops (Top 10)', fontsize=14, fontweight='bold', pad=20)
                    plt.gca().invert_yaxis()  # Show highest at top
                    plt.tight_layout()
                    
                    # Save the graph
                    crop_graph_path = "most_predicted_crops.png"
                    graph_full_path = os.path.join("static", crop_graph_path)
                    plt.savefig(graph_full_path, dpi=100, bbox_inches='tight')
                    plt.close()
                    print(f"DEBUG: Crop prediction graph saved to {graph_full_path}")
        except Exception as e:
            print(f"Error generating crop graph: {e}")
            import traceback
            traceback.print_exc()
        
        conn.close()
        
        return render_template(
            "admin.html",
            users=users_data or [],
            predictions=predictions_data or [],
            sessions=sessions_data or [],
            crop_graph_path=crop_graph_path
        )
    except Exception as e:
        flash(f"Error loading admin dashboard: {str(e)}", "danger")
        return redirect(url_for("prediction"))

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    if "user" in session:
        user_email = session["user"]
        # Update logout time for the most recent session
        try:
            conn = get_db_connection()
            c = conn.cursor()
            # First, find the most recent active session
            c.execute("""
                SELECT us.id 
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE u.email = ? AND us.logout_time IS NULL
                ORDER BY us.login_time DESC
                LIMIT 1
            """, (user_email,))
            session_row = c.fetchone()
            
            if session_row:
                # Update that specific session
                c.execute("""
                    UPDATE user_sessions 
                    SET logout_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (session_row[0],))
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating logout time: {e}")
            # Continue with logout even if session update fails
    
    session.pop("user", None)
    flash("Logged out successfully.")
    return redirect(url_for("login"))

# ---------- ADMIN LOGOUT ----------
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    session.pop("admin_email", None)
    flash("Admin logged out successfully.", "success")
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)

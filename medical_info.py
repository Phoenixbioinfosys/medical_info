import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import plotly.express as px
import bcrypt

# Set up the database
conn = sqlite3.connect('hospital_data.db')
cursor = conn.cursor()

# Define table structure for users and patient records
def create_tables():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS patients (
        bed_number INTEGER PRIMARY KEY,
        name TEXT,
        demographic_data TEXT,
        assessment TEXT,
        investigations TEXT,
        diagnosis TEXT,
        prognosis TEXT,
        progress_data TEXT,
        last_modified_by TEXT,
        last_modified_on TEXT
    )''')
    conn.commit()

create_tables()

# Hashing function for storing passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Authentication functions
def add_user(username, password):
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
    conn.commit()

def verify_user(username, password):
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    if result and bcrypt.checkpw(password.encode(), result[0]):
        return True
    return False

# Patient data functions
def add_patient_data(bed_number, data):
    cursor.execute("INSERT OR REPLACE INTO patients (bed_number, name, demographic_data, assessment, investigations, diagnosis, prognosis, progress_data, last_modified_by, last_modified_on) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
    conn.commit()

def get_patient_data(bed_number):
    cursor.execute("SELECT * FROM patients WHERE bed_number=?", (bed_number,))
    return cursor.fetchone()

# Login and Registration
st.title("Hospital Management System")

# Check if user is logged in
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    option = st.selectbox("Login or Sign up", ["Login", "Sign Up"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Sign Up":
        if st.button("Register"):
            add_user(username, password)
            st.success("User registered successfully!")
    elif option == "Login":
        if st.button("Login"):
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome {username}!")
            else:
                st.error("Invalid username or password.")
else:
    # Main App
    st.sidebar.title("Patient Management")

    # Add a new patient record
    st.sidebar.subheader("Add / Update Patient Data")
    bed_number = st.sidebar.number_input("Patient Bed Number", min_value=1, step=1)
    name = st.sidebar.text_input("Patient Name")
    demographic_data = st.sidebar.text_area("Demographic Data")
    assessment = st.sidebar.text_area("Assessment")
    investigations = st.sidebar.text_area("Investigations")
    diagnosis = st.sidebar.text_area("Diagnosis")
    prognosis = st.sidebar.text_area("Prognosis")
    progress_data = st.sidebar.text_area("Progress Notes")

    # Save patient data with modification details
    if st.sidebar.button("Save Data"):
        data = (
            bed_number,
            name,
            demographic_data,
            assessment,
            investigations,
            diagnosis,
            prognosis,
            progress_data,
            st.session_state.username,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        add_patient_data(bed_number, data)
        st.sidebar.success("Patient data saved successfully!")

    # Display and search patient records
    st.header("Patient Records")
    bed_number_search = st.number_input("Enter Bed Number to Retrieve Patient Data", min_value=1, step=1)

    if st.button("Fetch Patient Data"):
        patient_data = get_patient_data(bed_number_search)
        if patient_data:
            bed_num, name, demo, assess, inves, diag, prog, progress, last_mod_by, last_mod_on = patient_data
            st.subheader(f"Patient: {name}")
            st.text(f"Bed Number: {bed_num}")
            st.text(f"Demographic Data: {demo}")
            st.text(f"Assessment: {assess}")
            st.text(f"Investigations: {inves}")
            st.text(f"Diagnosis: {diag}")
            st.text(f"Prognosis: {prog}")
            st.text(f"Progress Notes: {progress}")
            st.text(f"Last Modified by: {last_mod_by} on {last_mod_on}")

            # Displaying progress graph if data is available
            if progress:
                progress_points = progress.split(',')
                progress_values = [float(val.strip()) for val in progress_points if val.strip().isdigit()]
                progress_df = pd.DataFrame({
                    'Session': list(range(1, len(progress_values) + 1)),
                    'Progress Value': progress_values
                })
                fig = px.line(progress_df, x='Session', y='Progress Value', title=f"Progress of {name}")
                st.plotly_chart(fig)
        else:
            st.warning("No data found for the given bed number.")

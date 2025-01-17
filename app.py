import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Shared Credentials Setup
def get_credentials():
    """Retrieve shared credentials from Streamlit secrets."""
    try:
        cred_dict = dict(st.secrets["firebase_credentials"])  # Convert AttrDict to dictionary
        return cred_dict
    except Exception as e:
        st.error(f"Error retrieving shared credentials: {e}")
        return None

# Firebase Setup
def initialize_firebase(cred_dict):
    """Initialize Firebase app and Firestore client."""
    try:
        if not firebase_admin._apps:  # Prevent reinitialization
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        return db
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        return None

def connect_to_google_sheets():
    """Connect to Google Sheets using credentials."""
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file"
        ]
        credentials_info = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)
        client = gspread.authorize(credentials)
        sheet = client.open("QualityReport").sheet1  # Replace with your actual Google Sheet name
        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def save_to_google_sheet(data):
    """Save user input data to Google Sheets."""
    sheet = connect_to_google_sheets()
    if sheet:
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            formatted_data = [current_date] + data
            st.write("Formatted data to save:", formatted_data)  # Debugging log
            sheet.append_row(formatted_data)
            st.success("Data saved to Google Sheets successfully!")
        except Exception as e:
            st.error(f"Error saving data to Google Sheets: {e}")

# Generate PDF Report
def generate_pdf(batch_id, data):
    """Generate a PDF quality report."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Quality Report for Batch {batch_id}", ln=True, align="C")
        pdf.ln(10)  # Line break

        for key, value in data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align="L")

        file_name = f"Batch_{batch_id}_Report.pdf"
        pdf.output(file_name)
        return file_name
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

# Streamlit App
st.title("Port Worker Quality Checker")
st.header("Enter Quality Parameters")

# Retrieve shared credentials
cred_dict = get_credentials()

# Initialize Firebase
db = None
if cred_dict:
    db = initialize_firebase(cred_dict)

# Fetch real-time data from Firebase
if db:
    try:
        docs = db.collection("port_worker_data").stream()
        firebase_data = [doc.to_dict() for doc in docs]
        if firebase_data:
            st.subheader("Real-time Data from Firebase")
            st.write(firebase_data)
    except Exception as e:
        st.error(f"Error retrieving data from Firebase: {e}")

# Input form
with st.form("input_form"):
    batch_id = st.text_input("Batch ID", placeholder="Enter unique batch ID")
    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
    pressure = st.number_input("Pressure", min_value=0.0, step=0.1)
    temperature = st.number_input("Temperature (°C)", min_value=-50.0, step=0.1)
    worker_name = st.text_input("Worker Name")
    submit_button = st.form_submit_button("Submit")

    if submit_button:
        user_data = [batch_id, weight, pressure, temperature, worker_name]
        save_to_google_sheet(user_data)

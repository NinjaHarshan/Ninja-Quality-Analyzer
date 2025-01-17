import streamlit as st
from fpdf import FPDF
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

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

    if submit_button and db:
        try:
            data = {
                "batch_id": batch_id,
                "weight": weight,
                "pressure": pressure,
                "temperature": temperature,
                "worker_name": worker_name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            db.collection("port_worker_data").add(data)
            st.success("Data saved to Firebase successfully!")
        except Exception as e:
            st.error(f"Error saving data to Firebase: {e}")
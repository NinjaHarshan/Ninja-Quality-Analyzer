import streamlit as st
from datetime import datetime
from fpdf import FPDF
import re
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Setup Functions
def get_credentials():
    try:
        return dict(st.secrets["firebase_credentials"])
    except Exception as e:
        st.error(f"Error retrieving credentials: {e}")
        return None

def initialize_firebase(cred_dict):
    if not firebase_admin._apps:  # Prevent reinitialization
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

# PDF Generation Function
def generate_pdf(consignment_number, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Quality Report for Consignment {consignment_number}", ln=True, align="C")
    pdf.ln(10)
    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align="L")
    file_name = f"Consignment_{consignment_number}_Report.pdf"
    pdf.output(file_name)
    return file_name

# Validation Helpers
def validate_numeric(input_value):
    # Regex: Allow numbers with optional decimal, but no more than 2 decimals.
    regex = r"^\-?\d{1,3}(\.\d{0,2})?$"  # Allow negative and up to 2 decimal places
    return bool(re.fullmatch(regex, input_value.strip()))

# Streamlit App
st.title("Port Worker Quality Checker")
st.header("Enter Quality Parameters")

# Firebase Initialization
cred_dict = get_credentials()
db = initialize_firebase(cred_dict) if cred_dict else None

# Form State Management
if "weights" not in st.session_state:
    st.session_state.weights = []

# Form for Inputs
with st.form("input_form"):
    # Consignment and Inspector Name
    consignment_number = st.text_input(
        "Consignment Number",
        placeholder="Enter consignment number",
        max_chars=10,
        help="Maximum 10 characters.",
    )
    inspector_name = st.text_input(
        "Inspector Name",
        placeholder="Enter inspector name",
        max_chars=15,
        help="Maximum 15 characters.",
    )

    # Number of Boxes
    num_boxes = st.number_input(
        "Number of Boxes for Testing",
        min_value=1,
        step=1,
        format="%d",
        help="Enter the total number of boxes for testing.",
        key="num_boxes",
    )

    # Dynamically Create Weight Inputs for each box
    st.subheader("Weights")
    weights = []
    for i in range(num_boxes):
        weight = st.text_input(
            f"Weight {i + 1} (kg) *",
            placeholder="Enter weight",
            key=f"weight_{i}",
        )
        weights.append(weight)

    # Pressure Inputs (3 Mandatory Fields)
    st.subheader("Pressures")
    pressures = []
    for i in range(3):
        pressure = st.text_input(
            f"Pressure {i + 1} (kgf/cm²) *",
            placeholder="Enter pressure",
            key=f"pressure_{i}",
        )
        pressures.append(pressure)

    # Temperature Inputs (3 Mandatory Fields) - Default is negative
    st.subheader("Temperatures")
    temperatures = []
    for i in range(3):
        # Default temperature with negative sign
        temperature = st.text_input(
            f"Temperature {i + 1} (°C) *",
            placeholder="Enter temperature (in °C, negative by default)",
            key=f"temperature_{i}",
            value="-",  # Display negative sign upfront
        )
        temperatures.append(temperature)

    # File Upload
    file = st.file_uploader("Upload Image/Video/PDF (Optional)", type=["jpg", "jpeg", "png", "mp4", "pdf"])

    # Submit Button
    submit_button = st.form_submit_button("Submit")

# Real-time validation logic
if submit_button:
    errors = []

    # Validate Consignment and Inspector Name
    if not consignment_number.strip():
        errors.append("Consignment Number is mandatory!")
    if not inspector_name.strip():
        errors.append("Inspector Name is mandatory!")

    # Validate Weight Inputs
    for i, weight in enumerate(weights):
        if not weight.strip():
            errors.append(f"Weight {i + 1} is mandatory!")
        elif not validate_numeric(weight):  # Validate as numeric (up to 2 decimals)
            errors.append(f"Weight {i + 1} must be a valid number!")

    # Validate Pressure Inputs
    for i, pressure in enumerate(pressures):
        if not pressure.strip():
            errors.append(f"Pressure {i + 1} is mandatory!")
        elif not validate_numeric(pressure):  # Validate as numeric (up to 2 decimals)
            errors.append(f"Pressure {i + 1} must be a valid number!")

    # Validate Temperature Inputs (No explicit check for negative values)
    for i, temperature in enumerate(temperatures):
        if not temperature.strip() or temperature == "-":
            errors.append(f"Temperature {i + 1} is mandatory!")
        elif not validate_numeric(temperature):  # Validate as numeric (up to 2 decimals)
            errors.append(f"Temperature {i + 1} must be a valid number!")

    # Show Errors or Process Form
    if errors:
        for error in errors:
            st.error(error)
    else:
        # Treat user input as negative value for temperatures
        temperatures = [str(-abs(float(temp))) for temp in temperatures]

        data = {
            "Consignment Number": consignment_number,
            "Inspector Name": inspector_name,
            "Number of Boxes": num_boxes,
            "Weights": weights,
            "Pressures": pressures,
            "Temperatures": temperatures,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if file:
            data["Uploaded File"] = file.name

        # Save to Firebase
        if db:
            db.collection("port_worker_data").add(data)
            st.success("Data submitted successfully!")
        else:
            st.warning("Firebase connection not initialized.")

        # Generate and save PDF
        report_file = generate_pdf(consignment_number, data)
        if report_file:
            with open(report_file, "rb") as f:
                # Move download button outside the form
                st.download_button(
                    label="Download Report",
                    data=f,
                    file_name=report_file,
                    mime="application/pdf",
                )

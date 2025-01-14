import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from fpdf import FPDF

# Google Sheets setup
def connect_to_google_sheets():
    # Define the scope of the permissions
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Load credentials from the JSON key file
    creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Users\Harshan G_NC24854\Downloads\My projects\Quality_app\sheet_credentials.json", scope)
    
    # Authorize the client and access the Google Sheet
    client = gspread.authorize(creds)
    sheet = client.open("QualityReport").sheet1  # Replace with your sheet name
    return sheet

# Save data to Google Sheets
def save_to_google_sheet(data):
    sheet = connect_to_google_sheets()
    sheet.append_row(data)

# Generate PDF report
def generate_pdf(batch_id, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Quality Report for Batch {batch_id}", ln=True, align="C")

    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align="L")

    file_name = f"Batch_{batch_id}_Report.pdf"
    pdf.output(file_name)
    return file_name

# Streamlit App
st.title("Port Worker Quality Checker")
st.header("Enter Quality Parameters")

# Input form
with st.form("input_form"):
    batch_id = st.text_input("Batch ID")
    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
    pressure = st.number_input("Pressure (bar)", min_value=0.0, step=0.1)
    temperature = st.number_input("Temperature (°C)", min_value=0.0, step=0.1)
    inspector_name = st.text_input("Inspector Name")
    submit = st.form_submit_button("Submit")

if submit:
    # Save data to Google Sheets and locally
    data = [batch_id, weight, pressure, temperature, inspector_name]
    save_to_google_sheet(data)

    # Generate and allow download of PDF report
    report_file = generate_pdf(batch_id, {
        "Weight": weight,
        "Pressure": pressure,
        "Temperature": temperature,
        "Inspector Name": inspector_name
    })
    with open(report_file, "rb") as file:
        st.download_button("Download Report", file, file_name=report_file)

    st.success("Data submitted and report generated!")

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF

# Google Sheets setup
def connect_to_google_sheets():
    try:
        # Define the scope of the permissions
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # Load credentials from Streamlit secrets
        credentials_info = st.secrets["gcp_service_account"]  # Access the secret directly
        credentials = Credentials.from_service_account_info(credentials_info)  # Create credentials object

        # Authorize the client and access the Google Sheet
        client = gspread.authorize(credentials)
        sheet = client.open("QualityReport").sheet1  # Replace with your Google Sheet name
        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# Save data to Google Sheets
def save_to_google_sheet(data):
    sheet = connect_to_google_sheets()
    if sheet:
        try:
            sheet.append_row(data)
            st.success("Data saved to Google Sheets successfully!")
        except Exception as e:
            st.error(f"Error saving data to Google Sheets: {e}")

# Generate PDF report
def generate_pdf(batch_id, data):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Quality Report for Batch {batch_id}", ln=True, align="C")

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

# Input form
with st.form("input_form"):
    batch_id = st.text_input("Batch ID")
    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)
    pressure = st.number_input("Pressure (bar)", min_value=0.0, step=0.1)
    temperature = st.number_input("Temperature (°C)", min_value=0.0, step=0.1)
    inspector_name = st.text_input("Inspector Name")
    submit = st.form_submit_button("Submit")

if submit:
    if batch_id and inspector_name:
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
        if report_file:
            with open(report_file, "rb") as file:
                st.download_button("Download Report", file, file_name=report_file)
    else:
        st.error("Please fill in all required fields (Batch ID and Inspector Name).")

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from datetime import datetime

# Google Sheets setup
def connect_to_google_sheets():
    try:
        # Define the scope of the permissions
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",  # Correct scope for Sheets
            "https://www.googleapis.com/auth/drive.file"    # Access to Google Drive files
        ]

        # Load credentials from Streamlit secrets
        credentials_info = st.secrets["gcp_service_account"]  # Access the secret directly
        credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)  # Create credentials object

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
            # Debugging: Check the data being passed to Google Sheets
            st.write("Data being saved:", data)
            
            # Get the current date for the "Date" field
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Prepare data in a proper format to match Google Sheets columns
            formatted_data = [current_date] + data  # Prepend the current date to the data

            # Ensure the header is correct
            headers = ["Date", "Batch ID", "Weight", "Pressure", "Temperature", "InspectorName"]

            # Get all existing records from the sheet (this ensures we match headers)
            existing_records = sheet.get_all_records()  # You can skip 'expected_headers' here
            st.write("Existing records:", existing_records)

            # Append the row to Google Sheets
            sheet.append_row(formatted_data)

            # Debugging: Print all records after appending to ensure data is saved
            st.write("Updated data in sheet:", sheet.get_all_records())

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
    inspector_name = st.text_input("InspectorName")
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
            "InspectorName": inspector_name
        })
        if report_file:
            with open(report_file, "rb") as file:
                st.download_button("Download Report", file, file_name=report_file)
    else:
        st.error("Please fill in all required fields (Batch ID and InspectorName).")

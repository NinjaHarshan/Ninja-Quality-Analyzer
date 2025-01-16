import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from datetime import datetime

# Google Sheets setup
def connect_to_google_sheets(json_file_path, sheet_name):
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file"
        ]
        credentials = Credentials.from_service_account_file(json_file_path, scopes=scope)
        client = gspread.authorize(credentials)
        sheet = client.open(sheet_name).sheet1  # Ensure this matches your sheet name
        return sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# Save data to Google Sheets
def save_to_google_sheet(data, json_file_path, sheet_name):
    sheet = connect_to_google_sheets(json_file_path, sheet_name)
    if sheet:
        try:
            sheet.append_row(data)
            st.success("Data saved successfully!")
        except Exception as e:
            st.error(f"Error saving data to Google Sheets: {e}")

# Generate PDF report
def generate_pdf(consignment_number, number_of_boxes, data, averages):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Quality Report for Consignment {consignment_number}", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Number of Boxes: {number_of_boxes}", ln=True, align="L")
        pdf.cell(200, 10, txt="", ln=True)  # Blank line

        # Add data for each box
        for i, box_data in enumerate(data, start=1):
            pdf.cell(200, 10, txt=f"Box {i} Details:", ln=True, align="L")
            pdf.cell(200, 10, txt=f"   Weight: {box_data['weight']} kg", ln=True, align="L")
            pdf.cell(200, 10, txt=f"   Pressure: {box_data['pressure']} bar", ln=True, align="L")
            pdf.cell(200, 10, txt=f"   Temperature: {box_data['temperature']} °C", ln=True, align="L")

        # Add averages
        pdf.cell(200, 10, txt="", ln=True)  # Blank line
        pdf.cell(200, 10, txt="Averages:", ln=True, align="L")
        pdf.cell(200, 10, txt=f"   Average Weight: {averages['weight']} kg", ln=True, align="L")
        pdf.cell(200, 10, txt=f"   Average Pressure: {averages['pressure']} bar", ln=True, align="L")
        pdf.cell(200, 10, txt=f"   Average Temperature: {averages['temperature']} °C", ln=True, align="L")

        file_name = f"Consignment_{consignment_number}_Report.pdf"
        pdf.output(file_name)
        return file_name
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

# Streamlit app
st.title("Port Worker Quality Checker")

# Specify the path to your JSON credentials
json_file_path = r"C:\Users\Harshan G_NC24854\Downloads\My projects\Quality_app\final-447815-9961556bd9c1.json"  # Replace with the actual path
sheet_name = "IranApple"  # Replace with your sheet name

# Step 1: Consignment number
consignment_number = st.text_input("Enter Consignment Number")

if consignment_number:
    # Step 2: Number of boxes
    number_of_boxes = st.number_input("Enter Number of Boxes Picked for Testing", min_value=1, step=1)

    if number_of_boxes > 0:
        # Dynamic input for each box
        box_data = []
        for i in range(1, number_of_boxes + 1):
            st.subheader(f"Box {i}")
            weight = st.number_input(f"Enter Weight for Box {i} (kg)", min_value=0.0, step=0.1)
            pressure = st.number_input(f"Enter Pressure for Box {i} (bar)", min_value=0.0, step=0.1)
            temperature = st.number_input(f"Enter Temperature for Box {i} (°C)", min_value=0.0, step=0.1)
            box_data.append({"weight": weight, "pressure": pressure, "temperature": temperature})

        # Step 3: Inspector Name
        inspector_name = st.text_input("Enter Inspector Name")

        # Step 4: Submit button
        if st.button("Submit"):
            if inspector_name:
                # Calculate averages
                avg_weight = sum(box["weight"] for box in box_data) / number_of_boxes
                avg_pressure = sum(box["pressure"] for box in box_data) / number_of_boxes
                avg_temperature = sum(box["temperature"] for box in box_data) / number_of_boxes
                averages = {"weight": avg_weight, "pressure": avg_pressure, "temperature": avg_temperature}

                # Save data to Google Sheets
                for i, box in enumerate(box_data, start=1):
                    data_row = [
                        consignment_number,
                        i,
                        box["weight"],
                        box["pressure"],
                        box["temperature"],
                        inspector_name,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    save_to_google_sheet(data_row, json_file_path, sheet_name)

                # Generate PDF report
                report_file = generate_pdf(consignment_number, number_of_boxes, box_data, averages)
                if report_file:
                    with open(report_file, "rb") as file:
                        st.download_button("Download Report", file, file_name=report_file)
            else:
                st.error("Please enter the Inspector Name.")

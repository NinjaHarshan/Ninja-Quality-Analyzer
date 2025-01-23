import streamlit as st
from datetime import datetime
from fpdf import FPDF
import re
import firebase_admin
from firebase_admin import credentials, firestore
from io import BytesIO

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

# Helper function for summary
def generate_summary(data):
    # Calculate averages
    average_weight = sum(data['Weights']) / len(data['Weights'])
    avg_temperature = sum(data['Temperatures']) / len(data['Temperatures'])
    avg_pressure = sum(data['Pressures']) / len(data['Pressures'])
# Helper function for summary

    # Temperature categorization logic from second code
    temp_remarks = "Cold storage" if avg_temperature <= 5 else "Not stored in cold storage"
    
    # Pressure categorization logic from second code
    pressure_remarks = (
        "Hard" if avg_pressure > 6.35
        else "Firm" if 5 <= avg_pressure <= 6.35
        else "Firm Ripe" if 3.65 <= avg_pressure < 5
        else "Ripe"
    )

    # Weight remark always as "NA"
    weight_remark = "NA"
    
    # Construct remarks dictionary
    remarks = {
        "Weight": weight_remark,
        "Temperature": temp_remarks,
        "Pressure": pressure_remarks,
    }

    # Generate summary message
    summary = (
        f"Based on the quality analysis of consignment {data['Consignment Number']}, "
        f"the average weight is {average_weight:.2f} kg. "
        f"The average temperature of the apples is {avg_temperature:.2f} °C, "
        f"falling under the '{temp_remarks}' category. "
        f"The average pressure is {avg_pressure:.2f} kgf/cm², "
        f"falling under the '{pressure_remarks}' category.\n\n"
        f"Recommendations:\n"
        f"- For long storage, apples should be firm with high pressure.\n"
        f"- For immediate sale or processing, softer apples may be suitable."
    )

    return summary, remarks

# Remarks logic for categories
def weight_remark(weight):
    return "NA"

def temp_remark(temp):
    if temp < 0:
        return "Stored in cold storage"
    elif 0 <= temp <= 5:
        return "Stored in cold storage"
    else:
        return "Not stored in cold storage"

def pressure_remark(pressure):
    if pressure < 3:
        return "Ripe, For Short-term use"
    elif 3 <= pressure <= 5:
        return "Ideal for short-term use"
    else:
        return "Firm, suitable for long-term storage"

# PDF Generation Function
# Add About Us section method in CustomPDF class
# PDF Generation Function
# Add About Us section method in CustomPDF class
class CustomPDF(FPDF):
    def header(self):
        self.set_fill_color(144, 238, 144)  # Parrot Light Green
        self.rect(0, 0, 210, 40, 'F')  # Full-width header
        self.image("https://www.ninjacart.com/wp-content/uploads/2023/10/cropped-Group-207-1.png", x=10, y=5, w=190)
        self.ln(40)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "For queries & bookings, contact: +91 9586954665", align="C")

    def add_main_heading(self, title):
        self.set_xy(10, 50)
        self.set_font("Arial", "B", 20)
        self.cell(190, 10, title, 0, 1, "C")
        self.ln(10)

    def add_basic_details(self, data):
        self.set_font("Arial", size=12)
        self.cell(80, 8, "Consignment Number:", border=1)
        self.cell(0, 8, data["Consignment Number"], border=1, ln=True)

        self.cell(80, 8, "Inspector Name:", border=1)
        self.cell(0, 8, data["Inspector Name"], border=1, ln=True)

        self.cell(80, 8, "Buyer Name:", border=1)
        self.cell(0, 8, data["Buyer Name"], border=1, ln=True)

        self.cell(80, 8, "Timestamp:", border=1)
        self.cell(0, 8, data["Timestamp"], border=1, ln=True)

        self.ln(10)

    def add_summary_table(self, summary, remarks):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(144, 238, 144)

        self.cell(25, 10, "Category", 1, 0, "C", fill=True)
        self.cell(30, 10, "Average Value", 1, 0, "C", fill=True)
        self.cell(90, 10, "Reference Range", 1, 0, "C", fill=True)
        self.cell(25, 10, "Remarks", 1, 1, "C", fill=True)

        self.set_font("Arial", size=10)
        self.set_fill_color(240, 240, 240)

        categories = ["Weight", "Temperature", "Pressure"]
        values = [
            f"{sum(data['Weights']) / len(data['Weights']):.2f} kg",
            f"{sum(data['Temperatures']) / len(data['Temperatures']):.2f} °C",
            f"{sum(data['Pressures']) / len(data['Pressures']):.2f} kgf/cm²",
        ]
        ranges = ["3.6 kg - 7.5 kg", "-2°C to 5°C", "3 kgf/cm² to 7 kgf/cm²"]
        
        for i in range(3):
            self.cell(25, 10, categories[i], 1, 0, "C", fill=True)
            self.cell(30, 10, values[i], 1, 0, "C", fill=True)
            self.cell(90, 10, ranges[i], 1, 0, "C", fill=True)
            self.cell(25, 10, remarks[categories[i]], 1, 1, "C", fill=True)

        self.ln(10)

    def add_note_section(self):
        self.set_font("Arial", "I", 10)
        self.multi_cell(0, 10, "Note: This report is generated based testing 3 boxes from the consignment")
    
    def add_about_us_section(self):
        self.ln(10)  # Add extra space before "About Us"
        self.set_font("Arial", "B", 14)
        self.cell(0, 5, "About Us", 0, 1, "C")
        self.set_font("Arial", size=10)
        self.multi_cell(0, 5, "Ninjacart is an innovative leader in connecting farmers and businesses to deliver fresh, high-quality produce directly to customers. We are committed to providing premium-quality fruits and vegetables with a seamless supply chain experience.")
        self.ln(5)
        self.set_font("Arial", "I", 8)
        self.cell(0, 5, "Address: 2nd Floor Tower E, Helios Business Park, New Horizon College Bus Stop, Service Road, Chandana, Kadubeesanahalli, Bengaluru, 560103", 0, 1, "C")
        self.cell(0, 5, "Contact: 080 6915 5666, 988 699 9348", 0, 1, "C")
        self.cell(0, 5, "Email: queries@ninjacart.com", 0, 1, "C")
        self.ln(5)  # Add line break after "About Us"

def generate_pdf(consignment_number, data, summary, remarks):
    pdf = CustomPDF()
    pdf.add_page()

    pdf.add_main_heading("Apple Quality Report")
    pdf.add_basic_details(data)

    # Add second header "QUALITY REPORT SUMMARY"
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "QUALITY REPORT SUMMARY", 0, 1, "C")
    pdf.ln(5)

    pdf.add_summary_table(summary, remarks)

    # Add dynamic lines after the table
    average_weight = sum(data['Weights']) / len(data['Weights'])
    avg_temperature = sum(data['Temperatures']) / len(data['Temperatures'])
    avg_pressure = sum(data['Pressures']) / len(data['Pressures'])

    dynamic_lines = (
        f"Based on the quality analysis of consignment {data['Consignment Number']}, "
        f"the average weight is {average_weight:.2f} kg. "
        f"The average temperature of the apples is {avg_temperature:.2f} °C, "
        f"falling under the '{remarks['Temperature']}' category. "
        f"The average pressure is {avg_pressure:.2f} kgf/cm², "
        f"falling under the '{remarks['Pressure']}' category."
    )

    # Add the "Summary:" header and dynamic lines
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Summary:", ln=True)  # Bold header for "Summary:"
    pdf.set_font("Arial", size=10)  # Regular font for the text
    pdf.multi_cell(0, 5, dynamic_lines)
    pdf.ln(10)

    # Add the note section
    pdf.add_note_section()

    # Add About Us section
    pdf.add_about_us_section()

    file_name = f"Consignment_{consignment_number}_Report.pdf"
    pdf.output(file_name)
    return file_name

# Continue with the rest of your Streamlit app logic as before.

# Streamlit App
st.title("Apple Quality Analyzer")
st.header("Enter Quality Parameters")

# Firebase Initialization
cred_dict = get_credentials()
db = initialize_firebase(cred_dict) if cred_dict else None

# Form for Inputs
with st.form("input_form"):
    # Inputs inside the form
    consignment_number = st.text_input(
        "Enter Consignment Number",
        placeholder="Enter consignment number",
        max_chars=10,
        help="Maximum 10 characters.",
    )
    inspector_name = st.text_input(
        "Enter Inspector Name",
        placeholder="Enter inspector name",
        max_chars=15,
        help="Maximum 15 characters.",
    )
    buyer_name = st.text_input(
        "Enter Buyer Name",
        placeholder="Enter buyer name",
        max_chars=30,
        help="Maximum 30 characters.",
    )

    weights = [
        st.text_input(f"Enter Weight of Box {i + 1} (kg) *", key=f"weight_{i}")
        for i in range(3)
    ]
    pressures = [
        st.text_input(f"Enter Pressure of Apple {i + 1} (kgf/cm²) *", key=f"pressure_{i}")
        for i in range(3)
    ]
    temperatures = [
        st.text_input(f"Enter Temperature of Apple {i + 1} (°C) *", key=f"temperature_{i}")
        for i in range(3)
    ]

    file = st.file_uploader("Upload Image/Video/PDF (Optional)", type=["jpg", "jpeg", "png", "mp4", "pdf"])

    # Submit button
    submit_button = st.form_submit_button("Submit")

# Handle form submission
if submit_button:
    # Initialize the errors list
    errors = []

    # Perform input validation or data checks
    if not consignment_number:
        errors.append("Consignment number is required.")
    if not inspector_name:
        errors.append("Inspector name is required.")
    if not buyer_name:
        errors.append("Buyer name is required.")
    if len(weights) == 0:
        errors.append("At least one weight value is required.")
    if len(pressures) == 0:
        errors.append("At least one pressure value is required.")
    if len(temperatures) == 0:
        errors.append("At least one temperature value is required.")

    # Validate that temperatures are valid numbers (including negative values)
    for temp in temperatures:
        try:
            temp_value = float(temp)
            # Optional: Check for a reasonable range for temperature
            if temp_value < -50 or temp_value > 50:
                errors.append(f"Temperature value {temp} is out of range. Please provide a temperature between -50°C and 50°C.")
        except ValueError:
            errors.append(f"Temperature value '{temp}' is not a valid number.")

    # Proceed if no errors
    if not errors:
        # Prepare data for processing
        data = {
            "Consignment Number": consignment_number,
            "Inspector Name": inspector_name,
            "Buyer Name": buyer_name,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Weights": [float(w) for w in weights],
            "Pressures": [float(p) for p in pressures],
            "Temperatures": [float(t) for t in temperatures],
        }

        # Store data in Firebase Firestore
        if db:
            db.collection('apple_quality_reports').add(data)
            st.success("Data stored successfully in Firebase!")

        summary, remarks = generate_summary(data)

        # Generate PDF report
        pdf_filename = generate_pdf(consignment_number, data, summary, remarks)

        # Display the summary and link to the PDF report
        st.success("Quality Report Generated Successfully!")
        st.write(summary)
        st.download_button(
            label="Download Quality Report PDF",
            data=open(pdf_filename, "rb").read(),
            file_name=pdf_filename,
            mime="application/pdf",
        )
    else:
        # Display the error messages
        st.error("Please correct the following errors:")
        for error in errors:
            st.write(error)
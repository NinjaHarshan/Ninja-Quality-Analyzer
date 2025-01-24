import streamlit as st
from datetime import datetime
from fpdf import FPDF
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

# Helper function for summary
def generate_summary(data):
    # Calculate averages
    average_weight = sum(data['Weights']) / len(data['Weights'])
    avg_temperature = sum(data['Temperatures']) / len(data['Temperatures'])
    avg_pressure = sum(data['Pressures']) / len(data['Pressures'])
    
    # Temperature categorization logic
    temp_remarks = "Cold storage" if avg_temperature <= 5 else "Non-refrigerated storage"
    
    # Pressure categorization logic
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
        f"The consignment {data['Consignment Number']}, "
        f"inspected by {data['Inspector Name']} "
        f"on {data['Timestamp']}, "
        f"had an average crate weight of {average_weight:.2f} kg. "
        f"The recorded average temperature was {avg_temperature:.2f} °C, "
        f"indicating it was stored in '{temp_remarks}' at the time of inspection. "
        f"Additionally, the average pressure was measured at {avg_pressure:.2f} kgf/cm², "
        f"signifying that the consignment is '{pressure_remarks}'."
    )

    return summary, remarks

# CustomPDF class definition
class CustomPDF(FPDF):
    def header(self):
        self.set_fill_color(144, 238, 144)  # Parrot Light Green
        self.rect(0, 0, 210, 40, 'F')  # Full-width header
        self.image("https://www.ninjacart.com/wp-content/uploads/2023/10/cropped-Group-207-1.png", x=10, y=5, w=190)
        self.ln(40)

    def footer(self):
        self.set_y(-30)  # Move the footer up to make space for the address
        self.set_font("Arial", "I", 8)
        self.cell(0, 5, "Address: 2nd Floor Tower E, Helios Business Park, New Horizon College Bus Stop, Service Road, Chandana, Kadubeesanahalli, Bengaluru, 560103", 0, 1, "C")
        self.cell(0, 10, "For queries & bookings, contact: +91 9586954665", align="C")

    def add_main_heading(self, title):
        self.set_xy(10, 50)
        self.set_font("Arial", "B", 20)
        self.cell(190, 10, title, 0, 1, "C")
        self.ln(5)  # Reduced space

    def add_basic_details(self, data):
        self.set_font("Arial", size=12)
        
        info_types = ["Consignment Number", "Inspector Name", "Apple Variety", "Apple Color", "Crate Type", "Timestamp"]
        values = [data["Consignment Number"], data["Inspector Name"], data["Apple Variety"], data["Apple Color"], data["Crate Type"], data["Timestamp"]]

        for info, value in zip(info_types, values):
            self.set_fill_color(255, 200, 0)  # Light Orange background color
            self.cell(45, 8, info + ":", border=1, fill=True)
            self.cell(0, 8, value, border=1, ln=True)

        self.ln(5)  # Reduced space

    def add_summary_table(self, data, summary, remarks):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(144, 238, 144)

        # Define column widths
        col_widths = {
            "category": 25,  # Reduced from 30
            "values": 35,    # Reduced from 40
            "avg_value": 30,
            "reference_range": 60,
            "remarks": 40    # Increased from 30
        }

        # Column headers
        self.cell(col_widths["category"], 10, "Category", 1, 0, "C", fill=True)
        self.cell(col_widths["values"], 10, "Values", 1, 0, "C", fill=True)
        self.cell(col_widths["avg_value"], 10, "Average Value", 1, 0, "C", fill=True)
        self.cell(col_widths["reference_range"], 10, "Reference Range", 1, 0, "C", fill=True)
        self.cell(col_widths["remarks"], 10, "Remarks", 1, 1, "C", fill=True)

        self.set_font("Arial", size=10)
        self.set_fill_color(240, 240, 240)

        categories = ["Weight", "Temperature", "Pressure"]
        values = [
            '\n'.join(f"{w} kg" for w in data['Weights']),
            '\n'.join(f"{t} °C" for t in data['Temperatures']),
            '\n'.join(f"{p} kgf/cm²" for p in data['Pressures'])
        ]
        avg_values = [
            f"{sum(data['Weights']) / len(data['Weights']):.2f} kg",
            f"{sum(data['Temperatures']) / len(data['Temperatures']):.2f} °C",
            f"{sum(data['Pressures']) / len(data['Pressures']):.2f} kgf/cm²",
        ]
        ranges = [
            "NA",
            "-2°C to 5°C - Cold storage\n> 5°C - Non-refrigerated storage",
            "> 6.35 - Hard\n5 to 6.35 - Firm\n3.65 to 5 - Firm Ripe\n< 3.65 - Ripe"
        ]

        for i in range(3):
            # Calculate the maximum number of lines in the cells for the current row
            value_lines = len(values[i].split('\n'))
            range_lines = len(ranges[i].split('\n'))
            remark_lines = len(remarks[categories[i]].split('\n'))
            max_lines = max(value_lines, range_lines, remark_lines)
            cell_height = 5 * max_lines  # Adjust line height

            # Print cells, ensuring the same height for all cells in the row
            self.cell(col_widths["category"], cell_height, categories[i], 1, 0, "C", fill=True)
            
            x, y = self.get_x(), self.get_y()
            self.multi_cell(col_widths["values"], cell_height / value_lines, values[i], border=1, align="C", fill=True)
            self.set_xy(x + col_widths["values"], y)
            
            self.cell(col_widths["avg_value"], cell_height, avg_values[i], 1, 0, "C", fill=True)
            
            x, y = self.get_x(), self.get_y()
            self.multi_cell(col_widths["reference_range"], cell_height / range_lines, ranges[i], border=1, align="C", fill=True)
            self.set_xy(x + col_widths["reference_range"], y)
            
            self.cell(col_widths["remarks"], cell_height, remarks[categories[i]], 1, 1, "C", fill=True)

        self.ln(5)  # Reduced space

    def add_note_section(self):
        self.set_font("Arial", "I", 10)
        self.multi_cell(0, 10, "Note: This report is generated based testing 3 boxes from the consignment")

def generate_pdf(consignment_number, data, summary, remarks):
    pdf = CustomPDF()
    pdf.add_page()

    pdf.add_main_heading("Apple Quality Report")
    pdf.add_basic_details(data)

    # Add second header "Summary"
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Summary", 0, 1, "C")
    pdf.ln(5)

    pdf.add_summary_table(data, summary, remarks)

    # Add dynamic lines after the table
    average_weight = sum(data['Weights']) / len(data['Weights'])
    avg_temperature = sum(data['Temperatures']) / len(data['Temperatures'])
    avg_pressure = sum(data['Pressures']) / len(data['Pressures'])

    dynamic_lines = (
        f"The consignment {data['Consignment Number']}, "
        f"inspected by {data['Inspector Name']} "
        f"on {data['Timestamp']}, "
        f"had an average crate weight of {average_weight:.2f} kg. "
        f"The recorded average temperature was {avg_temperature:.2f} °C, "
        f"indicating it was stored in '{remarks['Temperature']}' at the time of inspection. "
        f"Additionally, the average pressure was measured at {avg_pressure:.2f} kgf/cm², "
        f"signifying that the consignment is '{remarks['Pressure']}'."
    )

    # Add the "Overview of Results:" header and dynamic lines
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Overview of Results:", ln=True)  # Bold header for "Overview of Results:"
    pdf.set_font("Arial", size=10)  # Regular font for the text
    pdf.multi_cell(0, 5, dynamic_lines)
    pdf.ln(5)

    # Add the note section
    pdf.add_note_section()

    file_name = f"Consignment_{consignment_number}_Report.pdf"
    pdf.output(file_name)
    return file_name

# Streamlit App
st.title("Ninja Apple Quality Inspection")
#st.header("Enter Quality Parameters")

# Firebase Initialization
cred_dict = get_credentials()
db = initialize_firebase(cred_dict) if cred_dict else None

# Form for Inputs
with st.form("input_form"):
    # Inputs inside the form
    consignment_number = st.text_input(
        "Enter Consignment Number* (e.g. DF-AMCU9352772, VPI-AMCU9354567)",
        placeholder="Enter consignment number",
        max_chars=30,
        help="Maximum 30 characters.",
    )
    inspector_name = st.text_input(
        "Enter Inspector Name*",
        placeholder="Enter inspector name",
        max_chars=15,
        help="Maximum 15 characters.",
    )
    
    # New Inputs
    apple_variety = st.selectbox(
        "Choose the Apple Variety*",
        ["", "I-Apple", "Turkey - Apple"],
        index=0,
        key='apple_variety'
    )
    
    apple_color = st.selectbox(
        "Choose Apple Color*",
        ["", "Red", "Dark Red", "Light Red"]
    )
    
    crate_type = st.selectbox(
        "Choose Crate Type*",
        ["", "White Crate", "Green Crate"],
        index=0,
        key='crate_type'
    )

    weights = [
        st.text_input(f"Enter Weight of Box {i + 1} (kg) *", key=f"weight_{i}")
        for i in range(3)
    ]
    temperatures = [
        st.text_input(f"Enter Temperature of Apple {i + 1} (°C) *", key=f"temperature_{i}")
        for i in range(3)
    ]
    pressures = [
        st.text_input(f"Enter Pressure of Apple {i + 1} (kgf/cm²) *", key=f"pressure_{i}")
        for i in range(3)
    ]

    #file = st.file_uploader("Upload Image/Video/PDF (Optional)", type=["jpg", "jpeg", "png", "mp4", "pdf"])

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
    if not apple_variety:
        errors.append("Apple variety is required.")
    if not apple_color:
        errors.append("Apple color is required.")
    if not crate_type:
        errors.append("Crate type is required.")
    if not all(weights):
        errors.append("All weight values are required.")
    if not all(temperatures):
        errors.append("All temperature values are required.")
    if not all(pressures):
        errors.append("All pressure values are required.")

    # Validate that weights, temperatures, and pressures are valid numbers
    for weight in weights:
        try:
            float(weight)
        except ValueError:
            errors.append(f"Weight value '{weight}' is not a valid number.")
    
    for temp in temperatures:
        try:
            float(temp)
        except ValueError:
            errors.append(f"Temperature value '{temp}' is not a valid number.")
    
    for pressure in pressures:
        try:
            float(pressure)
        except ValueError:
            errors.append(f"Pressure value '{pressure}' is not a valid number.")

    # Proceed if no errors
    if not errors:
        # Prepare data for processing
        data = {
            "Consignment Number": consignment_number,
            "Inspector Name": inspector_name,
            "Apple Variety": apple_variety,
            "Apple Color": apple_color,
            "Crate Type": crate_type,
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

        # Clear session state to prompt user input again
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    else:
        # Display the error messages
        st.error("Please correct the following errors:")
        for error in errors:
            st.write(error)
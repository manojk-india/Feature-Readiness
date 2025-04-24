import pandas as pd
from fpdf import FPDF
import ast

def clean_latin1(text):
    if not isinstance(text, str):
        return ''
    # Replace common curly quotes and dashes with ASCII equivalents
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',  # single/double curly quotes
        '\u2013': '-', '\u2014': '-',                                 # en-dash, em-dash
        '\u2026': '...',                                              # ellipsis
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Remove any remaining non-latin1 characters
    return text.encode('latin-1', 'replace').decode('latin-1')

class PDFReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, 'Acceptance Criteria Improvement Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_acceptance_improvement_report(csv_file="data/Final_API.csv", pdf_file="Report/acceptance_report.pdf"):
    df = pd.read_csv(csv_file)

    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font('helvetica', '', 11)  # Use built-in font

    for idx, row in df.iterrows():
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, clean_latin1(f"Feature Key: {row.get('key', '')}"), ln=True)
        pdf.set_font('helvetica', '', 11)

        pdf.multi_cell(0, 8, clean_latin1(f"Summary: {row.get('summary', '')}"))
        pdf.ln(1)
        pdf.multi_cell(0, 8, clean_latin1(f"Description: {row.get('description', '')}"))
        pdf.ln(1)
        pdf.multi_cell(0, 8, clean_latin1(f"Acceptance Criteria: {row.get('acceptance_crieteria', '')}"))
        pdf.ln(5)

        # Parse the acceptance improvement dictionary string safely
        improvement_str = row.get('Acceptance_improvement', '{}')
        try:
            improvement_dict = ast.literal_eval(improvement_str) if isinstance(improvement_str, str) else {}
        except Exception:
            improvement_dict = {}

        strengths = improvement_dict.get('strengths', [])
        improvement_areas = improvement_dict.get('improvement_areas', [])
        revised_version = improvement_dict.get('revised_version', '')

        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 10, clean_latin1('Strengths:'), ln=True)
        pdf.set_font('helvetica', '', 11)
        if strengths:
            for s in strengths:
                pdf.multi_cell(0, 8, clean_latin1(f"- {s}"))
        else:
            pdf.cell(0, 8, 'None', ln=True)

        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 10, clean_latin1('Improvement Areas:'), ln=True)
        pdf.set_font('helvetica', '', 11)
        if improvement_areas:
            for imp in improvement_areas:
                pdf.multi_cell(0, 8, clean_latin1(f"- {imp}"))
        else:
            pdf.cell(0, 8, 'None', ln=True)

        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 10, clean_latin1('Revised Version:'), ln=True)
        pdf.set_font('helvetica', '', 11)
        if revised_version:
            pdf.multi_cell(0, 8, clean_latin1(revised_version))
        else:
            pdf.cell(0, 8, 'None', ln=True)

        pdf.ln(10)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)

    pdf.output(pdf_file)

# Usage:
# create_acceptance_improvement_report('your_input.csv', 'acceptance_report.pdf')


create_acceptance_improvement_report()
#!/usr/bin/env python3
"""Generate roetfilter planning PDF for Volvo V40"""

from fpdf import FPDF
from datetime import datetime

class PlanningPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 20)
        self.cell(0, 15, 'Roetfilter Regeneratie Planning', align='C', ln=True)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Volvo V40 Diesel - Keuring 26 februari 2026', align='C', ln=True)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Gegenereerd op {datetime.now().strftime("%d/%m/%Y")}', align='C')

pdf = PlanningPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# Problem section
pdf.set_font('Helvetica', 'B', 14)
pdf.set_text_color(180, 0, 0)
pdf.cell(0, 10, 'Probleem', ln=True)
pdf.set_text_color(0, 0, 0)
pdf.set_font('Helvetica', '', 11)
pdf.multi_cell(0, 7, 
    'Deeltjestest te hoog bij vorige keuring. Roetfilter is 2 jaar oud (nog jong). '
    'Oorzaak: te weinig kilometers, altijd lage toeren. Filter heeft regeneratie nodig.')
pdf.ln(5)

# Solution section
pdf.set_font('Helvetica', 'B', 14)
pdf.set_text_color(0, 120, 0)
pdf.cell(0, 10, 'Oplossing: DIY Regeneratie (90%+ slaagkans)', ln=True)
pdf.set_text_color(0, 0, 0)
pdf.set_font('Helvetica', '', 11)
pdf.multi_cell(0, 7,
    '1. DPF/roetfilter additief kopen (bv. Liqui Moly, Wynn\'s, STP)\n'
    '2. Toevoegen aan volle tank diesel\n'
    '3. Minstens 3 snelwegritten maken van 30-45 min\n'
    '4. Rijden op 2500-3500 toeren (regeneratie-zone)')
pdf.ln(8)

# Planning table
pdf.set_font('Helvetica', 'B', 14)
pdf.set_text_color(0, 0, 150)
pdf.cell(0, 10, 'Planning', ln=True)
pdf.set_text_color(0, 0, 0)

# Table header
pdf.set_fill_color(230, 230, 230)
pdf.set_font('Helvetica', 'B', 11)
pdf.cell(35, 10, 'Datum', border=1, fill=True)
pdf.cell(70, 10, 'Actie', border=1, fill=True)
pdf.cell(85, 10, 'Details', border=1, fill=True, ln=True)

# Table rows
pdf.set_font('Helvetica', '', 10)
rows = [
    ('Za 8 feb', 'Additief + Rit 1', 'Additief kopen & toevoegen. Eerste snelwegrit 45 min.'),
    ('Za 15 feb', 'Rit 2', 'Tweede regeneratierit. E40 richting Gent of Brussel.'),
    ('Za 22 feb', 'Rit 3 (check)', 'Laatste rit voor keuring. Check of motor soepel loopt.'),
    ('Do 26 feb', 'KEURING', 'Deeltjestest moet nu slagen!'),
]

for date, action, details in rows:
    # Highlight keuring row
    if 'KEURING' in action:
        pdf.set_fill_color(255, 255, 200)
        pdf.set_font('Helvetica', 'B', 10)
        fill = True
    else:
        fill = False
        pdf.set_font('Helvetica', '', 10)
    
    pdf.cell(35, 12, date, border=1, fill=fill)
    pdf.cell(70, 12, action, border=1, fill=fill)
    pdf.cell(85, 12, details, border=1, fill=fill, ln=True)

pdf.ln(8)

# Tips section
pdf.set_font('Helvetica', 'B', 14)
pdf.set_text_color(100, 100, 0)
pdf.cell(0, 10, 'Tips voor de ritten', ln=True)
pdf.set_text_color(0, 0, 0)
pdf.set_font('Helvetica', '', 11)

tips = [
    'Rij minstens 30-45 minuten aaneengesloten op de snelweg',
    'Houd 2500-3500 toeren aan (gebruik sport-modus of lagere versnelling)',
    'Vermijd stop-and-go verkeer tijdens regeneratie',
    'Tank vol voor je begint (additief werkt beter met volle tank)',
    'Rij bij voorkeur als motor al warm is',
]

for tip in tips:
    pdf.cell(5, 7, chr(149))  # bullet point
    pdf.cell(0, 7, tip, ln=True)

pdf.ln(5)

# Backup section
pdf.set_font('Helvetica', 'B', 12)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 10, 'Backup plan (als DIY niet werkt)', ln=True)
pdf.set_text_color(60, 60, 60)
pdf.set_font('Helvetica', '', 10)
pdf.multi_cell(0, 6,
    'Roetfilter Center - roetfilter-center.be - Bedient regio Oudenaarde\n'
    'Auto-onderdelen: TAS, Kloosterstraat 83, Erwetegem - 09/360 49 92')

# Save
output_path = '/home/wouter/clawd/roetfilter-planning.pdf'
pdf.output(output_path)
print(f'PDF saved to: {output_path}')

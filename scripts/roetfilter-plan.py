#!/usr/bin/env python3
"""Generate roetfilter planning PDF for Wouter's V40"""

from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'Roetfilter Regeneratie Planning', align='C', ln=True)
        self.set_font('Helvetica', '', 10)
        self.cell(0, 6, 'Volvo V40 Diesel - Keuring 26 februari 2026', align='C', ln=True)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Gegenereerd door Rez - {datetime.now().strftime("%d/%m/%Y")}', align='C')

pdf = PDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# Situatie
pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 10, 'Situatie', ln=True)
pdf.set_font('Helvetica', '', 11)
situatie = [
    ('Probleem', 'Deeltjestest te hoog bij onderhoud'),
    ('Oorzaak', 'Te weinig kilometers, altijd lage toeren'),
    ('Filter leeftijd', '2 jaar (nog jong)'),
    ('Lampje', 'Brandt niet'),
    ('Keuring', '26 februari 2026'),
    ('Slaagkans DIY', '90%+ bij correcte uitvoering'),
]
for label, value in situatie:
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(50, 7, f'{label}:', ln=False)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, value, ln=True)
pdf.ln(5)

# Benodigdheden
pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 10, 'Benodigdheden', ln=True)
pdf.set_font('Helvetica', '', 11)
items = [
    'DPF Additief (bv. Liqui Moly DPF Cleaner of Wynn\'s DPF Regenerator)',
    '2 flesjes kopen (~EUR 20-25 per stuk)',
    'Verkrijgbaar bij: Hubo, AutoDoc, Halfords, auto-onderdelen winkel',
]
for item in items:
    pdf.cell(5, 7, '', ln=False)
    pdf.cell(0, 7, f'- {item}', ln=True)
pdf.ln(5)

# Planning
pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 10, 'Planning', ln=True)

planning = [
    ('Week 1 - Za 8 feb', 'Eerste regeneratierit', [
        'Additief kopen',
        'Tank bijna leeg rijden',
        'Additief toevoegen + vol tanken',
        'Snelwegrit 50-60 km (Zottegem > Gent > Antwerpen > terug)',
    ]),
    ('Week 2 - Za 15 feb', 'Tweede regeneratierit', [
        'Optioneel: nieuwe dosis additief bij tanken',
        'Opnieuw snelwegrit 50-60 km',
        'Houd 2500-3500 toeren aan',
    ]),
    ('Week 3 - Za 22 feb', 'Laatste rit voor keuring', [
        'Additief toevoegen bij tanken',
        'Finale snelwegrit',
        'Filter zou nu schoon moeten zijn',
    ]),
    ('Wo 26 feb', 'Keuring', [
        'Vingers kruisen!',
    ]),
]

for date, title, actions in planning:
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, f'{date}: {title}', ln=True, fill=True)
    pdf.set_font('Helvetica', '', 11)
    for action in actions:
        pdf.cell(10, 6, '', ln=False)
        pdf.cell(0, 6, f'- {action}', ln=True)
    pdf.ln(2)

pdf.ln(3)

# Tips voor de rit
pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 10, 'Tips voor de snelwegrit', ln=True)
pdf.set_font('Helvetica', '', 11)
tips = [
    'Rij minstens 45-60 minuten ononderbroken',
    'Houd 2500-3500 toeren aan (niet alleen cruise control!)',
    'Varieer snelheid: gas geven, inhalen, accelereren',
    'Doel: uitlaattemperatuur >500C voor regeneratie',
    'Route suggestie: E40/E17 richting Gent-Antwerpen',
]
for tip in tips:
    pdf.cell(5, 7, '', ln=False)
    pdf.cell(0, 7, f'- {tip}', ln=True)
pdf.ln(5)

# Backup plan
pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 10, 'Backup plan (als DIY niet werkt)', ln=True)
pdf.set_font('Helvetica', '', 11)
backup = [
    'Roetfilter Center - bedient ook Oudenaarde (dichtbij Zottegem)',
    'Website: roetfilter-center.be',
    'Diagnose: EUR 50 (terugbetaald bij herstelling)',
    'Professionele reiniging: EUR 195-250',
    'Binnen 24u klaar, ophaalservice beschikbaar',
]
for item in backup:
    pdf.cell(5, 7, '', ln=False)
    pdf.cell(0, 7, f'- {item}', ln=True)

# Output
output_path = '/home/wouter/clawd/roetfilter-planning.pdf'
pdf.output(output_path)
print(f'PDF saved to {output_path}')

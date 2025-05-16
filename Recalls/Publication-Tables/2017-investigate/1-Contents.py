""" 
GOAL: PRODUCE COTENTS PAGE FOR RECALL TABLES IN THE OMSQ.
By Eric Nyame, 17/04/2024
"""

# Create workbook and the contents tab

output_work_book = f'Tables_{year}Q{qtr}.xlsx'
workbook = Workbook()
contents_sheet = workbook.active # active sheet
contents_sheet.title = 'Contents'
contents_sheet['A1'] = 'Contents'
contents_sheet['A1'].font = Font(name='Arial', size=16, bold=True)

# Save workbook
workbook.save(output_work_book)
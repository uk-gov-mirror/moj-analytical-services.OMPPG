""" 
GOAL: PRODUCE TABLE 3 - CONTINUATION FROM TABLE 2 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Calculate summaries for the combined DataFrame
table_3_summary = table_3_func(recalls, probation_region, hdc_values)

len(table_3_summary) # 225
table_3_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_3_summary['Probation region'] = table_3_summary['Probation region'].astype(CategoricalDtype(categories=probation_region, ordered=True))
table_3_summary['Recall category'] = table_3_summary['Recall category'].astype(CategoricalDtype(categories=hdc_values, ordered=True))

# Pivot the final summary DataFrame to get the desired format

table_3_df = table_3_summary.pivot_table(
    index=['Probation region', 'Recall category'],
    columns='quarter',
    values='values',
    aggfunc='sum'
).reset_index()

len(table_3_df) # 45

# Order the columns for publication
table_3_df = table_3_df[['Probation region', 'Recall category'] + quarters]

table_3_df.head(20)

# send to excel workbook

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_3_df.to_excel(writer,startrow = 4, sheet_name='Table 3',index=False)

# Load the workbook to modify Table 3
workbook = load_workbook(output_work_book)

sheet = workbook['Table 3']

# Text to be added
header_text_t3 = [
    "Table 3: Time series: number of recalls from licence, by supervising body and recall category, England and Wales [note 1][note 2]",
    "This worksheet contains one table.",
    "Link to Contents tab",
    "Source: Public Protection Unit Database (PPUD)"
]

# Write the text in the first 4 rows in column A
for i, text in enumerate(header_text_t3, start = 1):
    cell = sheet.cell(row = i, column = 1)
    cell.value = text
    if i == 1:
        cell.font = title_font
    else:
        cell.font = normal_font
    #cell.alignment = Alignment(wrap_text=False)

# Add hyperlink to the "Link to Contents tab" text
sheet.cell(row=3, column=1).hyperlink = '#Contents!A1'
sheet.cell(row=3, column=1).font = Font(name='Arial', size=12, color='0000FF', underline='single')


# Apply font and formatting for the DataFrame cells
for row in sheet.iter_rows(min_row=5, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column):
    for cell in row:
        cell.font = normal_font
        # Apply different alignment based on column index
        if cell.column <= 2:  # First three columns
            cell.alignment = Alignment(vertical='bottom',wrap_text=True)
        else:  # Columns 3 to 7
            cell.alignment = Alignment(vertical='bottom', horizontal='right',wrap_text=True)
        cell.border = None

# Format columns 2 to 7 with a thousand separator
for col in range(3, 8):
    for row in range(5, sheet.max_row + 1):
        cell = sheet.cell(row=row, column=col)
        cell.number_format = '#,##0'

# Set consistent column widths
set_fixed_column_widths(sheet, start_row=5, columns=range(1, 8), gap_width=5)

# Bold headers (row 5), set row height, and wrap text for the last header cell
for cell in sheet[5]:
    cell.font = header_font
    
sheet.row_dimensions[5].height = 46.8
#sheet.cell(row=5, column=sheet.max_column).alignment = Alignment(wrap_text=True)

# Loop through column 3 to find 'All recalls' and set row height
for row in range(5, sheet.max_row + 1):
    if sheet.cell(row=row, column=2).value == 'All recalls':
        sheet.row_dimensions[row].height = 24.9
        
# Save the modified workbook
workbook.save(output_work_book)
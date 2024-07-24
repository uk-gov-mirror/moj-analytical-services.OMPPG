""" 
GOAL: PRODUCE TABLE 8 - CONTINUATION FROM TABLE 7 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Get final UAL data for the last 5 quarters ----------------------------------------------------


# ---------------Table 5.8: Total number of offenders not returned to custody after licence recall, by supervising body, and length of time since recall

ual['HOWLONG'].value_counts()
ual['HOWLONG'] = ual['HOWLONG'].map(howlong_mapping).fillna('Unknown')
ual['HOWLONG'].value_counts()

# Calculate summaries for the combined DataFrame
table_8_summary = table_8_func(ual, supervising_body,howlong_vals)

len(table_8_summary) # 120
table_8_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_8_summary['Supervising body'] = table_8_summary['Supervising body'].astype(CategoricalDtype(categories=supervising_body, ordered=True))
table_8_summary['Time since recall'] = table_8_summary['Time since recall'].astype(CategoricalDtype(categories=howlong_vals, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_8_df = table_8_summary.pivot_table(
    index=['Supervising body','Time since recall'],
    columns='text',
    values='values'
).reset_index()

len(table_8_df) # 24

# Order the columns for publication
table_8_df = table_8_df[['Supervising body','Time since recall'] + rec_1984_not_returned_by]

table_8_df

with pd.ExcelWriter(output_work_book,engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
    table_8_df.to_excel(writer,startrow = 4, sheet_name='Table 8',index=False)

# Load the workbook to modify it
workbook = load_workbook(output_work_book)

# Modify the Table 5_12
sheet = workbook['Table 8']

# Text to be added
header_text_t8 = [
    "Table 8: Time series: number of offenders not returned to custody after licence recall, by supervising body and length of time since recall, England and Wales [note 2]",
    "This worksheet contains one table.",
    "Link to Contents tab",
    "Source: Public Protection Unit Database (PPUD)"
]

# Write the text in the first 4 rows in column A
for i, text in enumerate(header_text_t8, start = 1):
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
        else:  # number columns
            cell.alignment = Alignment(vertical='bottom', horizontal='right',wrap_text=True)
        cell.border = None

# Format columns 4 to 8 with a thousand separator
for col in range(3, 8):
    for row in range(5, sheet.max_row + 1):
        cell = sheet.cell(row=row, column=col)
        cell.number_format = '#,##0'


# Set consistent column widths
set_fixed_column_widths(sheet, start_row=5, columns=range(1, 3), gap_width=5)

sheet.column_dimensions['C'].width = 44
sheet.column_dimensions['D'].width = 44
sheet.column_dimensions['E'].width = 44
sheet.column_dimensions['F'].width = 44
sheet.column_dimensions['G'].width = 44


# Bold headers (row 5), set row height, and wrap text for the last header cell
for cell in sheet[5]:
    cell.font = header_font
    
sheet.row_dimensions[5].height = 46.8
#sheet.cell(row=5, column=sheet.max_column).alignment = Alignment(wrap_text=True)

# Loop through column 3 to find 'All recalls' and set row height
for row in range(5, sheet.max_row + 1):
    if sheet.cell(row=row, column=2).value == 'All not returned':
        sheet.row_dimensions[row].height = 24.9
        
# Save the modified workbook
workbook.save(output_work_book)

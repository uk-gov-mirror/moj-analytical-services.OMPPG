""" 
GOAL: PRODUCE TABLE 12 - CONTINUATION FROM TABLE 11 CODE.
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


# reasons[reasons['REASON_DESC'] == 'Other']['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False)
ethnicity(recalls)
recalls['ETHNICITY'].value_counts(dropna=False)
# create a list of the unique recall['QUARTER'] values ---------------

quarters = list(recalls['QUARTER'].unique()) # values like 'Month to Month Year'
quarters

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

table_12_summary = table_12_func(recalls, sex_values, sentence_values, ethnicity_vals)

len(table_12_summary) # 245
table_12_summary.head(20) # each row came from a dictionary in a list

# Order the values of the columns of the summary table
table_12_summary['Sex'] = table_12_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_12_summary['Sentence type'] = table_12_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_12_summary['Ethnicity'] = table_12_summary['Ethnicity'].astype(CategoricalDtype(categories=['All ethnicities'] + ethnicity_vals, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_12_df = table_12_summary.pivot_table(
    index=['Sex', 'Sentence type', 'Ethnicity'],
    columns='quarter',
    values='values'
).reset_index()

len(table_12_df) # 49

# Order the columns for publication

table_12_df = table_12_df[['Sex', 'Sentence type', 'Ethnicity'] + quarters]

table_12_df

# Write pivot table to excel document

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='replace') as writer:
    table_12_df.to_excel(writer,startrow = 4, sheet_name='Table 12',index=False)

# Load the workbook to modify Table 2

workbook = load_workbook(output_work_book)
sheet = workbook['Table 12']

# Header text
header_text_t12 = [
    "Table 12: Time series: number of recalls, by sex, sentence, supervising body and ethnicity, England and Wales [note 2]",
    "This worksheet contains one table.",
    "Link to Contents tab",
    "Source: Public Protection Unit Database (PPUD)"
]

# Write the text in the first 4 rows in column A
for i, text in enumerate(header_text_t12, start = 1):
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

# Table area - use normal font, left alignment for first three colums and right alighment for the numbers

for row in sheet.iter_rows(min_row=5, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column):
    for cell in row:
        cell.font = normal_font
        # Apply different alignment based on column index
        if cell.column <= 3:  # First three columns
            cell.alignment = Alignment(vertical='bottom',wrap_text=True)
        else:  # Columns 4 to 8
            cell.alignment = Alignment(vertical='bottom', horizontal='right',wrap_text=True)
        cell.border = None

# Format columns 4 to 8 with a thousand separator

for col in range(4, 9):
    for row in range(5, sheet.max_row + 1):
        cell = sheet.cell(row=row, column=col)
        cell.number_format = '#,##0'

# Set consistent column widths

set_fixed_column_widths(sheet, start_row=5, columns=range(1, 9), gap_width=5)
#set_fixed_column_widths(sheet, start_row=5, columns=range(4, 9), gap_width=)
#set_fixed_column_widths(sheet, start_row=5, columns=range(4, 9), gap_width=5)
#sheet.column_dimensions['I'].width = 25

# Bold headers (row 5) set the header row

for cell in sheet[5]:
    cell.font = header_font
    
sheet.row_dimensions[5].height = 46.8

# Loop through column 3 to find 'All recalls' and set row height to distinquish combinations

for row in range(5, sheet.max_row + 1):
    if sheet.cell(row=row, column=3).value == 'All ethnicities':
        sheet.row_dimensions[row].height = 24.9
        
# Save the modified workbook

workbook.save(output_work_book)

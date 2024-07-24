""" 
GOAL: PRODUCE TABLE 5 - CONTINUATION FROM TABLE 4 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


# ---------------Table 5.4: Number of returns to custody after licence recall, by sex, supervising body, and sentence length

table_5_condition = ( (recalls['UAL_FLAG'] == True) |
                     (
                        (recalls['LICENCE_REVOKE_DATE'].dt.year < 2015) & 
                        (
                            (recalls['RTC_DATE'] > recalls['RETURN_BY']) | 
                            (recalls['RTC_DATE'].isna())
                        )
                     )
                   )

# Create a 'recalled in and not returned' by headings

recalls['RECALLED_IN_NOT_RETURNED_BY'] = recalls.apply(lambda x: 'Recalled in ' + str(x['QUARTER']) + ' not returned by ' + str(x['RETURN_BY_STR']), axis=1)

recalls['RECALLED_IN_NOT_RETURNED_BY'].unique()

# Define unique values Table 5
rec_not_return_by = list(recalls['RECALLED_IN_NOT_RETURNED_BY'].unique())

# Calculate summaries for the combined DataFrame
table_5_summary = table_5_func(recalls, sex_values, sentence_values)

len(table_5_summary) # 75
table_5_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_5_summary['Sex'] = table_5_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_5_summary['Sentence type'] = table_5_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_5_df = table_5_summary.pivot_table(
    index=['Sex', 'Sentence type'],
    columns='text',
    values='values',
    aggfunc='sum'
).reset_index()

len(table_5_df) # 15

# Order the columns for publication
table_5_df = table_5_df[['Sex', 'Sentence type'] + rec_not_return_by]

table_5_df

# Output
with pd.ExcelWriter(output_work_book,engine='openpyxl', mode ='a',if_sheet_exists='overlay') as writer:
    table_5_df.to_excel(writer,startrow = 4, sheet_name='Table 5',index=False)


# Load the workbook to modify it
workbook = load_workbook(output_work_book)

# Modify the Table 5
sheet = workbook['Table 5']

# Text to be added
header_text_t5 = [
    "Table 5: Time series: number of offenders not returned to custody after licence recall, by sex and sentence, England and Wales [note 2]",
    "This worksheet contains one table.",
    "Link to Contents tab",
    "Source: Public Protection Unit Database (PPUD)"
]

# Write the text in the first 4 rows in column A
for i, text in enumerate(header_text_t5, start = 1):
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
        else:  # Columns 4 to 8
            cell.alignment = Alignment(vertical='bottom', horizontal='right',wrap_text=True)
        cell.border = None

# Format columns 4 to 8 with a thousand separator
for col in range(3, 8):
    for row in range(5, sheet.max_row + 1):
        cell = sheet.cell(row=row, column=col)
        cell.number_format = '#,##0'

# Set consistent column widths
set_fixed_column_widths(sheet, start_row=5, columns=range(1, 3), gap_width=5)
sheet.column_dimensions['C'].width = 31.22
sheet.column_dimensions['D'].width = 31.22
sheet.column_dimensions['E'].width = 31.22
sheet.column_dimensions['F'].width = 31.22
sheet.column_dimensions['G'].width = 31.22


# Bold headers (row 5), set row height, and wrap text for the last header cell
for cell in sheet[5]:
    cell.font = header_font
    
sheet.row_dimensions[5].height = 46.8

# Loop through column 3 to find 'All recalls' and set row height
for row in range(5, sheet.max_row + 1):
    if sheet.cell(row=row, column=2).value == 'All sentence types':
        sheet.row_dimensions[row].height = 24.9
        
# Save the modified workbook
workbook.save(output_work_book)

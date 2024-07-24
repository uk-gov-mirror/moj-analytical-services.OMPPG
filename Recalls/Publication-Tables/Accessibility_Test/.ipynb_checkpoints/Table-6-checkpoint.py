""" 
GOAL: PRODUCE TABLE 6 - CONTINUATION FROM TABLE 5 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


# ---------------Table 5.6: Number of recalls from licence by sentence type, and process time

# correct recall process and recall target

recalls['RECALL_PROCESS'].value_counts(dropna=False)
recalls['RECALL_TARGET'].value_counts(dropna=False)

recalls['RECALL_TARGET'] = recalls['RECALL_TARGET'].str.strip()
recalls['RECALL_TARGET'].value_counts(dropna=False)

recalls.loc[recalls['CUSTODYTYPE'].isin(['IPP','Life']),'RECALL_PROCESS'] = 'Indeterminate Emergency'
recalls.loc[recalls['RECALL_PROCESS'] == 'Emergency','RECALL_PROCESS'] = 'Determinate Emergency'
recalls.loc[recalls['RECALL_PROCESS'] == 'Standard','RECALL_PROCESS'] = 'Determinate Standard'

recalls.loc[recalls['RECALL_TARGET'] == 'd. Resolved','RECALL_TARGET'] = 'b. Returned outside target'

recalls['RECALL_TARGET_2'] = recalls.apply(lambda x: x['RECALL_TARGET'][2:].strip(), axis=1)


# Create 'recall target date' headings

recalls['RECALLED_IN_STATUS_ON'] = recalls.apply(lambda x: 'Recalled in ' + str(x['QUARTER']) + ' returned by ' + str(x['RETURN_BY_STR']), axis=1)

recalls['RECALLED_IN_STATUS_ON'].unique()

# Define unique values Table 5
rec_in_status_on = list(recalls['RECALLED_IN_STATUS_ON'].unique())
rec_in_status_on

# Calculate summaries for the combined DataFrame
table_6_summary = table_6_func(recalls, sex_values, sentence_values)

len(table_6_summary) # 80
table_6_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_6_summary['Recall process'] = table_6_summary['Recall process'].astype(CategoricalDtype(categories=rec_process, ordered=True))
table_6_summary['Return status'] = table_6_summary['Return status'].astype(CategoricalDtype(categories=return_statuses, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_6_df = table_6_summary.pivot_table(
    index=['Recall process', 'Return status'],
    columns='text',
    values='values'
).reset_index()

len(table_6_df) # 16

# Order the columns for publication
table_6_df = table_6_df[['Recall process', 'Return status'] + rec_in_status_on]

table_6_df

# Output
with pd.ExcelWriter(output_work_book,engine='openpyxl', mode ='a',if_sheet_exists='replace') as writer:
    table_6_df.to_excel(writer,startrow = 4, sheet_name='Table 6',index=False)


# Load the workbook to modify it
workbook = load_workbook(output_work_book)

# Modify the Table 6
sheet = workbook['Table 6']

# Text to be added
header_text_t6 = [
    "Table 6: Time series: Table 5.6: Number of recalls from licence by recall process and return to custody status, England and Wales [note 4][note 5]",
    "This worksheet contains one table.",
    "Link to Contents tab",
    "Source: Public Protection Unit Database (PPUD)"
]

# Write the text in the first 4 rows in column A
for i, text in enumerate(header_text_t6, start = 1):
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
    if sheet.cell(row=row, column=2).value == 'All return statuses':
        sheet.row_dimensions[row].height = 24.9
        
# Save the modified workbook
workbook.save(output_work_book)

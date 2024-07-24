""" 
GOAL: PRODUCE TABLE 9 - CONTINUATION FROM TABLE 8 CODE
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


# ---------------Table 5.9: Total number of offenders not returned to custody after licence recall, by offence

# Correct offence groups
ual['OFFENCEGRP_NEW'].unique()

ual.loc[ual['OFFENCEGRP_NEW']=='Violence Against The Person','OFFENCEGRP_NEW'] = 'Violence against the person'
ual.loc[ual['OFFENCEGRP_NEW']=='Sexual Offences','OFFENCEGRP_NEW'] = 'Sexual offences'
ual.loc[ual['OFFENCEGRP_NEW']=='Drug Offences','OFFENCEGRP_NEW'] = 'Drug offences'
ual.loc[ual['OFFENCEGRP_NEW']=='Fraud offences','OFFENCEGRP_NEW'] = 'Fraud'
ual.loc[ual['OFFENCEGRP_NEW']=='Summary Motoring','OFFENCEGRP_NEW'] = 'Summary motoring'
ual.loc[ual['OFFENCEGRP_NEW']=='Public Order Offences','OFFENCEGRP_NEW'] = 'Public order offences'
ual.loc[ual['OFFENCEGRP_NEW']=='Criminal Damage and Arson','OFFENCEGRP_NEW'] = 'Criminal damage and arson'
ual.loc[ual['OFFENCEGRP_NEW']=='Miscellaneous Crimes Against Society','OFFENCEGRP_NEW'] = 'Miscellaneous crimes against society'
ual.loc[ual['OFFENCEGRP_NEW'].isna(),'OFFENCEGRP_NEW'] = 'Offence not recorded'

# Correct offence subgroups
ual['OFFENCESUBGROUP_NEW'].unique()

ual['OFFENCESUBGROUP_NEW'] = ual['OFFENCESUBGROUP_NEW'].str.strip()

ual.loc[ual['OFFENCESUBGROUP_NEW'].isna(),'OFFENCESUBGROUP_NEW'] = 'Missing'
ual.loc[ual['OFFENCESUBGROUP_NEW']=='Stalking and Harassment','OFFENCESUBGROUP_NEW'] = 'Stalking and harassment'
ual.loc[ual['OFFENCESUBGROUP_NEW']=='Gross indecency with children','OFFENCESUBGROUP_NEW'] = 'Other sexual offences'

# Calculate summaries for the combined DataFrame
table_9_summary = table_9_func(ual, offence_groups,vatp_subs,sexual_offence_subs)

len(table_9_summary) # 100
table_9_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_9_summary['Offence group'] = table_9_summary['Offence group'].astype(CategoricalDtype(categories=offence_groups, ordered=True))
table_9_summary['Offence subgroup'] = table_9_summary['Offence subgroup'].astype(CategoricalDtype(categories=['All offences'] + vatp_subs + sexual_offence_subs, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_9_df = table_9_summary.pivot_table(
    index=['Offence group','Offence subgroup'],
    columns='text',
    values='values'
).reset_index()

len(table_9_df) # 20

# Order the columns for publication
table_9_df = table_9_df[['Offence group','Offence subgroup'] + rec_1984_not_returned_by]

table_9_df

with pd.ExcelWriter(output_work_book,engine='openpyxl',mode='a',if_sheet_exists='replace') as writer:
    table_9_df.to_excel(writer,startrow = 4, sheet_name='Table 9',index=False)

# Load the workbook to modify it
workbook = load_workbook(output_work_book)

# Modify the Table 5_12
sheet = workbook['Table 9']

# Text to be added
header_text_t9 = [
    "Table 9: number of offenders not returned to custody after licence recall, by offence, England and Wales",
    "This worksheet contains one table.",
    "Link to Contents tab",
    "Source: Public Protection Unit Database (PPUD)"
]

# Write the text in the first 4 rows in column A
for i, text in enumerate(header_text_t9, start = 1):
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
    if ( (sheet.cell(row=row, column=1).value in ['All offences',
                                                    'Violence against the person',
                                                    'Sexual offences',
                                                    'Robbery']) and 
        (sheet.cell(row=row, column=2).value == 'All offences')
       ):
        sheet.row_dimensions[row].height = 24.9
        
# Save the modified workbook
workbook.save(output_work_book)

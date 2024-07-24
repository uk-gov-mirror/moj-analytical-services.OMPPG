""" 
GOAL: PRODUCE TABLE 7 - CONTINUATION FROM TABLE 6 CODE
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

ual1 = pd.read_sas('s3://alpha-omppg/UAL/final_data/ual_final_2022q4.sas7bdat',encoding='latin1')
ual2 = pd.read_sas('s3://alpha-omppg/UAL/final_data/ual_final_2023q1.sas7bdat',encoding='latin1')
ual3 = pd.read_sas('s3://alpha-omppg/UAL/final_data/ual_final_2023q2.sas7bdat',encoding='latin1')
ual4 = pd.read_sas('s3://alpha-omppg/UAL/final_data/ual_final_2023q3.sas7bdat',encoding='latin1')
ual5 = pd.read_parquet('s3://alpha-omppg/UAL/final_data/ual_final_2023q4.parquet')

# uppercase the headers
for df in [ual1,ual2,ual3,ual4,ual5]:
    df.columns = df.columns.str.upper()

# Create recall end date for each file

max(ual3['LICENCE_REVOKE_DATE'])

for df in [ual1,ual2,ual3,ual4,ual5]:
    df['RECALL_END_DATE'] = max(df['LICENCE_REVOKE_DATE'])
    df['RECALL_END_DATE'] = df['RECALL_END_DATE'].dt.to_period("Q").dt.end_time
    df['RECALL_END_DATE_STR'] = df['RECALL_END_DATE'].dt.strftime('%d %b %Y')
    
# Concatenate all DataFrames into one------------------------------------------------------------------

ual = pd.concat( [ual1,ual2,ual3,ual4,ual5], ignore_index=True)
len(ual) # 11627
ual.head()
ual.info()

# Add a recall 'QUARTER' column to each DataFrame-----------------------------------------------------------------
ual['RECALL_END_DATE'].unique()

ual['QUARTER'] = ual['RECALL_END_DATE'].dt.quarter
ual['QUARTER'].unique()

# Create a recalled in and returened by headings

ual['RETURN_BY'] = ual.apply(lambda x: np.where(
    x['QUARTER'] == 4, pd.Timestamp(x['RECALL_END_DATE'].year+1,3,31), 
    np.where(x['QUARTER'] == 3, pd.Timestamp(x['RECALL_END_DATE'].year,12,31),
    np.where(x['QUARTER'] == 2, pd.Timestamp(x['RECALL_END_DATE'].year,9,30), 
             pd.Timestamp(x['RECALL_END_DATE'].year,6,30)))).item(),axis = 1)

ual['RETURN_BY_STR'] = ual['RETURN_BY'].dt.strftime('%d %b %Y')
ual['RETURN_BY_STR'].unique()

ual[['LICENCE_REVOKE_DATE','RECALL_END_DATE','QUARTER',"RETURN_BY_STR"]].head()

ual['RECALLED_IN_NOT_RETURNED_BY'] = ual.apply(lambda x: 'Recalled between 1984 and ' + str(x['RECALL_END_DATE_STR']) + ' not returned by ' + str(x['RETURN_BY_STR']), axis=1)

ual['RECALLED_IN_NOT_RETURNED_BY'].unique()
ual.head()

# Change gender values ----------------------------------------------------------------------

ual['GENDER'].unique()
ual['GENDER'] = ual['GENDER'].replace(gender_mapping)

# Create a SENTENCE column (under 12, over 12, IPP, life----------------------------------------------------------

sentence(ual) # sentece() function is from Shared.py

ual['SENTENCE'].unique()
ual.head()

# Couple of corrections
ual['SUP_BODY'].value_counts(dropna=False)

((ual['SUP_BODY'] == 'a. Probation Trust') & (ual['SENTENCE'] == 'Determinate less than 12 months')).sum() # 0 as expected

ual.loc[(ual['SUP_BODY'] == 'a. Probation Trust') & (ual['SENTENCE'] == 'Determinate less than 12 months'),'SUP_BODY'] = 'c. CRC'

ual.loc[ual['SUP_BODY'] == 'b. PS','SUP_BODY']= 'b. NPS'

ual.loc[ual['SUP_BODY'] == 'b. NPS','SUP_BODY'] = 'National probation'
ual.loc[ual['SUP_BODY'] == 'a. Probation Trust','SUP_BODY'] = 'Probation trust'
ual.loc[ual['SUP_BODY'] == 'c. CRC','SUP_BODY']= 'Community rehabilitation companies'

ual['SUP_BODY'].unique()

# Define unique values Table 7
rec_1984_not_returned_by = list(ual['RECALLED_IN_NOT_RETURNED_BY'].unique())
rec_1984_not_returned_by

# Calculate summaries for the combined DataFrame
table_7_summary = table_7_func(ual, sex_values, sentence_values)

len(table_7_summary) # 300
table_7_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_7_summary['Sex'] = table_7_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_7_summary['Sentence type'] = table_7_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_7_summary['Supervising body'] = table_7_summary['Supervising body'].astype(CategoricalDtype(categories=supervising_body, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_7_df = table_7_summary.pivot_table(
    index=['Sex', 'Sentence type', 'Supervising body'],
    columns='text',
    values='values',
    aggfunc='sum'
).reset_index()

len(table_7_df) # 60

# Order the columns for publication
table_7_df = table_7_df[['Sex', 'Sentence type', 'Supervising body'] + rec_1984_not_returned_by]

table_7_df.head(20)

with pd.ExcelWriter(output_work_book,engine='openpyxl',mode='a',if_sheet_exists='overlay') as writer:
    table_7_df.to_excel(writer,startrow = 4, sheet_name='Table 7',index=False)

# Load the workbook to modify it
workbook = load_workbook(output_work_book)

# Modify the Table 5_12
sheet = workbook['Table 7']

# Text to be added
header_text_t7 = [
    "Table 7: Time series: number of offenders not returned to custody after licence recall, by sex, sentence and supervising body, England and Wales",
    "This worksheet contains one table.",
    "Link to Contents tab",
    "Source: Public Protection Unit Database (PPUD)"
]

# Write the text in the first 4 rows in column A
for i, text in enumerate(header_text_t7, start = 1):
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
set_fixed_column_widths(sheet, start_row=5, columns=range(1, 4), gap_width=5)

sheet.column_dimensions['D'].width = 44
sheet.column_dimensions['E'].width = 44
sheet.column_dimensions['F'].width = 44
sheet.column_dimensions['G'].width = 44
sheet.column_dimensions['H'].width = 44

# Bold headers (row 5), set row height, and wrap text for the last header cell
for cell in sheet[5]:
    cell.font = header_font
    
sheet.row_dimensions[5].height = 46.8
#sheet.cell(row=5, column=sheet.max_column).alignment = Alignment(wrap_text=True)

# Loop through column 3 to find 'All recalls' and set row height
for row in range(5, sheet.max_row + 1):
    if sheet.cell(row=row, column=3).value == 'All supervising bodies':
        sheet.row_dimensions[row].height = 24.9
        
# Save the modified workbook
workbook.save(output_work_book)
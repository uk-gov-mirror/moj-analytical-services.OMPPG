""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Get last final recall data for the last 5 quarters----------------------------------------------------------------------


rec2 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023q1.sas7bdat',encoding='latin1')
rec3 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023q2.sas7bdat',encoding='latin1')
rec4 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023q3.sas7bdat',encoding='latin1')
rec5 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/Parquet/recalls_final_2023q4.parquet')
rec1 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/Parquet/recalls_final_2024q1.parquet')

# uppercase the headers
for df in [rec1,rec2,rec3,rec4,rec5]:
    df.columns = df.columns.str.upper()

# Concatenate all DataFrames into one------------------------------------------------------------------

recalls = pd.concat([rec2,rec3,rec4,rec5,rec1], ignore_index=True)
len(recalls) # 35235
recalls.head()
recalls.info()

del rec1,rec2,rec3,rec4,rec5

# Add a recall 'QUARTER' column in the form 'Month to Month year'-------------------------------------------
# this uses a function in Shared.py

recalls['QUARTER'] = recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q') # convert in the form 2022Q2
recalls['QUARTER'] = recalls['QUARTER'].apply(format_quarter) # then apply the function to it to change to 'Month to Month year'

recalls.head() # have a look

# Format return by date for 2022Q4 - this doesn't have to be repeated after publishing for 2023Q4
#recalls['RETURN_BY'].unique()
#recalls.loc[recalls['QUARTER']=='Oct to Dec 2022','RETURN_BY'] = pd.Timestamp(2023,3,31)
#recalls['RETURN_BY'] = pd.to_datetime(recalls['RETURN_BY'])
#recalls.info()

# Change gender values - uses a mapping from Shared.py-----------------------------------------------------------
recalls['GENDER'].unique()
recalls['GENDER'] = recalls['GENDER'].replace(gender_mapping) # change 'F' to 'Female', 'M' to 'Male'

# Create a SENTENCE column (under 12, over 12, IPP, life)--------------------------------------------------------
sentence(recalls)
recalls['SENTENCE'].unique()

# Create a HDC indentification ------------------------------------------------------------------

recalls['HDC'] = 'Non-HDC'
recalls.loc[recalls['RECALL_TYPE_DESCRIPTION'].str.contains('HDC', case=False),'HDC'] = 'HDC'

# recalls.pivot_table(index=['RECALL_TYPE_DESCRIPTION','HDC'],aggfunc='size').reset_index(name='count').sort_values('HDC')

# create a list of the unique recall['QUARTER'] values ---------------

quarters = list(recalls['QUARTER'].unique()) # values like 'Month to Month Year'
quarters

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

table_2_summary = table_2_func(recalls, sex_values, sentence_values, hdc_values)

len(table_2_summary) # 225
table_2_summary.head(20) # each row came from a dictionary in a list

# Order the values of the columns of the summary table
table_2_summary['Sex'] = table_2_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_2_summary['Sentence type'] = table_2_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_2_summary['Recall category'] = table_2_summary['Recall category'].astype(CategoricalDtype(categories=hdc_values, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_2_df = table_2_summary.pivot_table(
    index=['Sex', 'Sentence type', 'Recall category'],
    columns='quarter',
    values='values'
).reset_index()

len(table_2_df) # 45

# Order the columns for publication

table_2_df = table_2_df[['Sex', 'Sentence type', 'Recall category'] + quarters]

table_2_df.head(20)

# don't use: percentage change ---------------------------------------------------------------- 
#percent_change_words = f'Percentage change between {quarters[0]} and {quarters[-1]}'
#table_2_df[percent_change_words] = (table_2_df[quarters[-1]] - table_2_df[quarters[0]])/ table_2_df[quarters[0]]
#table_2_df[percent_change_words] = np.round(table_2_df[percent_change_words],4)

# don't use: Format the values to have thousand separators ------------------------
#for quarter in quarters:
    #table_2_df[quarter] = table_2_df[quarter].apply(lambda x: f"{int(x):,}" if not pd.isna(x) else x)

# Write pivot table to excel document
output_work_book = f'Tables_{year}Q{qtr}.xlsx'

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='replace') as writer:
    table_2_df.to_excel(writer,startrow = 4, sheet_name='Table 2',index=False)

# Load the workbook to modify Table 2

workbook = load_workbook(output_work_book)
sheet = workbook['Table 2']

# Header text
header_text_t2 = [
    "Table 2: Time series: number of recalls from licence, by sex, sentence type, and recall category, England and Wales [note 1]",
    "This worksheet contains one table.",
    "Link to Contents tab",
    "Source: Public Protection Unit Database (PPUD)"
]

# Write the text in the first 4 rows in column A
for i, text in enumerate(header_text_t2, start = 1):
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

# don't use: Format the last column as percentages and handle missing values
#for row in range(5, sheet.max_row + 1):
#    cell = sheet.cell(row=row, column=9)
#    if cell.value is None:
#        cell.value = '[z]'
#        cell.font = Font(name='Arial', size=12)
#    else:
#        cell.number_format = '0%'
        
# Set consistent column widths

set_fixed_column_widths(sheet, start_row=5, columns=range(1, 3), gap_width=5)
set_fixed_column_widths(sheet, start_row=5, columns=range(3, 4), gap_width=7)
set_fixed_column_widths(sheet, start_row=5, columns=range(4, 9), gap_width=5)
#sheet.column_dimensions['I'].width = 25

# Bold headers (row 5) set the header row

for cell in sheet[5]:
    cell.font = header_font
    
sheet.row_dimensions[5].height = 46.8

# Loop through column 3 to find 'All recalls' and set row height to distinquish combinations

for row in range(5, sheet.max_row + 1):
    if sheet.cell(row=row, column=3).value == 'All recalls':
        sheet.row_dimensions[row].height = 24.9
        
# Save the modified workbook

workbook.save(output_work_book)

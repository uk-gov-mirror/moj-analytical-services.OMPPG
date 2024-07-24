""" 
GOAL: PRODUCE TABLE 10 - CONTINUATION FROM TABLE 9 CODE.
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

reas1 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2022q4.parquet')
reas2 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2023q1.parquet')
reas3 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2023q2.parquet')
reas4 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2023q3.parquet')
reas5 = pd.read_parquet(f's3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2023q4.parquet')

# uppercase the headers
for df in [reas1,reas2,reas3,reas4,reas5]:
    df.columns = df.columns.str.upper()

# Concatenate all DataFrames into one------------------------------------------------------------------

reasons = pd.concat([reas1,reas2,reas3,reas4,reas5], ignore_index=True)
len(reasons) # 66131
reasons.head()
reasons.info()

del reas1,reas2,reas3,reas4,reas5

# Some corrections
reasons['SENTENCETYPE'].value_counts()

reasons.loc[reasons['CUSTODYTYPE'] == 'IPP','SENTENCETYPE'] = 'IPP'
reasons.loc[reasons['CUSTODYTYPE'] == 'Life','SENTENCETYPE'] = 'Life sentence'
reasons.loc[reasons['SENTENCETYPE'] == 'Other','SENTENCETYPE'] = 'Determinate 12 months or more'
reasons.loc[reasons['SENTENCETYPE'] == 'Under 12 months','SENTENCETYPE'] = 'Determinate less than 12 months'

reasons['SENTENCE'] = reasons['SENTENCETYPE']

# Add a recall 'QUARTER' column in the form 'Month to Month year'-------------------------------------------
# this uses a function in Shared.py

reasons['QUARTER'] = reasons['LICENCE_REVOKE_DATE'].dt.to_period('Q') # convert in the form 2022Q2
reasons['QUARTER'] = reasons['QUARTER'].apply(format_quarter) # then apply the function to it to change to 'Month to Month year'

reasons.head() # have a look

# Change gender values - uses a mapping from Shared.py-----------------------------------------------------------
reasons['GENDER'].unique()
reasons['GENDER'] = reasons['GENDER'].replace(gender_mapping) # change 'F' to 'Female', 'M' to 'Male'

# reasons[reasons['REASON_DESC'] == 'Other']['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False)

# create a list of the unique recall['QUARTER'] values ---------------

quarters = list(reasons['QUARTER'].unique()) # values like 'Month to Month Year'
quarters

def table_10_func(df, df2, sex_values, sentence_values, reason_desc_vals): # parameters are in Shared.py
    
    summary_list = []
    
    for sex in sex_values:
        if sex == 'Male and female':
            for sentence in sentence_values:
                if sentence == 'All sentence types':
                    temp_df = df
                else:
                    temp_df = df[df['SENTENCE'] == sentence]

                # First line for each combination of gender and sentence -> All recall types

                for quarter in quarters:
                    temp_date_df = temp_df[temp_df['QUARTER'] == quarter]              

                    for reason in reason_desc_vals:  # Skip 'All recalls' in this loop
                        reason_value = temp_date_df[temp_date_df['REASON_DESC'] == reason]['LICENCE_REVOKE_DATE'].count()
                        summary_list.append({
                            'Sex': sex,
                            'Sentence type': sentence,
                            'Recall reason': reason,
                            'quarter': quarter,
                            'values': reason_value
                        })
    
        else:
            temp_df = df[df['GENDER'] == sex]
            for quarter in quarters:
                temp_date_df = temp_df[temp_df['QUARTER'] == quarter]              

                for reason in reason_desc_vals:  # Skip 'All recalls' in this loop
                    reason_value = temp_date_df[temp_date_df['REASON_DESC'] == reason]['LICENCE_REVOKE_DATE'].count()
                    summary_list.append({
                            'Sex': sex,
                            'Sentence type': 'All sentence types',
                            'Recall reason': reason,
                            'quarter': quarter,
                            'values': reason_value
                        })
    return pd.DataFrame(summary_list)

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

table_10_summary = table_10_func(reasons,recalls, sex_values, sentence_values, reason_desc_vals)

len(table_10_summary) # 420
table_10_summary.head(20) # each row came from a dictionary in a list

# Order the values of the columns of the summary table
table_10_summary['Sex'] = table_10_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_10_summary['Sentence type'] = table_10_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_10_summary['Recall reason'] = table_10_summary['Recall reason'].astype(CategoricalDtype(categories=reason_desc_vals, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_10_df = table_10_summary.pivot_table(
    index=['Sex', 'Sentence type', 'Recall reason'],
    columns='quarter',
    values='values'
).reset_index()

len(table_10_df) # 84

# Order the columns for publication

table_10_df = table_10_df[['Sex', 'Sentence type', 'Recall reason'] + quarters]

table_10_df

# don't use: percentage change ---------------------------------------------------------------- 
#percent_change_words = f'Percentage change between {quarters[0]} and {quarters[-1]}'
#table_2_df[percent_change_words] = (table_2_df[quarters[-1]] - table_2_df[quarters[0]])/ table_2_df[quarters[0]]
#table_2_df[percent_change_words] = np.round(table_2_df[percent_change_words],4)

# don't use: Format the values to have thousand separators ------------------------
#for quarter in quarters:
    #table_2_df[quarter] = table_2_df[quarter].apply(lambda x: f"{int(x):,}" if not pd.isna(x) else x)

# Write pivot table to excel document

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='replace') as writer:
    table_10_df.to_excel(writer,startrow = 4, sheet_name='Table 10',index=False)

# Load the workbook to modify Table 2

workbook = load_workbook(output_work_book)
sheet = workbook['Table 10']

# Header text
header_text_t10 = [
    "Table 10: Time series: number of recalls, by sex, sentence and reason for recall, England and Wales [note 4]",
    "This worksheet contains one table.",
    "Link to Contents tab",
    "Source: Public Protection Unit Database (PPUD)"
]

# Write the text in the first 4 rows in column A
for i, text in enumerate(header_text_t10, start = 1):
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
    if sheet.cell(row=row, column=3).value == 'Facing further charge':
        sheet.row_dimensions[row].height = 24.9
        
# Save the modified workbook

workbook.save(output_work_book)

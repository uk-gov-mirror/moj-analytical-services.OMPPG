""" 
GOAL: PRODUCE TABLE 11 - CONTINUATION FROM TABLE 10 CODE.
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

real1 = pd.read_sas('s3://alpha-omppg/isp_releases/final-data/isp_releases_2022q4.sas7bdat',encoding='latin1')
real2 = pd.read_sas('s3://alpha-omppg/isp_releases/final-data/isp_releases_2023q1.sas7bdat',encoding='latin1')
real3 = pd.read_sas('s3://alpha-omppg/isp_releases/final-data/isp_releases_2023q2.sas7bdat',encoding='latin1')
real4 = pd.read_sas('s3://alpha-omppg/isp_releases/final-data/isp_releases_2023q3.sas7bdat',encoding='latin1')
real5 = pd.read_sas('s3://alpha-omppg/isp_releases/final-data/isp_releases_2023q4.sas7bdat',encoding='latin1')

# uppercase the headers
for df in [real1,real2,real3,real4,real5]:
    df.columns = df.columns.str.upper()

max(real1['RELEASE_DATE'])

for df in [real1,real2,real3,real4,real5]:
    df['QUARTER'] = max(df['RELEASE_DATE'])
    df['QUARTER'] = df['QUARTER'].dt.to_period("Q")
    df['QUARTER_CHECK'] = df['RELEASE_DATE'].dt.to_period("Q")

releases = pd.concat([real1,real2,real3,real4,real5], ignore_index=True)

del real1,real2,real3,real4,real5

releases['RELEASE_TYPE'].unique()
releases = releases[releases['RELEASE_TYPE'] == 'Recall Re-release']

releases = releases[releases['QUARTER'] == releases['QUARTER_CHECK']]
len(releases) #811

releases['MONTHS_RECALLED'] = releases.apply(lambda x: TimeDiffs.month_diff(x['LAST_RTC_DATE'],x['RELEASE_DATE']),axis=1)

# Concatenate all DataFrames into one------------------------------------------------------------------

releases['QUARTER'] = releases['QUARTER'].apply(format_quarter) # then apply the function to it to change to 'Month to Month year

len(releases) # 204

releases.loc[releases['CUSTODY_TYPE_DESCRIPTION'] == 'DPP','CUSTODY_TYPE_DESCRIPTION'] = 'IPP'
releases.loc[releases['CUSTODY_TYPE_DESCRIPTION'] != 'IPP','CUSTODY_TYPE_DESCRIPTION'] = 'Life sentence'

# create a list of the unique recall['QUARTER'] values ---------------

quarters = list(releases['QUARTER'].unique()) # values like 'Month to Month Year'
quarters

table_11_summary =releases.groupby(['CUSTODY_TYPE_DESCRIPTION',
                                    'QUARTER'],dropna=False)['MONTHS_RECALLED'].agg(['size','mean']).reset_index()

table_11_melted = pd.melt(table_11_summary, 
                          id_vars=['CUSTODY_TYPE_DESCRIPTION', 'QUARTER'], 
                          var_name='Statistic', value_name='Value')

table_11_melted['Value'] = table_11_melted['Value'].round()
table_11_melted['Value'] = table_11_melted['Value'].astype('int64')

table_11_melted['Statistic'] = table_11_melted['Statistic'].map({'size':'Number of releases','mean': 'Average time recalled (months)'})
table_11_melted = table_11_melted.rename(columns = {'CUSTODY_TYPE_DESCRIPTION':'Sentence type'})

# Order the values of the columns of the summary table
table_11_melted['Sentence type'] = table_11_melted['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_11_melted['Statistic'] = table_11_melted['Statistic'].astype(CategoricalDtype(categories=['Number of releases','Average time recalled (months)'], ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_11_df = table_11_melted.pivot_table(
    index=['Sentence type', 'Statistic'],
    columns='QUARTER',
    values='Value'
).reset_index()


# Order the columns for publication

table_11_df = table_11_df[['Sentence type', 'Statistic'] + quarters]

table_11_df

# Write pivot table to excel document

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='replace') as writer:
    table_11_df.to_excel(writer,startrow = 4, sheet_name='Table 11',index=False)

# Load the workbook to modify Table 2

workbook = load_workbook(output_work_book)
sheet = workbook['Table 11']

# Header text
header_text_t11 = [
    "Table 11: number of recall re-releases and mean time recalled (indeterminate-sentence offenders),England and Wales [note 4]",
    "This worksheet contains one table.",
    "Link to Contents tab",
    "Source: Public Protection Unit Database (PPUD)"
]

# Write the text in the first 4 rows in column A
for i, text in enumerate(header_text_t11, start = 1):
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
    if sheet.cell(row=row, column=2).value == 'Number of releases':
        sheet.row_dimensions[row].height = 24.9
        
# Save the modified workbook

workbook.save(output_work_book)

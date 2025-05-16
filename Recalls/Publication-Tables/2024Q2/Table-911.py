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

real3 = pd.read_sas('s3://alpha-omppg/isp_releases/final-data/isp_releases_2023q2.sas7bdat',encoding='latin1')
real4 = pd.read_sas('s3://alpha-omppg/isp_releases/final-data/isp_releases_2023q3.sas7bdat',encoding='latin1')
real5 = pd.read_sas('s3://alpha-omppg/isp_releases/final-data/isp_releases_2023q4.sas7bdat',encoding='latin1')
real1 = pd.read_parquet('s3://alpha-omppg/isp_releases/final-data/isp_releases_2024q1.parquet')
real2 = pd.read_parquet('s3://alpha-omppg/isp_releases/final-data/isp_releases_2024q2.parquet')

# uppercase the headers
for df in [real1,real2,real3,real4,real5]:
    df.columns = df.columns.str.upper()

max(real2['RELEASE_DATE'])

for df in [real1,real2,real3,real4,real5]:
    df['QUARTER'] = max(df['RELEASE_DATE'])
    df['QUARTER'] = df['QUARTER'].dt.to_period("Q")
    df['QUARTER_CHECK'] = df['RELEASE_DATE'].dt.to_period("Q")

releases = pd.concat([real3,real4,real5,real1,real2], ignore_index=True)

del real1,real2,real3,real4,real5

releases['RELEASE_TYPE'].unique()
releases = releases[releases['RELEASE_TYPE'] == 'Recall Re-release']

releases = releases[releases['QUARTER'] == releases['QUARTER_CHECK']]
len(releases) #1011,887,811

releases['MONTHS_RECALLED'] = releases.apply(lambda x: TimeDiffs.month_diff(x['LAST_RTC_DATE'],x['RELEASE_DATE']),axis=1)

releases['MONTHS_RECALLED'].unique()

# Concatenate all DataFrames into one------------------------------------------------------------------

releases['QUARTER'] = releases['QUARTER'].apply(format_quarter) # then apply the function to it to change to 'Month to Month year

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

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_11_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_11',index=False,header=False)
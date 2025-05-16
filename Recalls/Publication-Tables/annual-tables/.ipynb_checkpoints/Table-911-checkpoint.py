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
relYears = list(range(2017,2025))
relQuarters = [i for i in range(1,5)]

#---------------------------------- Import data

# some of the files are SAS and others are Parquet, so try to import each

def conCatReleaseDatasets(years,quarters):
    
    releases = pd.DataFrame() # start with an empty dataframe

    for year in years:
        
        for quarter in quarters:

            quart_rels = pd.DataFrame() # Reset appending file

            try: # Try to import SAS file first
                quart_rels = pd.read_sas(f"s3://alpha-omppg/isp_releases/final-data/isp_releases_{year}q{quarter}.sas7bdat", encoding='latin1')
                quart_rels.columns = quart_rels.columns.str.upper()
                quart_rels = quart_rels[(quart_rels['RELEASE_DATE'].dt.year == year) & (quart_rels['RELEASE_DATE'].dt.quarter == quarter)]
                quart_rels = quart_rels.drop(columns =['LATEST_RELEASE_DATE'])                                             
                #print(f"Loaded SAS file for {year}{quarter}. Empty {quart_rels.empty}?")

            except Exception as e:# If no SAS file, import parquet version

                print(f"Failed to load SAS file for {year}{quarter}, error: {e}")

                try:
                    quart_rels = pd.read_parquet(f"s3://alpha-omppg/isp_releases/final-data/isp_releases_{year}q{quarter}.parquet")
                    quart_rels.columns = quart_rels.columns.str.upper()
                    quart_rels = quart_rels[(quart_rels['RELEASE_DATE'].dt.year == year) & (quart_rels['RELEASE_DATE'].dt.quarter == quarter)]
                    quart_rels = quart_rels.drop(columns =['LATEST_RELEASE_DATE'])
                    #print(f"Loaded Parquet file for {year}{quarter}. Empty {quart_rels.empty}?")

                except Exception as e:
                    print(f"Failed to load parquet file for {year}{quarter}, error: {e}")

            if not quart_rels.empty:
                releases = pd.concat([releases,quart_rels],axis=0)
                print(f"Added file for {year}q{quarter}. Empty?: {quart_rels.empty}")
                
    return releases

releases_0 =  conCatReleaseDatasets(relYears,relQuarters)
releases = releases_0.copy()

# placeholder for summaries
releases['COMMON'] = 1

# Add a recall 'YEAR' column in the form 'Month to Month year'-------------------------------------------

releases['YEAR'] = releases['RELEASE_DATE'].dt.year

"""
releases.head()
releases.tail()

"""

releases['RELEASE_TYPE'].unique()
releases = releases[releases['RELEASE_TYPE'] == 'Recall Re-release']

len(releases) # 

releases['MONTHS_RECALLED'] = releases.apply(lambda x: TimeDiffs.month_diff(x['LAST_RTC_DATE'],x['RELEASE_DATE']),axis=1)

releases['MONTHS_RECALLED'].unique()

# Concatenate all DataFrames into one------------------------------------------------------------------

releases.loc[releases['CUSTODY_TYPE_DESCRIPTION'] == 'DPP','CUSTODY_TYPE_DESCRIPTION'] = 'IPP'
releases.loc[releases['CUSTODY_TYPE_DESCRIPTION'] != 'IPP','CUSTODY_TYPE_DESCRIPTION'] = 'Life sentence'

# create a list of the unique recall['QUARTER'] values ---------------

years

table_11_summary =releases.groupby(['CUSTODY_TYPE_DESCRIPTION',
                                    'YEAR'],dropna=False)['MONTHS_RECALLED'].agg(['size','mean']).reset_index()

table_11_melted = pd.melt(table_11_summary, 
                          id_vars=['CUSTODY_TYPE_DESCRIPTION', 'YEAR'], 
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
    columns='YEAR',
    values='Value',observed=False
).reset_index()


# Order the columns for publication

table_11_df = table_11_df[['Sentence type', 'Statistic'] + relYears]

table_11_df

# Write pivot table to excel document

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_11_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_11',index=False,header=False)
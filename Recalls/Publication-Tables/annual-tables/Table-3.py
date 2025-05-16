""" 
GOAL: PRODUCE TABLE 3 - CONTINUATION FROM TABLE 2 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Calculate summaries for the combined DataFrame
recalls['NPS_CRC_NAME'].unique()
recalls.pivot_table(index=['SUP_BODY','NPS_CRC_NAME'],columns='YEAR',aggfunc='size')
recalls[recalls['YEAR']==2018]['NPS_CRC_NAME'].unique()


supervision_body_format = {'a.NSD':'National security division','b. NPS':'National probation',
                           'b. PS':'National probation','c. CRC':'Community rehabilitation companies',
                          'd. Unknown':'Unknown'}

mps_crc_format = {'LondonLondon - NPS':'London',
                  'WalesWales - NPS':'Wales',
                  'London - NPS':'London',
                  'Wales - NPS':'Wales',
                   np.nan:'Unassigned'}

recalls['SUP_BODY'] = recalls['SUP_BODY'].replace(supervision_body_format)
recalls['NPS_CRC_NAME'] = recalls['NPS_CRC_NAME'].replace(mps_crc_format)

recalls.loc[recalls['NPS_CRC_NAME'] == 'National Security Division', 'SUP_BODY'] = 'National security division'

recalls.loc[(recalls['NPS_CRC_NAME'] == 'South West') & (recalls['LICENCE_REVOKE_DATE'] <= pd.Timestamp(2021,9,30)), 'NPS_CRC_NAME'] = 'South West & South Central'

recalls[recalls['YEAR']==2018]['SUP_BODY'].value_counts(dropna=False)
recalls[recalls['YEAR']==2018]['NPS_CRC_NAME'].value_counts(dropna=False)

recalls.pivot_table(index=['SUP_BODY','NPS_CRC_NAME'],
                                           columns='YEAR',aggfunc='size',
                                           observed=False,fill_value=0)

table_3_summary = table_3_func(recalls, supervising_body,probation_region)
table_3_summary = table_3_summary.loc[table_3_summary['values'] != 0]
len(table_3_summary) # 290

table_3_summary.head(50) # each row came from a dictionary in a list

# categorise to order values for publication
recalls['NPS_CRC_NAME'].value_counts(dropna=False).sort_index().index

supBodyOrder = ['All supervising bodies', 'National probation', 'National security division', 'Community rehabilitation companies','Unknown']

npsOrder = ['All regions','East Midlands','East of England','Greater Manchester','Kent Surrey Sussex',
 'London','North East','North West','South Central','South West','West Midlands',
 'Yorkshire and The Humber', 'Wales','Midlands','South East & Eastern','South West & South Central']

table_3_summary['Supervising body'] = table_3_summary['Supervising body'].astype(CategoricalDtype(categories=supBodyOrder, ordered=True))
table_3_summary.loc[table_3_summary['Supervising body'] =='National probation','Region'] = table_3_summary.loc[table_3_summary['Supervising body'] =='National probation']['Region'].astype(CategoricalDtype(categories=npsOrder, ordered=True))

# Pivot the final summary DataFrame to get the desired format

table_3_df = table_3_summary.pivot_table(
    index=['Supervising body', 'Region'],
    columns='year',
    values='values',
    fill_value='[z]'
).reset_index()

len(table_3_df) # 42

# Order the columns for publication
table_3_df = table_3_df[['Supervising body', 'Region'] + years]

table_3_df


# send to excel workbook

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_3_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_3',index=False,header = False)
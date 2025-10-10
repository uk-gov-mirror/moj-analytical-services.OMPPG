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
table_3_summary = table_3_func(recalls, probation_region, hdc_values)

len(table_3_summary) # 225
table_3_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_3_summary['Probation region'] = table_3_summary['Probation region'].astype(CategoricalDtype(categories=probation_region, ordered=True))
table_3_summary['Recall category'] = table_3_summary['Recall category'].astype(CategoricalDtype(categories=hdc_values, ordered=True))

# Pivot the final summary DataFrame to get the desired format

table_3_df = table_3_summary.pivot_table(
    index=['Probation region', 'Recall category'],
    columns='quarter',
    values='values',observed=False
).reset_index()

len(table_3_df) # 45

# Order the columns for publication
table_3_df = table_3_df[['Probation region', 'Recall category'] + quarters]

table_3_df

# send to excel workbook

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_3_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_3',index=False,header = False)
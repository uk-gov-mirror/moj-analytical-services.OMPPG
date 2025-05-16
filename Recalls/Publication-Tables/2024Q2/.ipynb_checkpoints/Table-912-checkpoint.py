""" 
GOAL: PRODUCE TABLE 12 - CONTINUATION FROM TABLE 11 CODE.
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


# reasons[reasons['REASON_DESC'] == 'Other']['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False)
ethnicity(recalls)
recalls['ETHNICITY'].value_counts(dropna=False)
# create a list of the unique recall['QUARTER'] values ---------------

quarters

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

table_12_summary = table_12_func(recalls, sex_values, sentence_values, ethnicity_vals)

len(table_12_summary) # 245
# table_12_summary.head(20) # each row came from a dictionary in a list

# Order the values of the columns of the summary table
table_12_summary['Sex'] = table_12_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_12_summary['Sentence type'] = table_12_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))
table_12_summary['Ethnicity'] = table_12_summary['Ethnicity'].astype(CategoricalDtype(categories=['All ethnicities'] + ethnicity_vals, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_12_df = table_12_summary.pivot_table(
    index=['Sex', 'Sentence type', 'Ethnicity'],
    columns='quarter',
    values='values'
).reset_index()

len(table_12_df) # 49

# Order the columns for publication

table_12_df = table_12_df[['Sex', 'Sentence type', 'Ethnicity'] + quarters]

table_12_df

# Write pivot table to excel document

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_12_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_12',index=False,header=False)
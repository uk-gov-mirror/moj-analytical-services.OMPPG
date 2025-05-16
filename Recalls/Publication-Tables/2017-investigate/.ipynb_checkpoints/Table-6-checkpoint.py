""" 
GOAL: PRODUCE TABLE 6 - CONTINUATION FROM TABLE 5 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


# ---------------Table 5.6: Number of recalls from licence by sentence type, and process time

# correct recall process and recall target

recalls['RECALL_PROCESS'].value_counts(dropna=False)
recalls['RECALL_TARGET'].value_counts(dropna=False)

recalls['RECALL_TARGET'] = recalls['RECALL_TARGET'].str.strip()
recalls['RECALL_TARGET'].value_counts(dropna=False)

recalls.loc[recalls['CUSTODYTYPE'].isin(['IPP','Life']),'RECALL_PROCESS'] = 'Indeterminate Emergency'
recalls.loc[recalls['RECALL_PROCESS'] == 'Emergency','RECALL_PROCESS'] = 'Determinate Emergency'
recalls.loc[recalls['RECALL_PROCESS'] == 'Standard','RECALL_PROCESS'] = 'Determinate Standard'

recalls.loc[recalls['RECALL_TARGET'] == 'd. Resolved','RECALL_TARGET'] = 'b. Returned outside target'

recalls['RECALL_TARGET_2'] = recalls.apply(lambda x: x['RECALL_TARGET'][2:].strip(), axis=1)


# Create 'recall target date' headings

recalls['RECALLED_IN_STATUS_ON'] = recalls.apply(lambda x: 'Recalled in ' + str(x['QUARTER']) + ' returned by ' + str(x['RETURN_BY_STR']), axis=1)

recalls['RECALLED_IN_STATUS_ON'].unique()

# Define unique values Table 5
rec_in_status_on = list(recalls['RECALLED_IN_STATUS_ON'].unique())
rec_in_status_on

# Calculate summaries for the combined DataFrame
table_6_summary = table_6_func(recalls, sex_values, sentence_values)

len(table_6_summary) # 80
# table_6_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_6_summary['Recall process'] = table_6_summary['Recall process'].astype(CategoricalDtype(categories=rec_process, ordered=True))
table_6_summary['Return status'] = table_6_summary['Return status'].astype(CategoricalDtype(categories=return_statuses, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_6_df = table_6_summary.pivot_table(
    index=['Recall process', 'Return status'],
    columns='text',
    values='values'
).reset_index()

len(table_6_df) # 16

# Order the columns for publication
table_6_df = table_6_df[['Recall process', 'Return status'] + rec_in_status_on]

table_6_df

# Output
with pd.ExcelWriter(output_work_book,engine='openpyxl', mode ='a',if_sheet_exists='overlay') as writer:
    table_6_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_6',index=False,header=False)


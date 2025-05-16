""" 
GOAL: PRODUCE TABLE 4 - CONTINUATION FROM TABLE 3 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


# ---------------Table 5.13: Fixed term, standard recall

# Create fixed-term/ standard term column

ftrStd(recalls)

# recalls['RECALL_LENGTH_2'].value_counts(dropna=False)
#recalls.pivot_table(index =['RECALL_LENGTH_2','RECALL_TYPE_DESCRIPTION'],columns='QUARTER',aggfunc='size',observed=False,fill_value=0)

table_13_summary = table_13_func(recalls, sex_values, ftr_std_values)

len(table_13_summary) # 75
# table_13_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_13_summary['Sex'] = table_13_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_13_summary['Recall length'] = table_13_summary['Recall length'].astype(CategoricalDtype(categories=ftr_std_values, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_13_df = table_13_summary.pivot_table(
    index=['Sex', 'Recall length'],
    columns='quarter',
    values='values',observed=False
).reset_index()

len(table_13_df) # 15

# Order the columns for publication
table_13_df = table_13_df[['Sex', 'Recall length'] + quarters]

table_13_df

# Output to Excel
with pd.ExcelWriter(output_work_book,engine='openpyxl', mode ='a', if_sheet_exists='overlay') as writer:
    table_13_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_13',index=False,header = False)


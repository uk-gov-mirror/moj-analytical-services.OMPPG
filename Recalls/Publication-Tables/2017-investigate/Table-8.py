""" 
GOAL: PRODUCE TABLE 8 - CONTINUATION FROM TABLE 7 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Get final UAL data for the last 5 quarters ----------------------------------------------------


# ---------------Table 5.8: Total number of offenders not returned to custody after licence recall, by supervising body, and length of time since recall

ual['HOWLONG'].value_counts()
ual['HOWLONG'] = ual['HOWLONG'].map(howlong_mapping).fillna('Unknown')
ual['HOWLONG'].value_counts()

# Calculate summaries for the combined DataFrame
table_8_summary = table_8_func(ual, supervising_body,howlong_vals)

len(table_8_summary) # 120
# table_8_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_8_summary['Supervising body'] = table_8_summary['Supervising body'].astype(CategoricalDtype(categories=supervising_body, ordered=True))
table_8_summary['Time since recall'] = table_8_summary['Time since recall'].astype(CategoricalDtype(categories=howlong_vals, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_8_df = table_8_summary.pivot_table(
    index=['Supervising body','Time since recall'],
    columns='text',
    values='values',observed=False
).reset_index()

len(table_8_df) # 24

# Order the columns for publication
table_8_df = table_8_df[['Supervising body','Time since recall'] + rec_1984_not_returned_by]

table_8_df

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_8_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_8',index=False,header=False)
""" 
GOAL: PRODUCE TABLE 5 - CONTINUATION FROM TABLE 4 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


# ---------------Table 5.4: Number of returns to custody after licence recall, by sex, supervising body, and sentence length

table_5_condition = ( (recalls['UAL_FLAG'] == True) |
                     (
                        (recalls['LICENCE_REVOKE_DATE'].dt.year < 2015) & 
                        (
                            (recalls['RTC_DATE'] > recalls['RETURN_BY']) | 
                            (recalls['RTC_DATE'].isna())
                        )
                     )
                   )

# Create a 'recalled in and not returned' by headings

recalls['RECALLED_IN_NOT_RETURNED_BY'] = recalls.apply(lambda x: 'Recalled in ' + str(x['QUARTER']) + ' not returned by ' + str(x['RETURN_BY_STR']), axis=1)

recalls['RECALLED_IN_NOT_RETURNED_BY'].unique()

# Define unique values Table 5
rec_not_return_by = list(recalls['RECALLED_IN_NOT_RETURNED_BY'].unique())

# Calculate summaries for the combined DataFrame
table_5_summary = table_5_func(recalls, sex_values, sentence_values,table_5_condition)

len(table_5_summary) # 75
table_5_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_5_summary['Sex'] = table_5_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_5_summary['Sentence type'] = table_5_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_5_df = table_5_summary.pivot_table(
    index=['Sex', 'Sentence type'],
    columns='text',
    values='values'
).reset_index()

len(table_5_df) # 15

# Order the columns for publication
table_5_df = table_5_df[['Sex', 'Sentence type'] + rec_not_return_by]

table_5_df

# Output
with pd.ExcelWriter(output_work_book,engine='openpyxl', mode ='a',if_sheet_exists='overlay') as writer:
    table_5_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5',index=False,header = False)


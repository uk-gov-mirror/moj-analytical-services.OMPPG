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


# ---------------Table 5.4: Number of returns to custody after licence recall, by sex, supervising body, and sentence length

# format UAL_FLAG

recalls['UAL_FLAG'].unique()
recalls.loc[recalls['UAL_FLAG']=='FALSE','UAL_FLAG'] = False
recalls.loc[recalls['UAL_FLAG']=='TRUE','UAL_FLAG'] = True
recalls['UAL_FLAG'].unique()
recalls.info() # leave it as object type

# Create 'recalled in and returned by' headings

recalls['RETURN_BY'].unique()
recalls['RETURN_BY_STR'] = recalls['RETURN_BY'].dt.strftime('%d %b %Y') # convert return by dates to string 'dd mmm yyyy'
recalls['RETURN_BY_STR'] = recalls['RETURN_BY_STR'].replace({'Jun':'June','Jul':'July','Sep':'Sept'},regex=True)
recalls['RETURN_BY_STR'].unique()

recalls['RECALLED_IN_RETURNED_BY'] = recalls.apply(lambda x: 'Recalled in ' + str(x['QUARTER']) + ' returned by ' + str(x['RETURN_BY_STR']), axis=1)

recalls['RECALLED_IN_RETURNED_BY'].unique()

# Define unique values Table 5
rec_return_by = list(recalls['RECALLED_IN_RETURNED_BY'].unique())

# Calculate summaries for the combined DataFrame

table_4_condition = ( (recalls['UAL_FLAG'] == False) |
                    (
                        (recalls['LICENCE_REVOKE_DATE'].dt.year < 2015) & 
                        (recalls['RTC_DATE'] <= recalls['RETURN_BY']) & 
                        (recalls['RTC_DATE'].notna())
                     )
                   )

table_4_summary = table_4_func(recalls, sex_values, sentence_values,table_4_condition)

len(table_4_summary) # 75
# table_4_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_4_summary['Sex'] = table_4_summary['Sex'].astype(CategoricalDtype(categories=sex_values, ordered=True))
table_4_summary['Sentence type'] = table_4_summary['Sentence type'].astype(CategoricalDtype(categories=sentence_values, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_4_df = table_4_summary.pivot_table(
    index=['Sex', 'Sentence type'],
    columns='text',
    values='values'
).reset_index()

len(table_4_df) # 15

# Order the columns for publication
table_4_df = table_4_df[['Sex', 'Sentence type'] + rec_return_by]

table_4_df

# Output to Excel
with pd.ExcelWriter(output_work_book,engine='openpyxl', mode ='a', if_sheet_exists='overlay') as writer:
    table_4_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_4',index=False,header = False)


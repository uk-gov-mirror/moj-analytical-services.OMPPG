""" 
GOAL: PRODUCE TABLE 4 - CONTINUATION FROM TABLE 3 CODE
By Eric Nyame, 17/04/2024
"""
# ---------------Table 5.13: Fixed term, standard recall

# Create fixed-term/ standard term column

import duckdb


recalls['RECALL_TYPE_DESCRIPTION'].unique()
recalls['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)
# ftrStd(recalls)

   # Fixed term vs standard recall values

RecallRef = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls', sheet_name='RecallType')

RecallRef.columns = RecallRef.columns.str.upper()
RecallRef = RecallRef.replace("–","-",regex=True) # replace long dashes with normal dashes

recalls.shape # 51300

query = """ SELECT a.*,
                b.FTR_STD AS RECALL_LENGTH_2

            FROM recalls as a 
            LEFT JOIN RecallRef as b 
            ON a.RECALL_TYPE_DESCRIPTION = b.RECALL_TYPE_DESCRIPTION
             """
  
recalls_matched = duckdb.sql(query).df()
recalls_matched.shape # 51300

# recalls_matched['RECALL_LENGTH_2'].value_counts(dropna=False)
#recalls_matched.pivot_table(index =['RECALL_LENGTH_2','RECALL_TYPE_DESCRIPTION'],columns='QUARTER',aggfunc='size',observed=False,fill_value=0)

# See if RECALL_LENGTH_2 match FTR_STD
recalls_matched.pivot_table(index =['RECALL_LENGTH_2','FTR_STD'],columns='QUARTER',aggfunc='size',observed=False,fill_value=0)
recalls_matched.head()

recalls = recalls_matched.copy()

table_13_summary = table_13_func(recalls, sex_values, ftr_std_values)

len(table_13_summary) # 90
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

len(table_13_df) # 18

table_13_df
# Order the columns for publication
table_13_df = table_13_df[['Sex', 'Recall length'] + quarters]

table_13_df

# Output to Excel
with pd.ExcelWriter(output_work_book,engine='openpyxl', mode ='a', if_sheet_exists='overlay') as writer:
    table_13_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_13',index=False,header = False)

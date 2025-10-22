""" 
GOAL: PRODUCE TABLE 9 - CONTINUATION FROM TABLE 8 CODE
By Eric Nyame, 17/04/2024
"""
# ---------------Table 5.9: Total number of offenders not returned to custody after licence recall, by offence

# Correct offence groups
ual['OFFENCEGRP_NEW'].unique()

ual.loc[ual['OFFENCEGRP_NEW']=='Violence Against The Person','OFFENCEGRP_NEW'] = 'Violence against the person'
ual.loc[ual['OFFENCEGRP_NEW']=='Sexual Offences','OFFENCEGRP_NEW'] = 'Sexual offences'
ual.loc[ual['OFFENCEGRP_NEW']=='Drug Offences','OFFENCEGRP_NEW'] = 'Drug offences'
ual.loc[ual['OFFENCEGRP_NEW']=='Fraud offences','OFFENCEGRP_NEW'] = 'Fraud'
ual.loc[ual['OFFENCEGRP_NEW']=='Summary Motoring','OFFENCEGRP_NEW'] = 'Summary motoring'
ual.loc[ual['OFFENCEGRP_NEW']=='Public Order Offences','OFFENCEGRP_NEW'] = 'Public order offences'
ual.loc[ual['OFFENCEGRP_NEW']=='Criminal Damage and Arson','OFFENCEGRP_NEW'] = 'Criminal damage and arson'
ual.loc[ual['OFFENCEGRP_NEW']=='Miscellaneous Crimes Against Society','OFFENCEGRP_NEW'] = 'Miscellaneous crimes against society'
ual.loc[ual['OFFENCEGRP_NEW'].isna(),'OFFENCEGRP_NEW'] = 'Offence not recorded'

# Correct offence subgroups
ual['OFFENCESUBGROUP_NEW'].unique()

ual['OFFENCESUBGROUP_NEW'] = ual['OFFENCESUBGROUP_NEW'].str.strip()

ual.loc[ual['OFFENCESUBGROUP_NEW'].isna(),'OFFENCESUBGROUP_NEW'] = 'Missing'
ual.loc[ual['OFFENCESUBGROUP_NEW']=='Stalking and Harassment','OFFENCESUBGROUP_NEW'] = 'Stalking and harassment'
ual.loc[ual['OFFENCESUBGROUP_NEW']=='Gross indecency with children','OFFENCESUBGROUP_NEW'] = 'Other sexual offences'

# Calculate summaries for the combined DataFrame
table_9_summary = table_9_func(ual, offence_groups,vatp_subs,sexual_offence_subs)

len(table_9_summary) # 100

# table_9_summary.head(20) # each row came from a dictionary in a list

# categorise to order values for publication
table_9_summary['Offence group'] = table_9_summary['Offence group'].astype(CategoricalDtype(categories=offence_groups, ordered=True))
table_9_summary['Offence subgroup'] = table_9_summary['Offence subgroup'].astype(CategoricalDtype(categories=['All offences'] + vatp_subs + sexual_offence_subs, ordered=True))

# Pivot the final summary DataFrame to get the desired format
table_9_df = table_9_summary.pivot_table(
    index=['Offence group','Offence subgroup'],
    columns='text',
    values='values',observed=False
).reset_index()

len(table_9_df) # 20

# Order the columns for publication
table_9_df = table_9_df[['Offence group','Offence subgroup'] + rec_1984_not_returned_by]

table_9_df

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:
    table_9_df.T.reset_index().T.to_excel(writer,startrow = 4, sheet_name='Table_5_Q_9',index=False,header=False)
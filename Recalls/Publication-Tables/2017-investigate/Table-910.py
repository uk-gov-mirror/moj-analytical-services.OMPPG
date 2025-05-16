""" 
GOAL: PRODUCE TABLE 10 - CONTINUATION FROM TABLE 9 CODE.
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Get last final recall data for the last 5 quarters----------------------------------------------------------------------

reasons = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2017q1.sas7bdat',encoding='latin1')
reasons.columns = reasons.columns.str.upper()

reasons.head()

# Some corrections
reasons['SENTENCETYPE'].value_counts()

reasons.loc[reasons['CUSTODYTYPE'] == 'IPP','SENTENCETYPE'] = 'IPP'
reasons.loc[reasons['CUSTODYTYPE'] == 'Life','SENTENCETYPE'] = 'Life sentence'
reasons.loc[reasons['SENTENCETYPE'] == 'Other','SENTENCETYPE'] = 'Determinate 12 months or more'
reasons.loc[reasons['SENTENCETYPE'] == 'Under 12 months','SENTENCETYPE'] = 'Determinate less than 12 months'

reasons['SENTENCE'] = reasons['SENTENCETYPE']

# Add a recall 'QUARTER' column in the form 'Month to Month year'-------------------------------------------
# this uses a function in Shared.py

reasons['QUARTER'] = reasons['LICENCE_REVOKE_DATE'].dt.to_period('Q') # convert in the form 2022Q2
reasons['QUARTER'] = reasons['QUARTER'].apply(format_quarter) # then apply the function to it to change to 'Month to Month year'
reasons['QUARTER'].unique()
reasons.head() # have a look

# Change gender values - uses a mapping from Shared.py-----------------------------------------------------------
reasons['GENDER'].unique()
reasons['GENDER'] = reasons['GENDER'].replace(gender_mapping) # change 'F' to 'Female', 'M' to 'Male'

# reasons[reasons['REASON_DESC'] == 'Other']['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False)

# create a list of the unique recall['QUARTER'] values ---------------

quarters = list(reasons['QUARTER'].unique()) # values like 'Month to Month Year'
quarters

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

reasons.pivot_table(index=['GENDER','REASON_DESC'],columns='QUARTER',aggfunc='size').reset_index()[['GENDER','REASON_DESC'] + quarters]

# Hunt
hunt_mask = (
            (recalls['LICENCE_REVOKE_DATE'].dt.quarter == 1) & 
            (recalls['GENDER'] == 'Male') & 
            (recalls['SENTENCE'] == 'Determinate less than 12 months') &
            (recalls['NPS_CRC_NAME'] == 'Midlands') &
            (recalls['RECALL_REASON_DESCRIPTIONS'].str.contains('keep in touch',case=False)) &
            (recalls['UAL_FLAG'].isna())
            )
sum(hunt_mask)
recalls.loc[hunt_mask]

"""
NOMS_ID = A5886AT
LICENCE_REVOKE_DATE = 2017-02-17
"""
NaN	Standard Recall - Under 12 Months	Determinate	DANIEL	WELLS	Recalled [*]	20696A	Determinate	Determinate	UNITED KINGDOM ( UK )	A5886AT	Failed to keep in touch	BREACH OF RESTRAINING ORDER	NPS - Nottinghamshire	NaN	NaN	4820/00N	True	White - British	Male	Standard	unlawful recall	1982-09-12	2017-02-17	1.0	2017-01-26	NaT	NaT	2017-02-16 13:13:00	2017-02-16 15:00:00	2017-02-17 11:19:00	2017-02-17 13:13:00	NaT	2017-02-21 11:19:00	2017-02-15 15:00:00	a. determinate	NPS - Nottinghamshire	b. NPS	Midlands	Midlands	standard	Under 12 months	2017-06-30	NaN	1.0	1.0	NaN	NaN	NaN	Standard - Less than 144 hours	Standard	Standard	a. Returned in target	0.0	Jan to Mar 2017	Determinate less than 12 months	Non-HDC	30 June 2017	Recalled in Jan to Mar 2017 returned by 30 June 2017	Recalled in Jan to Mar 2017 not returned by 30 June 2017

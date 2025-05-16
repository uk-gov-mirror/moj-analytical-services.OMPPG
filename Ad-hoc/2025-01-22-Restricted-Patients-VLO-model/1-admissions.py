""" 
GOAL: PRODUCE ADMISSION AaND RECALL STATISTICS FOR RESTRICTED PATIENT PUBLICATION
By Eric Nyame, 29/02/2024
"""

#---------------------------------- Import Packages

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

admis = pd.read_excel("rp_admissions_2024_b.xls")

admis = admis.replace("–","-", regex = True)

admis['AUTHORITY_FOR_DETENTION_DESCRIPTION'].value_counts(dropna=False)

not_hospital_orders = ['S48/49 - MHA 1983 - committed for Trial to CC',
                      'S48/49 - MHA 1983 - Remanded','S48/49 - MHA 1983 - Immigration Detainee','Not Applicable']

admis = admis[~admis['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(not_hospital_orders)]

len(admis) # 787

    # check datetime types
admis.info() # 121 all good

admis.head()

    # rearrange columns
# admis.columns

retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'ACTUAL_DATE',  'MOVE_TYPE_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION',
                'MOVE_SUB_SUB_TYPE_DESCRIPTION','FROM_ESTABLISHMENT_DESCRIPTION','TO_ESTABLISHMENT_DESCRIPTION']

admis = admis[retain_order + [col for col in admis.columns if col not in retain_order]]

admis.head()

#---------------Remove duplicates

admis[admis.duplicated(subset=['FILE_REFERENCE','ACTUAL_DATE'],keep = False)].sort_values(['FILE_REFERENCE','ACTUAL_DATE']).head(10) #0

len(admis) # 787

#---------------Remove Test cases
    # Check 'test' cases and remove
admis[admis['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

admis[admis['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (admis['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (admis['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (admis['FILE_REFERENCE'] != 'T18122')

admis = admis[~Test_Case_Mask]

len(admis) # 785

    # Check 'case' cases and remove
admis[admis['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

admis[admis['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
admis[admis['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

admis[admis['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none


admis.info() # 322


admis.head()

#--------------- Check active DAs

admis = admis.sort_values(by = ['FILE_REFERENCE','ACTUAL_DATE'],ascending=[True,False])

admis[admis.duplicated(['FILE_REFERENCE','ACTUAL_DATE','AUTHORITY_FOR_DETENTION_DESCRIPTION'], keep = False)] # 0

admis[admis.duplicated(['FILE_REFERENCE','ACTUAL_DATE'], keep = False)] # 0 cases, but authority for dentention differs

#--------------- Remove Non applicables and in foreign prisons

# admis[admis['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['Not Applicable', 'Not Specified'])]

admis = admis[~admis['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['Not Applicable', 'Not Specified'])]
len(admis) # 322

# admis[admis['CURRENT_ESTABLISHMENT_DESCRIPTION'].str.contains('Foreign', case=False)]

admis = admis[~admis['CURRENT_ESTABLISHMENT_DESCRIPTION'].str.contains('Foreign', case=False)]
len(admis) # 322

#---------------  Remove unrestricted patients

# admis['DA_CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

admis['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

admis = admis[admis['CUSTODY_TYPE_DESCRIPTION'] != 'Unrestricted Patient']
len(admis) # 781


#--------------- Export population before offence as Parquet
    
    # Conversions to satisfy parquet
    
admis['FILE_REFERENCE'] = admis['FILE_REFERENCE'].astype(str)
admis['NOMS_ID'] = admis['NOMS_ID'].astype(str)

admis.head()

# admis.to_parquet("output/admis.parquet")


offences = pd.read_excel("rp_admis_offences.xls")

offences = offences.replace("–","-",regex=True)

offences.head()

offences = offences[(offences['DATE_OF_HOSPITAL_ORDER'].dt.year >= 2023) | (offences['DATE_RECEIVED_IN_MHU'].dt.year >= 2023)]
offences.info() # 6322

# We will deduplicate the offences after the match 

    # offences = offences.sort_values(by=['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER'])

    # offences[offences.duplicated(['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER','OFFENCE_DESCRIPTION'],keep=False)] # don't worry about these yet

offences['FILE_REFERENCE'] = offences['FILE_REFERENCE'].astype(str)
offences['PRISON_NUMBER'] = offences['PRISON_NUMBER'].astype(str)


query2 = """SELECT a.*, 
                  b.OFFENCE_DESCRIPTION, 
                  b.OFFENCE_GROUP_DESCRIPTION,
                  b.COURT_OFFENCE_TEXT,
                  b.DATE_OF_HOSPITAL_ORDER
                  
            FROM admis AS a LEFT JOIN offences AS b
            
            ON  (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) 
            AND (a.AUTHORITY_FOR_DETENTION_DESCRIPTION = b.AUTHORITY_FOR_DETENTION_DESCRIPTION AND a.AUTHORITY_FOR_DETENTION_DESCRIPTION IS NOT NULL) """

admis_off = duckdb.sql(query2).df()
len(admis_off) # 1713

admis_off.head()

admis_off['OFFENCE_GROUP_DESCRIPTION'].value_counts(dropna=False)
# ----------------- Put together sorted missing offences

 retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'DATE_OF_HOSPITAL_ORDER','AUTHORITY_FOR_DETENTION_DESCRIPTION','OFFENCE_DESCRIPTION','OFFENCE_GROUP_DESCRIPTION','COURT_OFFENCE_TEXT']

admis_off = admis_off[retain_order + [col for col in admis.columns if col not in retain_order]]

specified_offences = ["Harassment","Harass","Stalking","Stalk","Breach","Breaching","Injunction","Fear ","Restraining","Restrain","Racially","Race","Religiously","Religion","Controlling","Control","Coercive","Coerce"]

pattern = '|'.join(specified_offences)

admis_off[admis_off['OFFENCE_DESCRIPTION'].str.contains(pattern, case=False, na=False)]['OFFENCE_DESCRIPTION'].value_counts(dropna=False)

admis_off[admis_off['COURT_OFFENCE_TEXT'].str.contains(pattern, case=False, na=False)]['COURT_OFFENCE_TEXT'].value_counts(dropna=False)

show(admis_off[admis_off['COURT_OFFENCE_TEXT'].str.contains(pattern, case=False, na=False)]['COURT_OFFENCE_TEXT'].value_counts(dropna=False),buttons='excel5')

# Keep only susptected cases
admis_off = admis_off[admis_off['COURT_OFFENCE_TEXT'].str.contains(pattern, case=False, na=False)]
len(admis_off) # 34

admis_off.head()

admis_off[admis_off['COURT_OFFENCE_TEXT'].str.contains('drug|theft|suspended|prevent|shpo|sopo', case=False, na=False)]['COURT_OFFENCE_TEXT'].value_counts(dropna=False)

admis_off = admis_off[~admis_off['COURT_OFFENCE_TEXT'].str.contains('drug|theft|suspended|prevent|shpo|sopo', case=False, na=False)]
len(admis_off) # 124

admis_off.head()

admis_off.to_excel("output/admis_inc_transfers.xlsx")

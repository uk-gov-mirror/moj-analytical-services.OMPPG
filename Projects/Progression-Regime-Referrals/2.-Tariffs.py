""" 
GOAL: PRODUCE ISP POP FOR OMSQ. 
By Eric Nyame, 05/02/2024
"""

#---------------------------------- Import Packages

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


#----------------------------------Import PPUD data

ispPPUD = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_ISP_{year}Q{quarter}.xls')
wlPPUD = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_WholeLife_{year}Q{quarter}.xls')

ispPPUD = ispPPUD.drop_duplicates()
wlPPUD = wlPPUD.drop_duplicates()

ispPPUD.info()
wlPPUD.info()

#----------------------------------Datetime columns appearing as object type - change

dateColsToChange = ['LATEST_RELEASE_DATE']

check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(ispPPUD,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in ispPPUD.columns if col not in dateColsToChange]]
check1
check1.shape # 2

    # Make two corrections to dates
for column in dateColsToChange:
    ispPPUD[column] = ispPPUD[column].astype(str).str.replace("8201-05-08 00:00:00", "2018-01-31 00:00:00") 
    ispPPUD[column] = ispPPUD[column].astype(str).str.replace("6201-07-09 00:00:00", "2011-06-09 00:00:00") 
    ispPPUD[column] = ispPPUD[column].astype(str).str.replace("2995-12-28 00:00:00", "") 
    ispPPUD[column] = ispPPUD[column].astype(str).str.replace("2922-01-07 00:00:00", "") 
    
   
    # Rerun check1 and see if if check1 is empty, then convert all datetime columns to datetime
    
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(ispPPUD,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in ispPPUD.columns if col not in dateColsToChange]]
check1.shape # 0

    # change certain columns to pandas datetime type

for column in dateColsToChange:
    ispPPUD[column] = pd.to_datetime(ispPPUD[column])

strip_blanks(ispPPUD)
strip_blanks(wlPPUD)

ispPPUD.info()
wlPPUD.info()

ispPPUD.dtypes.value_counts()
wlPPUD.info()
#---------------------------------- Add whole life flag to PPUD ISP data

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query = """SELECT a.*, 
                  b.WHOLE_LIFE 
                  
            FROM ispPPUD AS a 
            LEFT JOIN (SELECT DISTINCT PRISON_NUMBER, WHOLE_LIFE, DOS FROM wlPPUD) AS b
            
            ON  a.PRISON_NUMBER = b.PRISON_NUMBER AND
            a.DOS = b.DOS"""

ispPPUD_Matched = duckdb.sql(query).df()
ispPPUD_Matched.shape # 25326, 25222

ispPPUD_Matched.loc[ispPPUD_Matched['WHOLE_LIFE'] == True,'TARIFF_EXPIRY_DATE'] = pd.Timestamp.max.normalize()

# ispPPUD_Matched[ispPPUD_Matched['WHOLE_LIFE'] == True]['TARIFF_EXPIRY_DATE'].head()

ispPPUD_Matched = prepareMatch.prepareMatch(ispPPUD_Matched)

#---------------------------------- Match to A&O Dataset on either NOMIS number, Prison Number or Name and DOB

query = """SELECT DISTINCT a.*, 
                            b.DOS, b.TARIFF_EXPIRY_DATE, 
                            b.EXCLUDED_FROM_OPEN, 
                            b.WHOLE_LIFE, 
                            b.CUSTODY_TYPE_DESCRIPTION, 
                            b.STATUS_DESCRIPTION,
                            b.LATEST_RELEASE_DATE, 
                            b.FAMILY_NAME AS SURNAME_PPUD, 
                            b.DOB AS DOB_PPUD, 
                            b.INIT AS INIT_PPUD,
                            b.PRISON_NUMBER, 
                            b.PN_TRIM, 
                            b.PN_START, 
                            b.PN_END,
                            b.INDEX_OFFENCE_DESCRIPTION,
                            b.CURRENT_ESTABLISHMENT_DESCRIPTION AS PPUD_PRISON, 
                            b.NOMS_ID AS NOMS_ID_PPUD, 
                            b.NOMS_TRIM, 
                            b.NOMS_START, 
                            b.NOMS_END,
                            b.PROBATION_SERVICE_DESCRIPTION
                            
                    FROM openMatched AS a LEFT JOIN ispPPUD_Matched AS b
                    
                    ON a.EXTRACTDATE >= b.DOS AND 
                      (a.NOMIS_ID = b.NOMS_ID OR
                       a.NOMIS_ID = b.NOMS_TRIM OR
                       a.NOMIS_ID = b.NOMS_START OR
                       a.NOMIS_ID = b.NOMS_END OR
                       a.NOMIS_ID = b.PRISON_NUMBER OR
                       a.NOMIS_ID = b.PN_TRIM OR
                       a.NOMIS_ID = b.PN_START OR
                       a.NOMIS_ID = b.PN_END)"""

ispTariffs = duckdb.sql(query).df()
ispTariffs.shape # 22811, 22936, 22218

# subset
ispTariffs = ispTariffs[(ispTariffs['SENTENCESTATUS'].isin(['(5) IPP','(6) Life'])) | 
                        (~(ispTariffs['CUSTODY_TYPE_DESCRIPTION'].isna())) | 
                        (~(ispTariffs['TARIFF_EXPIRY_DATE'].isna()))]

ispTariffs.shape # 11300, 11323, 11325,11336, 11352, 11356

    # Rate quality of matches
    
def calculate_match(row):
    
    condition_a = pd.notna(row['NOMIS_ID']) and (
        row['NOMIS_ID'] in [row['NOMS_ID_PPUD'], row['NOMS_TRIM'], row['NOMS_START'], row['NOMS_END']]
    )
    
    condition_b = pd.notna(row['NOMIS_ID']) and (
        row['NOMIS_ID'] in [row['PRISON_NUMBER'], row['PN_START'], row['PN_END'], row['PN_TRIM']]
    )
    condition_c = (
        pd.notna(row['SURNAME']) and row['SURNAME'] == row['SURNAME_PPUD'] and
        pd.notna(row['DATEOFBIRTH']) and row['DATEOFBIRTH'] == row['DOB_PPUD'] and
        pd.notna(row['INITIAL']) and row['INITIAL'] == row['INIT_PPUD']
    )
    
    if condition_a and condition_c:
        return 4
    elif (condition_a or condition_b) and condition_c:
        return 3
    elif (condition_a or condition_b):
        return 2
    elif condition_c:
        return 1
    else:
        return 0

    # Create Match column by applying the function to each row
ispTariffs['MATCH'] = ispTariffs.apply(calculate_match, axis=1)

ispTariffs['EFFECTIVE_TED'] = ispTariffs.groupby('NOMIS_ID')['TARIFF_EXPIRY_DATE'].transform('max')

ispTariffs['CUS_PROPER'] = np.where(ispTariffs['CUSTODY_TYPE_DESCRIPTION'].isin(['IPP', 'DPP']),'(5) IPP','(6) Life')

ispTariffs['SENT_RANK'] = np.where(ispTariffs['SENTENCESTATUS'] == ispTariffs['CUS_PROPER'],1,2)

ispTariffs = ispTariffs.sort_values(by=['NOMIS_ID','MATCH','SENT_RANK','CUS_PROPER','TARIFF_EXPIRY_DATE','DOS','LATEST_RELEASE_DATE'],ascending = [True,False,True,False,False,True,False])

ispTNodup = ispTariffs.drop_duplicates(subset='NOMIS_ID', keep ='first').copy()

ispTNodup.shape # 10934, 10963,10976, 10993, 11000

#----------------------------------Add detailed offence groups

ispTNodup['OFFENCE_UPPER'] = ispTNodup['OFFENCE'].str.upper()
ispTNodup = ispTNodup.drop(['CUS_PROPER','SENT_RANK'], axis = 1)

offLookup = pd.read_excel("s3://alpha-omppg/isp-population/Reference/ISP Lookup.xls",sheet_name='Offences')
offLookup.columns = offLookup.columns.str.upper()
strip_blanks(offLookup)
offLookup = offLookup.drop_duplicates(subset='OFFENCE_UPPER', keep ='first')
offLookup.info()

query = """SELECT a.*, 
                  b.DETAILED_OFFENCE_GROUP 
                  
            FROM ispTNodup AS a LEFT JOIN offLookup AS b
            
            ON  a.OFFENCE_UPPER = b.OFFENCE_UPPER """

ispTNodup = duckdb.sql(query).df()

ispTNodup.shape # 10963

    # drop some columns
    
ispTNodup = ispTNodup.drop(['MATCH','SURNAME_PPUD', 'DOB_PPUD', 'INIT_PPUD','PN_TRIM', 'PN_START', 'PN_END', 'NOMS_ID_PPUD', 'NOMS_TRIM', 'NOMS_START', 'NOMS_END'],axis = 1)

#---------------------------------- Create final derived variables
    # tariff past
    
notIPP = (ispTNodup['SENTENCESTATUS'] == '(5) IPP') & (ispTNodup['TARIFF_EXPIRY_DATE'].dt.year < 2005)

ispTNodup.loc[notIPP,'TARIFF_EXPIRY_DATE'] = pd.NaT

tpast1 = (ispTNodup['TARIFF_EXPIRY_DATE'].isna()) | (ispTNodup['TARIFF_EXPIRY_DATE'] == pd.Timestamp(1900,1,1))
tpast2 = (ispTNodup['WHOLE_LIFE'] == True) | (ispTNodup['TARIFF_EXPIRY_DATE'] >= ispTNodup['EXTRACTDATE'])
tpast3 = ispTNodup['TARIFF_EXPIRY_DATE'] < ispTNodup['EXTRACTDATE']

ispTNodup.loc[tpast1,'TARIFF_PAST'] = 'n/a'
ispTNodup.loc[~(tpast1) & (tpast2),'TARIFF_PAST'] = 'N'
ispTNodup.loc[~(tpast1) & ~(tpast2) & (tpast3),'TARIFF_PAST'] = 'Y'

ispTNodup.loc[ispTNodup['SENTENCESTATUS'] == '(7) Recall','TARIFF_PAST'] = 'Y'

ispTNodup['TARIFF_PAST'].value_counts(dropna=False)

    # Tariff length in years and months

tmth = ispTNodup['TARIFF_EXPIRY_DATE'] >= ispTNodup['DOS']
tmth2 = (ispTNodup['TARIFF_EXPIRY_DATE'].dt.year == 1900) | (ispTNodup['TARIFF_EXPIRY_DATE'].dt.year == pd.Timestamp.max.year)

ispTNodup['TARIFF_MONTHS'] = np.where(tmth,
                                        ispTNodup.apply(lambda x: TimeDiffs.month_diff(x['DOS'],x['TARIFF_EXPIRY_DATE']),axis=1),
                                        np.nan)
                        
ispTNodup.loc[tmth2,'TARIFF_MONTHS'] = np.nan

ispTNodup['TARIFF_YEARS'] = ispTNodup['TARIFF_MONTHS'] // 12

    # Years and months in prison

ispTNodup['SERVED_MONTHS'] = ispTNodup.apply(lambda x: TimeDiffs.month_diff(x['DOS'],x['EXTRACTDATE']),axis=1)

ispTNodup['SERVED_YEARS'] = ispTNodup['SERVED_MONTHS'] // 12

    # Number of tariffs spent in prison

ispTNodup['TARIFFS_SERVED'] = np.where((ispTNodup['TARIFF_MONTHS'].isna()) | (ispTNodup['TARIFF_EXPIRY_DATE'] == ispTNodup['DOS']),
                                         np.nan,
                                         (ispTNodup['EXTRACTDATE'] -ispTNodup['DOS'])//(ispTNodup['TARIFF_EXPIRY_DATE'] -ispTNodup['DOS']))

     # Number of years and months spent in prison post tariff

ispTNodup['OVERTARIFF_MONTHS'] = np.where(ispTNodup['TARIFF_PAST'] == 'Y',
                                        ispTNodup.apply(lambda x: TimeDiffs.month_diff(x['TARIFF_EXPIRY_DATE'],x['EXTRACTDATE']),axis=1),
                                        np.nan)

ispTNodup['OVERTARIFF_YEARS'] = ispTNodup['OVERTARIFF_MONTHS'] // 12

    # Age at time of sentence
ispTNodup['DATEOFBIRTH'] = pd.to_datetime(ispTNodup['DATEOFBIRTH'],dayfirst=True)

ispTNodup['SENTENCED_AGE'] = np.where(ispTNodup['DOS'] > ispTNodup['DATEOFBIRTH'],
                                         ispTNodup.apply(lambda x: TimeDiffs.year_diff(x['DATEOFBIRTH'],x['DOS']),axis=1),
                                        np.nan)

  # Hitting tariff in next quarter
next_day = pd.Timestamp(year,int(month),day)+ np.timedelta64(1,'D')

next_day_year = next_day.year
next_day_quarter = next_day.quarter

ted_in_quart_cond = ((ispTNodup['TARIFF_EXPIRY_DATE'].dt.quarter == next_day_quarter) & (ispTNodup['TARIFF_EXPIRY_DATE'].dt.year == next_day_year))

ted_in_quart_cond.sum()

ispTNodup['TARIFF_IN_QUARTER'] = np.nan 

ispTNodup.loc[ted_in_quart_cond, 'TARIFF_IN_QUARTER'] = ispTNodup['TARIFF_EXPIRY_DATE']

    # Tariff length - publication categories

ispTNodup = tariff_groups.tariff_groups(ispTNodup)

    # Invalid Latest Release Date

ispTNodup.loc[ispTNodup['LATEST_RELEASE_DATE'] < ispTNodup['TARIFF_EXPIRY_DATE'], 'LATEST_RELEASE_DATE'] = pd.NaT

#---------------------------------- At most four years to Tarrif
ispTNodup['TARIFF_PAST'].value_counts(dropna=False)

ispTNodup['MONTHS_TO_TARIFF_EXPIRY'] = np.where(ispTNodup['TARIFF_PAST']=='N',
                                         ispTNodup.apply(lambda x: TimeDiffs.month_diff(x['EXTRACTDATE'],x['TARIFF_EXPIRY_DATE']),axis=1),
                                        np.nan)

ispTNodup['MONTHS_TO_TARIFF_EXPIRY'].value_counts(dropna=False)

ispTNodup['FOUR_YRS_MOST_TO_TED'] = np.where(ispTNodup['MONTHS_TO_TARIFF_EXPIRY'] <= 48,'Y','N')

ispTNodup.loc[ispTNodup['TARIFF_PAST'] == 'Y','FOUR_YRS_MOST_TO_TED'] = 'Tariff Past'

ispTNodup['FOUR_YRS_MOST_TO_TED'].value_counts(dropna=False)

    # Classify ISPs based on NOMIS sentence status, adding sentence information to recalls from PPUD

ispTNodup['SENTENCESTATUS'].value_counts(dropna=False)

nomis_recall_cond = (ispTNodup['SENTENCESTATUS'] == '(7) Recall')
missing_cus_type = ispTNodup['CUSTODY_TYPE_DESCRIPTION'].isna()
ipp_cus_type = ispTNodup['CUSTODY_TYPE_DESCRIPTION'].isin(['IPP','DPP'])

ispTNodup['ISP_STATUS'] = ''
ispTNodup.loc[nomis_recall_cond & missing_cus_type,'ISP_STATUS'] = 'Recalled ISP (unknown sentence)'
ispTNodup.loc[nomis_recall_cond & ipp_cus_type,'ISP_STATUS'] = 'Recalled IPP'
ispTNodup.loc[nomis_recall_cond & ~(missing_cus_type) & ~(ipp_cus_type),'ISP_STATUS'] = 'Recalled Life'

ispTNodup.loc[ispTNodup['SENTENCESTATUS'] == '(5) IPP','ISP_STATUS'] = 'Unreleased IPP'
ispTNodup.loc[ispTNodup['SENTENCESTATUS'] == '(6) Life','ISP_STATUS'] = 'Unreleased Life'

ispTNodup['ISP_STATUS'].value_counts(dropna=False)

ispTNodup['ISP_STATUS'].value_counts(dropna=False) # matches

ispTNodup = ispTNodup[~ispTNodup['ISP_STATUS'].isna()]

ispTNodup.info()

#---------------------------------- Temporary Save, delete later
ispTNodup.to_parquet("ispTNodup.parquet")


#ispTNodup2['TARIFF_IN_QUARTER'].value_counts(dropna=False)

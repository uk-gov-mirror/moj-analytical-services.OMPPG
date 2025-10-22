""" 
GOAL: ADD FIRST RELEASE INFORMATION FOR QUARTERLY ISP POP FOR OMSQ
By Eric Nyame, 05/02/2024
"""

#----------------------------------Match to ISP Population Dataset on either NOMIS number, Prison Number or Name and 

query6 = """SELECT DISTINCT a.*,                                    
                        b.RELEASE_DATE AS LAST_RELEASE_DATE, 
                        b.RELEASE_TYPE AS LAST_RELEASE_TYPE,
                        b.RELEASE_CONDITIONS AS LAST_RELEASE_CONDITIONS,
                        b.FAMILY_NAME AS SURNAME_PPUD, 
                        b.DOB AS DOB_PPUD, 
                        b.INIT AS INIT_PPUD,
                        b.PRISON_NUMBER AS PN2, 
                        b.PN_TRIM, 
                        b.PN_START, 
                        b.PN_END, 
                        b.NOMS_ID AS NOMS_ID_PPUD, 
                        b.NOMS_TRIM, 
                        b.NOMS_START, 
                        b.NOMS_END
                        
            FROM ispFirstRel AS a LEFT JOIN isp_releases_final AS b
                        
                        ON (a.EXTRACTDATE >= b.DOS OR b.DOS IS NULL) AND
                        a.EXTRACTDATE > b.RELEASE_DATE AND
                        (a.TARIFF_EXPIRY_DATE <= b.RELEASE_DATE OR a.TARIFF_EXPIRY_DATE IS NULL) AND
                        a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL"""

ispRelMatched = duckdb.sql(query6).df()
ispRelMatched.shape # 13483, 13420, 13406, 13354, 13380

#---------------------------------- Rate quality of the match
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
ispRelMatched['MATCH'] =ispRelMatched.apply(calculate_match, axis=1)

    # deduplicate
ispRelMatched = ispRelMatched.sort_values(by=['MATCH','LAST_RELEASE_DATE'],ascending = [False,False])

ispLastRel =ispRelMatched.drop_duplicates(subset='NOMIS_ID', keep ='first').copy()
ispLastRel.shape # 10886, 10881, 10899, 10902, 10939, 10961, 10995

#---------------------------------- drop some variables

ispLastRel = ispLastRel.drop(['MATCH', 'SURNAME_PPUD', 'DOB_PPUD', 'INIT_PPUD', 'PN2', 'PN_TRIM','PN_START', 
                                        'PN_END', 'NOMS_ID_PPUD', 'NOMS_TRIM', 'NOMS_START', 'NOMS_END'],axis=1)

ispLastRel.shape # 10886, 10881, 10899, 10902, 10939, 10961, 10995

#---------------------------------- Save
ispLastRel.to_parquet("ispLastRel.parquet")

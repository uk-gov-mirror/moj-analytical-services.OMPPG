""" 
GOAL: PRODUCE RE-RELEASES OF ISPS FOR OMSQ. A BY-PRODUCT IS FIRST RELEASES OF ISPS
By Eric Nyame, 05/02/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


#---------------------------------- Add releases to recalls dataset

# set duckdb sample size to 100000
duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query4 = """SELECT a.*, 
                b.RELEASE_DATE AS FIRST_RELEASE_DATE,
                b.RELEASE_CONDITIONS AS FIRST_RELEASE_CONDITIONS,
                b.PRISON_NUMBER AS REL_PRISNUM, 
                b.FILE_REFERENCE AS REL_FILEREF,
                b.FAMILY_NAME AS REL_SURNAME, 
                b.INIT AS REL_INIT,
                b.DOB AS REL_DOB
                
            FROM recalls_nodup AS a LEFT JOIN isp_releases_final AS b
            
            ON  (a.LICENCE_REVOKE_DATE >= b.RELEASE_DATE) AND
                (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL)
                ) AND b.RELEASE_TYPE = 'First Release'"""

release_to_recall = duckdb.sql(query4).df()
release_to_recall.shape # 10860, 10659, 10414,10180,9909

def calculate_match(row):
   
    condition_a = (row['FILE_REFERENCE'] == row['REL_FILEREF'])
    condition_b = (row['PRISON_NUMBER'] == row['REL_PRISNUM'])
      
    if condition_a and condition_b:
        return 2
    elif condition_a:
        return 1
    elif condition_b:
        return 1
    else:
        return 0

# Apply the function to each row
release_to_recall['MATCH'] = release_to_recall.apply(calculate_match, axis=1)

release_to_recall = release_to_recall.drop(['REL_PRISNUM','REL_FILEREF','REL_SURNAME','REL_INIT','REL_DOB'],axis=1)

# release_to_recall[release_to_recall['FILE_REFERENCE'].isna()].head()[['FILE_REFERENCE','REL_FILEREF','MATCH','PRISON_NUMBER','REL_PRISNUM']]

# release_to_recall['MATCH'].value_counts(dropna=False)

#---------------------------------- deduplicate

release_to_recall['UNIQUEREF']= release_to_recall['PRISON_NUMBER'].astype(str) + release_to_recall['LICENCE_REVOKE_DATE'].astype(str)

release_to_recall.sort_values(by=['MATCH','FIRST_RELEASE_DATE'],ascending = [False,True], inplace = True)
release_to_recall.drop_duplicates(subset=['UNIQUEREF'], keep ='first', inplace = True)
release_to_recall.shape # 10840, 10640, 10395,10162,9891

#---------------------------------- Add releases to recalls dataset

query5 = """SELECT a.*, 
                b.RELEASE_DATE AS LAST_RELEASE_DATE, 
                b.RELEASE_TYPE AS LAST_RELEASE_TYPE,
                b.RELEASE_CONDITIONS AS LAST_RELEASE_CONDITIONS,
                b.PRISON_NUMBER AS REL_PRISNUM, 
                b.FILE_REFERENCE AS REL_FILEREF,
                b.FAMILY_NAME AS REL_SURNAME,
                b.INIT AS REL_INIT,
                b.DOB AS REL_DOB
                 
            FROM release_to_recall AS a LEFT JOIN isp_releases_final AS b
            
            ON  (a.LICENCE_REVOKE_DATE >= b.RELEASE_DATE) AND
                (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL)
                ) """

release_to_recall2 = duckdb.sql(query5).df()
release_to_recall2.shape 18320, # 17800,17224,16647,16002

# Apply the function to each row
release_to_recall2['MATCH'] = release_to_recall2.apply(calculate_match, axis=1)

#release_to_recall2['MATCH'].value_counts(dropna=False)

release_to_recall2 = release_to_recall2.drop(['REL_PRISNUM','REL_FILEREF','REL_SURNAME','REL_INIT','REL_DOB'],axis=1)

release_to_recall2['UNIQUEREF']= release_to_recall2['PRISON_NUMBER'].astype(str) + release_to_recall2['LICENCE_REVOKE_DATE'].astype(str)

#---------------------------------- deduplicate
release_to_recall2.sort_values(by=['MATCH','LAST_RELEASE_DATE'],ascending = [False,False], inplace = True)

release_to_recall2 = release_to_recall2.drop_duplicates(subset=['UNIQUEREF'], keep ='first')
release_to_recall2.shape # 10840,  10640,10395,10162, 9891

#---------------------------------- Add releases to recalls dataset

query6 = """SELECT a.*, 
                b.RELEASE_DATE AS NEXT_RELEASE_DATE,
                b.RELEASE_TYPE AS NEXT_RELEASE_TYPE,
                b.RELEASE_CONDITIONS AS NEXT_RELEASE_CONDITIONS,
                b.PRISON_NUMBER AS REL_PRISNUM, 
                b.FILE_REFERENCE AS REL_FILEREF,
                b.FAMILY_NAME AS REL_SURNAME, 
                b.INIT AS REL_INIT,
                b.DOB AS REL_DOB
                
            FROM release_to_recall2 AS a LEFT JOIN isp_releases_final AS b
            ON  (a.RTC_DATE < b.RELEASE_DATE AND a.RTC_DATE IS NOT NULL) AND
                (a.LICENCE_REVOKE_DATE < b.RELEASE_DATE) AND
                (a.NEXT_RECALL_DATE >= b.RELEASE_DATE OR a.NEXT_RECALL_DATE IS NULL) AND
                (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL)
                ) """

release_to_recall3 = duckdb.sql(query6).df()
release_to_recall3.shape # 10874,  10670,10423,10190,9916

# Apply the function to each row
release_to_recall3['MATCH'] = release_to_recall3.apply(calculate_match, axis=1)

#release_to_recall2['MATCH'].value_counts(dropna=False)

release_to_recall3 = release_to_recall3.drop(['REL_PRISNUM','REL_FILEREF','REL_SURNAME','REL_INIT','REL_DOB'],axis=1)

release_to_recall3['UNIQUEREF']= release_to_recall3['PRISON_NUMBER'].astype(str) + release_to_recall3['LICENCE_REVOKE_DATE'].astype(str)

#---------------------------------- deduplicate
release_to_recall3.sort_values(by=['MATCH','NEXT_RELEASE_DATE'],ascending = [False,True], inplace = True)

release_to_recall3 = release_to_recall3.drop_duplicates(subset=['UNIQUEREF'], keep ='first')
release_to_recall3.shape # 10840, 10640, 10395,10162, 9891

#--------------MONTHS UNTIL RE-RELEASE
    
isp_recalls_final = release_to_recall3.copy()

isp_recalls_final['MONTHS_UNTIL_RELEASE'] = isp_recalls_final.apply(lambda x: TimeDiffs.month_diff(x['RTC_DATE'],x['NEXT_RELEASE_DATE']),axis=1)


# --------------------------- RELEASED_WITHIN_X_MONTHS OF RTC
'''
Logic: (1) OF THOSE who have been RTC'd AT LEAST 3 months in prison up to the end of the current period, 
           which ones got rereleased within 3 months?.
       (2) OF THOSE who have been RTC'd AT LEAST 6 months in prison up to the end of the current period, 
           which ones got rereleased within 6 months?.
           
Caveat: This is NOT determining who got rereleased with 3 months of all those RTC'd up to the end of the current period.
        Notice that some could have been RTC'd and subsequently rereleased within, say, 5 days to the end of the current
        period; however, these would not have had full three months RTC'd in prison, so we are not interested in them.
        
Future dev: Is this useful? What is the alternative? 

''' 

isp_recalls_final['LATEST_QUARTER'] = pd.Timestamp(year, quarter * 3 - 2, 1) - pd.Timedelta(days=1) # end of last quarter

rtcAtleast3MthsAgo = isp_recalls_final['RTC_DATE'] <= isp_recalls_final['LATEST_QUARTER']
rtcAtleast6MthsAgo = isp_recalls_final['RTC_DATE'] <= (isp_recalls_final['LATEST_QUARTER'] - pd.DateOffset(months = 3))
rtcAtleast12MthsAgo = isp_recalls_final['RTC_DATE'] <= (isp_recalls_final['LATEST_QUARTER'] - pd.DateOffset(months = 9))

isp_recalls_final['RELEASED_3_MONTHS'] = np.where(rtcAtleast3MthsAgo, 
                                                        np.where(isp_recalls_final['MONTHS_UNTIL_RELEASE'] < 3,100,0),
                                                    np.nan)


isp_recalls_final['RELEASED_6_MONTHS'] = np.where(rtcAtleast6MthsAgo, 
                                                        np.where(isp_recalls_final['MONTHS_UNTIL_RELEASE'] < 6,100,0),
                                                    np.nan)

isp_recalls_final['RELEASED_12_MONTHS'] = np.where(rtcAtleast12MthsAgo, 
                                                        np.where(isp_recalls_final['MONTHS_UNTIL_RELEASE'] < 12,100,0),
                                                    np.nan)

isp_recalls_final.drop(['UNIQUEREF','MATCH'],axis=1,inplace = True)

isp_recalls_final.shape # 10840, 10640,10395,10162, 9891

isp_recalls_final.head()

#---------------------------------- Save to Amazon

isp_recalls_final.to_parquet(f"s3://alpha-omppg/Recalls/final_data/recalls/isp/isp_recalls_{year}q{quarter}.parquet",index=False)
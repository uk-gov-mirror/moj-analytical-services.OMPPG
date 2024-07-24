# QUESTION -
 """ Please could you tell me how many IPP licences have been terminated whilst the individual is in custody having been recalled on their IPP licence """

# Models and settings
import pandas as pd
import duckdb

pd.options.display.max_columns = None
pd.options.display.max_rows = None

# Import Terminations Data
Terminations_to_30June2023 = pd.read_excel("s3://alpha-omppg/Data Central/IPP Licence Terminations/Terminations_Approved_up_to_30June2023.xlsx")
Terminations_to_30June2023.head()
Terminations_to_30June2023.dtypes
len(Terminations_to_30June2023) #234

# Import Releases Data
Releases_2013_to_30Sep2023 = pd.read_excel("s3://alpha-omppg/Data Central/PPUD Releases/ISP_Releases_2013_to_30Sep2023.xls")
Releases_2013_to_30Sep2023.head()
Releases_2013_to_30Sep2023.dtypes

    # Check custody types of release data
Releases_2013_to_30Sep2023["CUSTODY_TYPE_DESCRIPTION"].value_counts(dropna = False)

# Match Terminations and Releases
query =  """SELECT a.*, 
                   b.RELEASE_DATE,
                   b.RELEASE_TYPE_DESCRIPTION
            FROM Terminations_to_30June2023 AS a LEFT JOIN Releases_2013_to_30Sep2023 AS b 
            ON  (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL)"""

Terminations_and_Releases = duckdb.sql(query).df()
Terminations_and_Releases.head()

# COUNT SOME CASES OF INTEREST - THRE THREE MUST ADD UP
len(Terminations_and_Releases) # 256
len(Terminations_and_Releases[Terminations_and_Releases['RELEASE_DATE'] <= Terminations_and_Releases['ACTUAL']])
len(Terminations_and_Releases[Terminations_and_Releases['RELEASE_DATE'] > Terminations_and_Releases['ACTUAL']])
len(Terminations_and_Releases[pd.isna(Terminations_and_Releases['RELEASE_DATE']) | pd.isna(Terminations_and_Releases['ACTUAL'])])


# SELECT CASES WHERE RELEASE DATE IS ON OR AFTER THE TERMINATION DATE
Terminations_on_recall = Terminations_and_Releases[Terminations_and_Releases['RELEASE_DATE'] >= \
                                                    Terminations_and_Releases['ACTUAL']].copy()
len(Terminations_on_recall) # 0

# REPORT


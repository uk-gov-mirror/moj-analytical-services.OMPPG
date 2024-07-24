# QUESTION -
 """ The full question is
To ask His Majesty's Government how many applications for transfer from prison to hospital were decided
(1) within the target timescales set by the HM Prison and Probation Service Mental Health Casework Section, and (2) outside the target timescales;
and of those transfers decided outside of the target timescales, what was the average length of delay, in each of the last five years. """

# Models and settings
import pandas as pd
import duckdb

pd.options.display.max_columns = None
pd.options.display.max_rows = None

# Import Transfers Data
Transfers = pd.read_excel("s3://alpha-omppg/PQs/2024 01 15 Time to transfer.xls")
Transfers.head()
Transfers.dtypes
len(Transfers) #234

# Check milestone distribution
MilestoneDistribution = Transfers["TITLE"].value_counts(dropna = False)
MilestoneDistribution = MilestoneDistribution.rename_axis('TITLE')
MilestoneDistribution = MilestoneDistribution.reset_index(name='COUNT')
print(MilestoneDistribution)

# Reclassify TITLE to shorten it
05 -

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


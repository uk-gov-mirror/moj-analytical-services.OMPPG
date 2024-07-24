
# READ DATA FROM AMAZON WAREHOUSE
Licence_issued = pd.read_excel("s3://alpha-omppg/Ad hoc/2023 04 30 - Time from Decision to Release/Licence_issued_ISP_EDS.xls")
Recon_final = pd.read_excel("s3://alpha-omppg/Ad hoc/2023 04 30 - Time from Decision to Release/Recon_final_ISP_EDS.xls")

# DEDUPLICATE
Releases = Releases.drop_duplicates(subset=['PRISON_NUMBER', 'RELEASE_DATE'])
Decisions_Release = Decisions_Release.drop_duplicates(subset=['PRISON_NUMBER', 'SUBSEQUENT_OUTCOME_ACTUAL'])
len(Releases.index)
len(Decisions_Release.index)
Decisions_Release.head()


# BRING IN RELEASE INFO

proc sql; create table kabom as select
a.*,b.RELEASE_DATE,b.RELEASE_TYPE_DESCRIPTION 
from RELEASE_DECISIONS as a left join RELEASES as b
on (
(a.PRISON_NUMBER =b.PRISON_NUMBER and not missing(b.PRISON_NUMBER)) or 
(a.NOMS_ID=b.NOMS_ID and not missing(b.NOMS_ID))) and 
b.RELEASE_DATE ge a.SUBSEQUENT_OUTCOME_ACTUAL;
quit;

Kabom = duckdb.sql("""
        SELECT a.*,b.RELEASE_DATE,b.RELEASE_TYPE_DESCRIPTION
        FROM Decisions_Release AS a LEFT JOIN Releases AS b
        ON ((a.PRISON_NUMBER = b.PRISON_NUMBER and b.PRISON_NUMBER IS NOT NULL) or 
            a.NOMS_ID = b.NOMS_ID and b.NOMS_ID IS NOT NULL) and 
            b.RELEASE_DATE > a.SUBSEQUENT_OUTCOME_ACTUAL""").df()

len(Kabom.index)
# CHECK SUBSEQUENT OUTCOMES AND KEEP RELEASES ONLY
Decisions_Release["SUBSEQUENT_OUTCOME_DESCRIPTION"].value_counts()

Outcomes_Release = ["Direct Release", 
                    "Release (SO) [**]", 
                    "Immediate Release",
                    "Immediate Release (determ. recall ONLY)",
                    "Recommend Release",
                    "Release (SO) [*]",
                    "Release at a Future Date",
                    "Release at specified date (determ. recall ONLY)"]

Decisions_Release = Decisions_Release[Decisions_Release["SUBSEQUENT_OUTCOME_DESCRIPTION"].isin(Outcomes_Release)]

#DEDUPLICATE ACCROSS ALL COLUMNS
Decisions_Release = Decisions_Release.drop_duplicates()

# TEST CASES 
def checkTestCases(df):
    test_cases = df[(df["FAMILY_NAME"].str.contains("test", case = False,regex = False)) | 
                    (df["FIRST_NAMES"].str.contains("test", case = False,regex = False)) | \
                    (df["PRISON_NUMBER"].str.contains("test", case = False,regex = False))
                   ]
    return test_cases

checkTestCases(Decisions_Release)

def removeTestCases(df,to_keep):
    for column in ["FAMILY_NAME","FIRST_NAMES","PRISON_NUMBER"]:
        df = df[(~df[column].str.contains("test", case = False,na=False,regex = False)) | (df["NOMS_ID"].isin(to_keep))]
    return df

Decisions_Release = removeTestCases(Decisions_Release,['A9432AC'])

len(Decisions_Release.index) # 10115 entries

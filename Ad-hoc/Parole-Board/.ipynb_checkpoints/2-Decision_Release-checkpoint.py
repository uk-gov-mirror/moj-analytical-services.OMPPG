
# READ DATA FROM AMAZON WAREHOUSE
Decisions_Release = pd.read_excel("s3://alpha-omppg/Ad hoc/2023 04 30 - Time from Decision to Release/Release_Decisions_ISP_EDS.xls")
Decisions_Release.info() # date fields are good

Decisions_Release.head()

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

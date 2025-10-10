
eds = pd.read_csv(f"s3://alpha-omppg/data-central/PR_referrals/DAO_{year}_{month}_{day}.csv")
eds.columns = eds.columns.str.upper()
eds['SENTENCESTATUS'].value_counts()

#eds[eds['PED'].notna()]['PED'].head()
#eds[eds.columns[:100]].info()

eds['PED'] = pd.to_datetime(eds['PED'],dayfirst=True)

two_years_from_today = (pd.Timestamp.today() + pd.DateOffset(years=2)).normalize()
ped_mask = eds['PED'] <= two_years_from_today
ped_mask.sum() # 5254, 5450, 5070, 4960

eds = eds[ped_mask].reset_index(drop=True)
eds.shape

for i in eds.columns:
    print(i)
# pop[ped_mask | sentence_mask].to_csv("s3://alpha-omppg/Eric-Temp/Central Referall/Charlotte/DAO_2024_05_17.csv")

colKeep = ['NOMIS_NO', 'FIRST_MOVEMENT_DATE', 'JISL_YEARS','FORENAME1', 'SURNAME', 'DOB', 'PED', 'PRISONNAME', 'NATIONALITY_LONG', 'MAIN_OFFENCE_DESCRIPTION', 'OFFENCEGROUP', 'PRISONEDREGION', 'COURT_DESC', 'SENTENCE_LENGTH_BANDED', 'SENTENCESTATUS']

eds2 = eds[colKeep]

eds2.head()

#---------------------------------- Save
eds2.to_parquet(f"s3://alpha-omppg/Eric-Temp/Central Referall/Charlotte/eds.parquet",index=False)
eds2.to_excel(f"s3://alpha-omppg/Eric-Temp/Central Referall/Charlotte/eds.xlsx",index=False)

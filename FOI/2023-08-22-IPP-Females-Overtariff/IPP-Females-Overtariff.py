import pandas as pd

pd.options.display.max_columns = None
pd.options.display.max_rows = None

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

pop = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2024q1.sas7bdat", encoding='latin1')
pop.head()

condition = (pop["isp_status"] == "Unreleased IPP") & (pop["OVERTARIFF_YEARS"].notnull()) & (pop["PrisonGender"] =="F")

pop[condition].groupby("OVERTARIFF_YEARS").size()

pop['PRISON_NUMBER'].isna().sum()

pop['PRISON_NUMBER'].to_excel('Pris.xlsx')

pop[pop['custody_type_description']=='Automatic']['ImprisonmentStatusShort'].value_counts(dropna=False)

pop['custody_type_description'].value_counts(dropna=False)

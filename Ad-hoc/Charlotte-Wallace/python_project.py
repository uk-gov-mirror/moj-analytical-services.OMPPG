import pandas as pd
import numpy as np

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


# IMPORT DATASETS - FIND A BETTER WAY TO LOOP FOR THE IMPORT
Jun23= pd.read_sas("s3://alpha-omppg/ISP Population/final-data/isp_pop_2023q3.sas7bdat", encoding='latin1')
Sep23= pd.read_sas("s3://alpha-omppg/ISP Population/final-data/isp_pop_2023q4.sas7bdat", encoding='latin1')
Dec23= pd.read_sas("s3://alpha-omppg/ISP Population/final-data/isp_pop_2024q1.sas7bdat", encoding='latin1')
Mar24= pd.read_parquet("s3://alpha-omppg/ISP Population/final-data/isp_pop_2024q1.parquet")
Jun24= pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q2.parquet")

Mar24.head()

# CONCATENATE ALL THESE DATASES
for i in [Jun23,Sep23,Dec23,Mar24,Jun24]:
    i.columns = i.columns.str.upper()

pop_data = pd.concat([Jun23,Sep23,Dec23,Mar24,Jun24])

pop_data.head()

# KEEP ONLY NEEDED COLUMNS IN THE ORDER PREFERRED
colsToKeep = "EXTRACTDATE DOS TARIFF_PAST TARIFF_EXPIRY_DATE LAST_REVIEW_REASON LAST_REVIEW_RESULT LAST_SUBSEQUENT_DATE ISP_STATUS WHOLE_LIFE".split()

pop_out = pop_data[colsToKeep]

pop_out['EXTRACTDATE'].value_counts(dropna=False).sort_index()
pop_out.head()

# SAVE FINAL DATASET AS EXCEL FILE
pop_out.to_excel("ISP_POP_June2023_June2024.xlsx")

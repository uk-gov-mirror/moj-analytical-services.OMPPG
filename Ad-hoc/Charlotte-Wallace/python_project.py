import pandas as pd
import numpy as np
import s3fs

# IMPORT DATASETS - FIND A BETTER WAY TO LOOP FOR THE IMPORT
Mar21 = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2021q2.sas7bdat", encoding='latin1')
Jun21 = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2021q3.sas7bdat", encoding='latin1')
Sep21 = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2021q4.sas7bdat", encoding='latin1')
Dec21 = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2022q1.sas7bdat", encoding='latin1')

Mar22 = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2022q2.sas7bdat", encoding='latin1')
Jun22 = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2022q3.sas7bdat", encoding='latin1')
Sep22 = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2022q4.sas7bdat", encoding='latin1')
Dec22 = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2023q1.sas7bdat", encoding='latin1')

Mar23= pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2023q2.sas7bdat", encoding='latin1')

# CONCATENATE ALL THESE DATASES
pop_data = pd.concat([Mar21,Jun21,Sep21,Dec21,Mar22,Jun22,Sep22,Dec22,Mar23])
pop_data.dtypes

# CHANGE COLUMNS INTO UPPERCASE
upperColumns =[i.upper() for i in pop_data.columns]
pop_data.columns = upperColumns
pop_data.head()

# KEEP ONLY NEEDED COLUMNS IN THE ORDER PREFERRED
colsToKeep = "EXTRACTDATE DOS TARIFF_PAST TARIFF_EXPIRY_DATE LAST_REVIEW_REASON LAST_REVIEW_RESULT LAST_SUBSEQUENT_DATE ISP_STATUS WHOLE_LIFE".split()
pop_out = pop_data[colsToKeep]
pop_out.head()

# SAVE FINAL DATASET AS EXCEL FILE
pop_out.to_excel("ISP_POP_2021_2022.xlsx")
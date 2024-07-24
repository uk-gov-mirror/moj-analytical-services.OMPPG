import pandas as pd

pd.options.display.max_columns = None
pd.options.display.max_rows = None

pop = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2023q3.sas7bdat", encoding='latin1')
pop.head()

condition = (pop["isp_status"] == "Unreleased IPP") & (pop["OVERTARIFF_YEARS"].notnull()) & (pop["PrisonGender"] =="F")

pop[condition].groupby("OVERTARIFF_YEARS").size()
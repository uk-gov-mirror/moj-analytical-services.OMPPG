import pandas as pd
import numpy as np
import sys # for adding folders to the search path
import duckdb
import s3fs

pd.options.display.max_columns = None
pd.options.display.max_rows = None
#pd.options.display.precision = 2

SFO_wkb = pd.read_excel("s3://alpha-omppg/FOI/2023 04 03 SFO Offences/Compendium 30 Sep 2022 - FOI.xls",sheet_name=None)#
'2013-14', '2014-15', '2015-16', '2016-17', '2017-18', '2018-19', '2019-20', '2020-21', '2021-22'

sfo_1415 =SFO_wkb['2014-15']
sfo_1516 =SFO_wkb['2015-16']
sfo_1617 =SFO_wkb['2016-17']
sfo_1718 =SFO_wkb['2017-18']
sfo_1819 =SFO_wkb['2018-19']
sfo_1920 =SFO_wkb['2019-20']
sfo_2021 =SFO_wkb['2020-21']
sfo_2122 =SFO_wkb['2021-22']

sfo_one = pd.concat([sfo_1415,sfo_1516,sfo_1617,sfo_1718,sfo_1819,sfo_1920,sfo_2021,sfo_2122])
sfo_one['C_year'] = sfo_one['STAGE_12_DOCN_RECEIVED_ACTUAL'].apply(lambda x: x.year)
sfo_one['F_year'] = sfo_one['STAGE_12_DOCN_RECEIVED_ACTUAL'].apply(lambda x: str(x.year) + "/" + str(x.year+1) if x.month > 3 else str(x.year-1) + "/" + str(x.year))

sfo_one.head(500)[["STAGE_12_DOCN_RECEIVED_ACTUAL", "C_year", "F_year"]]
sfo_one.dtypes

# 
sfo_one.shape #4538
sfo_one.loc[sfo_one["STAGE_3_DOCN_RECEIVED_ACTUAL"].notna()].shape
sfo_one.loc[sfo_one["STAGE_3_DOCN_RECEIVED_ACTUAL"].notna()].groupby(["F_year","SFO_OFFENCE_DESCRIPTION"]).count().unstack()
sfo_one.to_excel("sfo.xlsx")

import pandas as pd
import numpy as np

from itables import show

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)


%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

open_recs = pd.read_excel("open_rec_final_2018-2023.xlsx")
open_recs.head()

open_recs['YEAR'] = open_recs['ACTUAL'].dt.year
open_recs['MONTH'] = open_recs['ACTUAL'].dt.month

ipp_cond = open_recs['CUSTODY_TYPE_DESCRIPTION'].isin(['DPP','IPP'])
open_recs['IPP'] = np.where(ipp_cond,"Yes","NO")

open_recs.pivot_table(index = 'YEAR',columns = 'DECISION',aggfunc='size',dropna=False,fill_value=0)

open_recs.pivot_table(index = ['IPP','CUSTODY_TYPE_DESCRIPTION'],columns = 'DECISION',aggfunc='size',dropna=False,fill_value=0)

summary = open_recs.pivot_table(index = 'YEAR',columns = 'DECISION',aggfunc='size',dropna=False,fill_value=0)
type(summary)
show(summary,buttons=["excelHtml5"])

summary_2 = open_recs[open_recs['YEAR']==2023].pivot_table(index = 'MONTH',columns = 'DECISION',aggfunc='size',dropna=False,fill_value=0)


show(summary_2,buttons=["excelHtml5"])

summary_3 = open_recs[open_recs['YEAR']==2023].pivot_table(index =['MONTH','IPP'],columns = 'DECISION',aggfunc='size',dropna=False,fill_value=0)

show(summary_3,buttons=["excelHtml5"])

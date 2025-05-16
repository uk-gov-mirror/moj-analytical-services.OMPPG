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

open_recs = pd.read_excel("open_rec_foi.xlsx")
open_recs.head()

len(open_recs)

open_recs['ACTUAL'].min()
open_recs['GENDER'].value_counts(dropna=False)

open_recs.loc[open_recs['GENDER'] == 0,"GENDER"] = 'M'
open_recs.loc[open_recs['GENDER'] == 'M ( Was F )',"GENDER"] = 'M'
open_recs.loc[open_recs['GENDER'].isna(),"GENDER"] = 'M'

open_recs[open_recs['GENDER']=='F']['Accepted / Rejected'].value_counts(dropna=False)

open_recs[open_recs['GENDER']=='M']['Accepted / Rejected'].value_counts(dropna=False)

vopen_recs.pivot_table(index = 'YEAR',columns = 'DECISION',aggfunc='size',dropna=False,fill_value=0)
type(summary)
show(summary,buttons=["excelHtml5"])

summary_2 = open_recs[open_recs['YEAR']==2023].pivot_table(index = 'MONTH',columns = 'DECISION',aggfunc='size',dropna=False,fill_value=0)

show(summary_2,buttons=["excelHtml5"])



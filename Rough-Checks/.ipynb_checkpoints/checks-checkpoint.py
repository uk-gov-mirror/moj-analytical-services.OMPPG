import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
import duckdb

pd.options.display.max_columns = None
pd.options.display.max_rows = None

ispPop = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2021q2.sas7bdat", encoding='latin1')

ispPop.head()
ispPop.dtypes.sort_index()
ispPop.ExtractDate.head()
ispPop['ExtractDate'].head()

ispPop.last_review_result.value_counts()

releaseReviews = ispPop[ispPop.last_review_result == "Release"]\
        [["PRISON_NUMBER","NOMIS_ID","Surname","last_review_result",\
          "ExtractDate","last_review_date","last_review_reason","isp_status"]].copy()

releaseReviews.isp_status.value_counts()
unreleased = releaseReviews[releaseReviews["isp_status"].str.contains("Unreleased",case=False,na=False)] 
unreleased.head()

import numpy as np
import pandas as pd

def tariff_groups(df):
    
    data = df.copy()
    
    ipp = data['SENTENCESTATUS'] == '(5) IPP'
    tmiss = data['TARIFF_YEARS'].isna()
    t2 = data['TARIFF_YEARS'] < 2
    t2_4 = (
                (data['TARIFF_YEARS'] < 4) | 
                (
                    (data['TARIFF_YEARS'] == 4) & 
                    (data['TARIFF_EXPIRY_DATE'].dt.month == data['DOS'].dt.month) &
                    (data['TARIFF_EXPIRY_DATE'].dt.day == data['DOS'].dt.day)
                )
            )

    t4_6 =  (
                (data['TARIFF_YEARS'] < 6) | 
                (
                    (data['TARIFF_YEARS'] == 6) & 
                    (data['TARIFF_EXPIRY_DATE'].dt.month == data['DOS'].dt.month) &
                    (data['TARIFF_EXPIRY_DATE'].dt.day == data['DOS'].dt.day)
                )
            )

    t6_10 = (
                (data['TARIFF_YEARS'] < 10) | 
                (
                    (data['TARIFF_YEARS'] == 10) & 
                    (data['TARIFF_EXPIRY_DATE'].dt.month == data['DOS'].dt.month) &
                    (data['TARIFF_EXPIRY_DATE'].dt.day == data['DOS'].dt.day)
                )
            )
    data.loc[ipp & tmiss,'TARIFF'] = 'f Tariff not available'
    data.loc[ipp & ~tmiss & t2,'TARIFF'] = 'a Less than 2 years'
    data.loc[ipp & ~(tmiss | t2) & t2_4,'TARIFF'] = 'b 2 years to less than or equal to 4 years'
    data.loc[ipp & ~(tmiss | t2 | t2_4) & t4_6,'TARIFF'] = 'c Greater than 4 years to less than or equal to 6 years'
    data.loc[ipp & ~(tmiss | t2 | t2_4 | t4_6) & t6_10,'TARIFF'] = 'd Greater than 6 years to less than or equal to 10 years'
    data.loc[ipp & ~(tmiss | t2 | t2_4 | t4_6 | t6_10),'TARIFF'] = 'e Greater than 10 years'
    
    life = data['SENTENCESTATUS'] == '(6) Life'
    wl = data['WHOLE_LIFE'].fillna(False)
    t10 = (
                (data['TARIFF_YEARS'] < 10) | 
                (
                    (data['TARIFF_YEARS'] == 10) & 
                    (data['TARIFF_EXPIRY_DATE'].dt.month == data['DOS'].dt.month) &
                    (data['TARIFF_EXPIRY_DATE'].dt.day == data['DOS'].dt.day)
                )
            )

    t20 =  (
                (data['TARIFF_YEARS'] < 20) | 
                (
                    (data['TARIFF_YEARS'] == 20) & 
                    (data['TARIFF_EXPIRY_DATE'].dt.month == data['DOS'].dt.month) &
                    (data['TARIFF_EXPIRY_DATE'].dt.day == data['DOS'].dt.day)
                )
            )

    t20b = data['TARIFF_YEARS'] >= 20

    data.loc[life & wl,'TARIFF'] = 'j Whole life'
    data.loc[life & ~wl & tmiss,'TARIFF'] = 'k Tariff not available'
    data.loc[life & ~(tmiss | wl) & t10,'TARIFF'] = 'g Less than or equal to 10 years'
    data.loc[life & ~(tmiss | wl | t10) & t20,'TARIFF'] = 'h Greater than 10 years to less than or equal to 20 years'
    data.loc[life & ~(tmiss | wl | t10 | t20) & t20b,'TARIFF'] = 'i More than 20 years'
    

    rec = data['SENTENCESTATUS'] == '(7) Recall'
    
    data.loc[rec,'TARIFF'] = 'l Recall'
    
    return data
    
#ispLastRev.loc[ispLastRev['SENTENCESTATUS'] == '(7) Recall','TARIFF_PAST'] = 'Y'

ispLastRev['TARIFF'].value_counts(dropna=False).sort_index()

ispLastRev.groupby(['PRISONGENDER','ISP_STATUS','TARIFF_PAST'])['EXTRACTDATE'].size().reset_index(name='count')

pd.crosstab([ispLastRev['PRISONGENDER'],ispLastRev['ISP_STATUS'],ispLastRev['TARIFF_PAST']],ispLastRev['EXTRACTDATE'],margins=True)

pd.crosstab([ispLastRev['ISP_STATUS'],ispLastRev['TARIFF_PAST'],ispLastRev['TARIFF']],ispLastRev['EXTRACTDATE'])

tb = ispLastRev[(ispLastRev['ISP_STATUS']=='Unreleased IPP') & ~(ispLastRev['OVERTARIFF_YEARS'].isna())].copy()

pd.crosstab(tb['OVERTARIFF_YEARS'],tb['TARIFF'], margins=True)

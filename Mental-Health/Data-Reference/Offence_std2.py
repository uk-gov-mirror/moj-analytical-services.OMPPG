import pandas as pd
import numpy as np
import re
import duckdb

#pd.options.display.max_columns
#pd.options.display.max_rows
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)


home_offence = pd.read_excel("HO_Offences.xls")
index_offence = pd.read_excel("Index_Offence_PPUD.xls")
index_offence['ones'] = 1
home_offence['ones'] = 1

wtr = ["of","a","3","so","act","2000","with","taking","an","which","the","any","or","to","by","under","in","being","and","when","also","than","whilst","from","one","for","at","on","section","s20","etc","as","no","not","do","1","that","be","40","into","out","within","u",
"to","for","a","do","or","etc","in","the","with","any","use","using","under","uk","into","and","by","s","on","an","be","that","at","not","no","so","d","r"]
pat = r'\b(?:{})\b'.format('|'.join([re.escape(x) for x in wtr]))

# remove unwanted words from column
def remove_punct(df,new_col,old_col):
    df[new_col] = df[old_col].str.replace('[(),/.)(-:’‘]', ' ',regex=True) 
    df[new_col] = df[new_col].str.lower()
    df[new_col] = df[new_col].str.replace(pat, ' ',regex=True) # remove chars
    df[new_col] = df[new_col].apply(lambda x: x.split())
    return df

index_offence = remove_punct(index_offence,"Index_Prep","INDEX_OFFENCE_DESCRIPTION")
index_offence.head()

home_offence['Home_Prep'] = home_offence['Detailed_offence'] + " " + \
                            home_offence['Offence group'] + " " + \
                            home_offence['Offence']

home_offence = remove_punct(home_offence,"Home_Prep","Home_Prep")

def remove_dups_in_list(x):
    return list(dict.fromkeys(x))

home_offence['Home_Prep'] = home_offence.apply(lambda x: remove_dups_in_list(x['Home_Prep']),axis=1)
index_offence['Index_Prep'] = index_offence.apply(lambda x: remove_dups_in_list(x['Index_Prep']),axis=1)

home_offence.head()
index_offence.head()

combined_df = pd.merge(index_offence,home_offence)
combined_df.shape

def in_count(col1,col2):
    y = sum([i in [j for j in col2] for i in col1])
    return y

combined_df["Appearance"] = combined_df.apply(lambda x: in_count(x["Index_Prep"],x["Home_Prep"]),axis=1)

combined_df = combined_df[combined_df["Appearance"] > 0]
combined_df.shape


combined_df = duckdb.sql("""
    SELECT *  
    FROM combined_df 
    ORDER BY INDEX_OFFENCE_DESCRIPTION ASC, Appearance DESC """).df()

combined_df.head(100)

combined_df2 = combined_df.drop_duplicates(subset = ['INDEX_OFFENCE_DESCRIPTION'])
combined_df2.shape
index_offence.shape
combined_df2.head(100)

combined_df2.to_excel("output.xlsx")

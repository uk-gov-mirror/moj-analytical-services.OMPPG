import pandas as pd
import numpy as np
import re
import duckdb

#pd.options.display.max_columns
#pd.options.display.max_rows
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)

# Read offence datasets

home_offence = pd.read_excel("HO_Offences2.xls")
index_offence = pd.read_excel("Index_Offence_PPUD2.xls")

index_offence = index_offence.rename(columns = {'OFFENCE_DESCRIPTION':'INDEX_OFFENCE_DESCRIPTION'})
home_offence = home_offence.drop_duplicates(subset=["Class","Offence"])
# Useful for cartesian join - improve this

index_offence['ones'] = 1
home_offence['ones'] = 1

display(index_offence.head(3),home_offence.head(3))

# Words to remove from comparison

wtr = ["of","a","3","so","act","2000","with","taking","an","which","the","any","or","to","by","under","in","being","and","when","also","than","whilst","from","one","for","at","on","section","s20","etc","as","no","not","do","1","that","be","40","into","out","within","u",
"to","for","a","do","or","etc","in","the","with","any","use","using","under","uk","into","and","by","s","on","an","be","that","at","not","no","so","d","r","intent"]

# Pattern to remove exact words in wtr

pat = r'\b(?:{})\b'.format('|'.join([re.escape(x) for x in wtr]))

# remove unwanted words from column

def remove_punct(df,new_col,old_col):
    """ Function to prepare both datasets 
    for matching"""

    df[new_col] = df[old_col].str.replace('[(),/.)(-:’‘]', ' ',regex=True)  # remove unwanted chars
    df[new_col] = df[new_col].str.lower()                                   # lower values for comparison
    df[new_col] = df[new_col].str.replace(pat, ' ',regex=True)              # remove nuisance words
    df[new_col] = df[new_col].apply(lambda x: x.split())                    # Convert cells into lists 4 comparison
    return df

index_offence = remove_punct(index_offence,"Index_Prep","INDEX_OFFENCE_DESCRIPTION")
index_offence.head()

    # Combine some fields in home office file for more matches
home_offence['Home_Prep'] = home_offence['Offence']

home_offence = home_offence[home_offence['Home_Prep'].notnull()]
# home_offence['Home_Prep'] =home_offence['Home_Prep'].fillna('')             #interfering NaNs
home_offence = remove_punct(home_offence,"Home_Prep","Home_Prep")
home_offence.head()

# Remove duplicate words in a cell as they can inflate matches

def remove_dups_in_list(x):
    """Removes duplicated elements 
    of a list"""
    
    return list(dict.fromkeys(x))

home_offence['Home_Prep'] = home_offence.apply(lambda x: remove_dups_in_list(x['Home_Prep']),axis=1)
index_offence['Index_Prep'] = index_offence.apply(lambda x: remove_dups_in_list(x['Index_Prep']),axis=1)

home_offence.head()
index_offence.head()

# Cartesian merge of the two datasets

combined_df = pd.merge(index_offence,home_offence)
#combined_df.shape

# How many key words in PPUD offence are in Home Office offence

def roll_count(col1,col2):
    """ Counts number of words in col1 that appears 
    on the same row in col2"""
    
    start_position = 0
    counter = len(col1)
    
    for i in col1:
        pos = col2.lower().find(i.lower(),start_position)
        if pos > -1:
            start_position = pos + len(i)
        elif pos == -1:
            counter = counter - 1
    return counter

combined_df["Appearance"] = combined_df.apply(lambda x: roll_count(x["Index_Prep"],x["Offence"]),axis=1)

# Subset for cases with matches only - shoudd be 2 minimum?
combined_df = combined_df[combined_df["Appearance"] > 0]
combined_df.shape

# Sort the large dataset - pandas is slow so use sql

combined_df = duckdb.sql("""
    SELECT *  
    FROM combined_df 
    ORDER BY INDEX_OFFENCE_DESCRIPTION ASC, Appearance DESC """).df()

combined_df.head(1000)

# Drop duplicates
combined_df2 = combined_df.drop_duplicates(subset = ['INDEX_OFFENCE_DESCRIPTION'])
combined_df2.shape
index_offence.shape
combined_df2.head(100)

# Save
combined_df2.to_excel("output3.xlsx")





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
Offence_Groups = pd.read_excel("Offence_Groups.xls")

home_offence = home_offence.drop_duplicates(subset=["Class","Offence"])
# Useful for cartesian join - improve this

Offence_Groups['ones'] = 1
home_offence['ones'] = 1

display(Offence_Groups.head(3),home_offence.head(3))

# Words to remove from comparison

wtr = ["of","a","3","so","act","2000","with","taking","an","which","the","any","or","to","by","under","in","being","and","when","also","than","whilst","from","one","for","at","on","section","s20","etc","as","no","not","do","1","that","be","40","into","out","within","u",
"to","for","a","do","or","etc","in","the","with","any","use","using","under","uk","into","and","by","s","on","an","be","that","at","not","no","so","d","r"]

# Pattern to remove exact words in wtr

pat = r'\b(?:{})\b'.format('|'.join([re.escape(x) for x in wtr]))
pat
# remove unwanted words from column

def remove_punct(df,new_col,old_col):
    """ Function to prepare both datasets 
    for matching"""

    df[new_col] = df[old_col].str.replace('[(),/.)(-:’‘]', ' ',regex=True)  # remove unwanted chars
    df[new_col] = df[new_col].str.lower()                                   # lower values for comparison
    df[new_col] = df[new_col].str.replace(pat, ' ',regex=True)              # remove nuisance words
    df[new_col] = df[new_col].apply(lambda x: x.split())                    # Convert cells into lists 4 comparison
    return df

home_offence = remove_punct(home_offence,"Home_Prep","Offence")
home_offence.head()

  
# Remove duplicate words in a cell as they can inflate matches

def remove_dups_in_list(x):
    """Removes duplicated elements 
    of a list"""
    
    return list(dict.fromkeys(x))

home_offence['Home_Prep'] = home_offence.apply(lambda x: remove_dups_in_list(x['Home_Prep']),axis=1)

# Cartesian merge of the two datasets

combined_df = pd.merge(home_offence,Offence_Groups,on="ones")
combined_df.shape
display(Offence_Groups.head(3),home_offence.head(3))

# How many key words in PPUD offence are in Home Office offence

def roll_count(col1,col2):
    """ Counts number of words in col1 that appears 
    on the same row in col2"""
    
    start_position = 0
    counter = len(col1)
    min_pos = 0
    
    for i in col1:
        pos = col2.lower().find(i.lower(),start_position)
        if pos > -1:
            start_position = pos + len(i)
            min_pos = min_pos + 1/(col1.index(i)+1) + 1/(pos + 1)  
        elif pos == -1:
            counter = counter - 1
       
    return counter + min_pos

combined_df["Appearance"] = combined_df.apply(lambda x: roll_count(x["Home_Prep"],x["Main_Offence"]),axis=1)

# Subset for cases with matches only - shoudd be 2 minimum?
combined_df = combined_df[combined_df["Appearance"] > 0]
combined_df.shape

# Sort the large dataset - pandas is slow so use sql

combined_df = duckdb.sql("""
    SELECT *  
    FROM combined_df 
    ORDER BY Offence_x ASC, Appearance DESC """).df()

combined_df.head(100)

# Drop duplicates
combined_df2 = combined_df.drop_duplicates(subset = ['Offence_x'])
combined_df2.shape
combined_df2.head(100)

# Save
combined_df2.to_excel("output5.xlsx")





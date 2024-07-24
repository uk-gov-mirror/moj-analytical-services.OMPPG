import pandas as pd
import numpy as np
import re
import duckdb

#pd.options.display.max_columns
#pd.options.display.max_rows
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

home_offence = pd.read_excel("HO_Offences.xls")
index_offence = pd.read_excel("Index_Offence_PPUD.xls")


# remove brackets and some characters. Also lowercase the values
index_offence['No_Act'] = index_offence['INDEX_OFFENCE_DESCRIPTION'].copy().str.replace(r"\(.*\)"," ",regex=True) 
index_offence['No_Act'] = index_offence['No_Act'].str.replace('[,/.)(-:’‘]', ' ',regex=True) 
index_offence['No_Act'] = index_offence['No_Act'].str.lower() # lower case
# index_offence['No_Act'] = index_offence['No_Act'].str.replace('\d+', '',regex=True) # remove numbers

# word list to remove from comparison
wtr = ["of","a","3","so","act","2000","with","taking","an","which","the","any","or","to","by","under","in","being","and","when","also","than","whilst","from","one","for","at","on","section",
"1956)","s20","etc","as","no","not","do","1","that","be","40","into","out","within","u",
"to","for","a","of","do","or","etc","in","the","with","any","use","using","under","uk","into","and","by","s","on","an","be","that","at","not","no","so","d","r"]

pat = r'\b(?:{})\b'.format('|'.join([re.escape(x) for x in wtr]))

# remove unwanted words from column
index_offence['No_Act'] = index_offence['No_Act'].str.replace(pat, ' ',regex=True) # remove chars
index_offence["Index_list"] = index_offence["No_Act"].copy().apply(lambda x: x.split())
index_offence.head(100)
# pd.Series(index_offence['Index_list']).explode().to_excel("output.xlsx")

# Count how many words in indext_list appears in No_Act
index_offence["Index_list_lower"] = index_offence["INDEX_OFFENCE_DESCRIPTION"].copy().str.lower().apply(lambda x: x.split())
index_offence["Index_list_lower"] = index_offence["INDEX_OFFENCE_DESCRIPTION"].copy().str.lower().apply(lambda x: x.split())

def in_count(col1,col2):
    y = sum([i in [j for j in col2] for i in col1])
    return y

index_offence["apps"] = index_offence.apply(lambda x: in_count(x["Index_list"],x["Index_list_lower"]),axis=1)
index_offence.head(100)
home_offence.head()


recalls_pub = duckdb.sql("""
    SELECT a.*, b.DOS,  
    FROM index_offence AS a LEFT JOIN home_offence AS b 
    ON  
        (a.PRISON_NUMBER = b.PRISON_NUMBER  OR
         a.FILE_REFERENCE = b.FILE_REFERENCE OR
         a.NOMS_ID = b.NOMS_ID
        ) AND 
        a.LICENCE_REVOKE_DATE = b.LICENCE_REVOKE_DATE""").df()

recalls_pub.shape



home_offence = pd.read_excel("HO_Offences.xls")
index_offence = pd.read_excel("Index_Offence_PPUD.xls")
index_offence['ones'] = 1
home_sub = pd.DataFrame(home_offence['Detailed_offence'])
home_sub['ones'] = 1

index_offence.head()
home_sub.head()

combined_df = pd.merge(index_offence,home_sub)
combined_df.shape
combined_df.head()

# remove brackets and some characters. Also lowercase the values
combined_df['Index_Prep'] = combined_df['INDEX_OFFENCE_DESCRIPTION'].copy().str.replace(r"\(.*\)"," ",regex=True) 
combined_df['Index_Prep'] = combined_df['Index_Prep'].str.replace('[,/.)(-:’‘]', ' ',regex=True) 
combined_df['Index_Prep'] = combined_df['Index_Prep'].str.lower() # lower case
# combined_df['No_Act'] = combined_df['No_Act'].str.replace('\d+', '',regex=True) # remove numbers

# word list to remove from comparison
wtr = ["of","a","3","so","act","2000","with","taking","an","which","the","any","or","to","by","under","in","being","and","when","also","than","whilst","from","one","for","at","on","section",
"1956)","s20","etc","as","no","not","do","1","that","be","40","into","out","within","u",
"to","for","a","of","do","or","etc","in","the","with","any","use","using","under","uk","into","and","by","s","on","an","be","that","at","not","no","so","d","r"]

pat = r'\b(?:{})\b'.format('|'.join([re.escape(x) for x in wtr]))

# remove unwanted words from column
combined_df['Index_Prep'] = combined_df['Index_Prep'].str.replace(pat, ' ',regex=True) # remove chars
combined_df['Index_Prep'] = combined_df['Index_Prep'].copy().apply(lambda x: x.split())

combined_df['Home_Prep'] = combined_df['Detailed_offence'].str.lower().apply(lambda x: x.split())
combined_df.head(100)

def in_count(col1,col2):
    y = sum([i in [j for j in col2] for i in col1])
    return y

combined_df["Appearance"] = combined_df.apply(lambda x: in_count(x["Index_Prep"],x["Home_Prep"]),axis=1)
combined_df.head(100)

combined.df2 = combi
combined_df.sort_values(by=["INDEX_OFFENCE_DESCRIPTION","Appearance"],
                       ascending= [True,False])
combined_df.head(100)

combined_df.shape

""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.
By Eric Nyame, 17/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


import pandas as pd

# Example DataFrame creation (replace with your actual DataFrame)
data = {
    'sex': ['Male', 'Male', 'Male', 'Male', 'Male', 'Male', 'Male', 'Male', 'Male', 'Male', 
            'Male', 'Male', 'Female', 'Female', 'Female', 'Female', 'Female', 'Female', 'Female', 
            'Female', 'Female', 'Female', 'Female','Female'],
    'age_group': ['Adults (21 and over)', 
                  'Adults (21 and over)', 'Adults (21 and over)', 'Adults (21 and over)', 
                  '18 to 20 year olds', '18 to 20 year olds', '18 to 20 year olds', '18 to 20 year olds', 
                  '15 to 17 year olds', '15 to 17 year olds', '15 to 17 year olds', '15 to 17 year olds', 
                  'Adults (21 and over)', 
                  'Adults (21 and over)', 'Adults (21 and over)', 'Adults (21 and over)', 
                  '18 to 20 year olds', '18 to 20 year olds', '18 to 20 year olds', '18 to 20 year olds', 
                  '15 to 17 year olds', '15 to 17 year olds', '15 to 17 year olds', '15 to 17 year olds'],
    'custody_type': ['Remand', 'Sentenced', 'Non criminal prisoners', 
                     'Remand', 'Sentenced', 'Non criminal prisoners', 
                     'Remand', 'Sentenced', 'Non criminal prisoners', 
                     'Remand', 'Sentenced', 'Non criminal prisoners', 
                     'Remand', 'Sentenced', 'Non criminal prisoners', 
                     'Remand', 'Sentenced', 'Non criminal prisoners', 
                     'Remand', 'Sentenced', 'Non criminal prisoners', 
                     'Remand', 'Sentenced', 'Non criminal prisoners'],
    'date': ['31/03/2023'] * 24,
    'values': [81057, 13870, 66547, 640, 77556, 12484, 64455, 617, 3166, 1234, 1909, 23, 
               335, 152, 183, 0, 3315, 721, 2572, 22, 3252, 692, 2538, 22]
}
len(data['sex'])
df = pd.DataFrame(data)
df


# Function to calculate and append summaries
def add_summaries(df):
    # Sum for all ages and all custody types for each sex
    total_summary = df.groupby('sex')['values'].sum().reset_index()
    total_summary['age_group'] = 'All ages'
    total_summary['custody_type'] = 'All custody types'
    
    # Sum for all ages for each custody type and each sex
    custody_summary = df.groupby(['sex', 'custody_type'])['values'].sum().reset_index()
    custody_summary['age_group'] = 'All ages'
    
    # Sum for all custody types for each age group and each sex
    age_summary = df.groupby(['sex', 'age_group'])['values'].sum().reset_index()
    age_summary['custody_type'] = 'All custody types'
    
    # Combine all summaries
    combined_summary = pd.concat([total_summary, custody_summary, age_summary], ignore_index=True)
    
    # Add combined 'Male and female' row
    combined_summary_all = combined_summary.groupby(['age_group', 'custody_type'])['values'].sum().reset_index()
    combined_summary_all['sex'] = 'Male and female'
    
    # Final concatenated DataFrame
    final_df = pd.concat([combined_summary_all, combined_summary], ignore_index=True)
    
    return final_df

# Apply the function to add summaries
final_df = add_summaries(df)

final_df.head()
# Rename and reorder columns
final_df = final_df[['sex', 'age_group', 'custody_type', 'values']]
final_df.columns = ['Sex', 'Age group', 'Custody type group', '31 Mar 2023']

final_df
# Format the '31 Mar 2023' column to have thousand separators
final_df['31 Mar 2023'] = final_df['31 Mar 2023'].apply(lambda x: f"{x:,}")

# Sorting the DataFrame for the desired output structure
final_df = final_df.sort_values(by=['Sex', 'Age group', 'Custody type group']).reset_index(drop=True)

# Displaying the final DataFrame
print(final_df.to_string(index=False))

g1_t = pd.DataFrame({'sex':['Male and female'],'age_group':['All ages'],'custody_type': ['All custody types'],'values':[np.sum(df['values'])]})
g1 = df.groupby('custody_type')['values'].sum().reset_index()
g1['sex'] = 'Male and female'
g1['age_group'] = 'All ages'
g1_t
g1

df1 = pd.concat([g1_t,g1],axis=0,ignore_index=True)

g2_t = pd.DataFrame({'sex':['Male and female'],'age_group':['Adults (21 and over)'],'custody_type': ['All custody types'],'values':[np.sum(df[df['age_group']=='Adults (21 and over)']['values'])]})
g2 = df[df['age_group']=='Adults (21 and over)'].groupby('custody_type')['values'].sum().reset_index()
g2['sex'] = 'Male and female'
g2['age_group'] = 'Adults (21 and over)'
g2_t
g2
df2 = pd.concat([g2_t,g2],axis=0,ignore_index=True)







import pandas as pd
import numpy as np

# Assuming df is your original DataFrame

# Create individual summaries
g1_t = pd.DataFrame({
    'sex': ['Male and female'],
    'age_group': ['All ages'],
    'custody_type': ['All custody types'],
    'values': [np.sum(df['values'])]
})
g1 = df.groupby('custody_type')['values'].sum().reset_index()
g1['sex'] = 'Male and female'
g1['age_group'] = 'All ages'

df1 = pd.concat([g1_t, g1], axis=0, ignore_index=True)

g2_t = pd.DataFrame({
    'sex': ['Male and female'],
    'age_group': ['Adults (21 and over)'],
    'custody_type': ['All custody types'],
    'values': [np.sum(df[df['age_group'] == 'Adults (21 and over)']['values'])]
})
g2 = df[df['age_group'] == 'Adults (21 and over)'].groupby('custody_type')['values'].sum().reset_index()
g2['sex'] = 'Male and female'
g2['age_group'] = 'Adults (21 and over)'

df2 = pd.concat([g2_t, g2], axis=0, ignore_index=True)

g3_t = pd.DataFrame({
    'sex': ['Male and female'],
    'age_group': ['18 to 20 year olds'],
    'custody_type': ['All custody types'],
    'values': [np.sum(df[df['age_group'] == '18 to 20 year olds']['values'])]
})
g3 = df[df['age_group'] == '18 to 20 year olds'].groupby('custody_type')['values'].sum().reset_index()
g3['sex'] = 'Male and female'
g3['age_group'] = '18 to 20 year olds'

df3 = pd.concat([g3_t, g3], axis=0, ignore_index=True)

g4_t = pd.DataFrame({
    'sex': ['Male and female'],
    'age_group': ['15 to 17 year olds'],
    'custody_type': ['All custody types'],
    'values': [np.sum(df[df['age_group'] == '15 to 17 year olds']['values'])]
})
g4 = df[df['age_group'] == '15 to 17 year olds'].groupby('custody_type')['values'].sum().reset_index()
g4['sex'] = 'Male and female'
g4['age_group'] = '15 to 17 year olds'

df4 = pd.concat([g4_t, g4], axis=0, ignore_index=True)

# Concatenate all the DataFrames
result_mf = pd.concat([df1, df2, df3, df4], axis=0, ignore_index=True)

# Repeat the same process for 'Male' and 'Female'
sexes = ['Male', 'Female']
final_df = result_mf.copy()

for sex in sexes:
    g1_t = pd.DataFrame({
        'sex': [sex],
        'age_group': ['All ages'],
        'custody_type': ['All custody types'],
        'values': [np.sum(df[df['sex'] == sex]['values'])]
    })
    g1 = df[df['sex'] == sex].groupby('custody_type')['values'].sum().reset_index()
    g1['sex'] = sex
    g1['age_group'] = 'All ages'

    df1 = pd.concat([g1_t, g1], axis=0, ignore_index=True)

    g2_t = pd.DataFrame({
        'sex': [sex],
        'age_group': ['Adults (21 and over)'],
        'custody_type': ['All custody types'],
        'values': [np.sum(df[(df['sex'] == sex) & (df['age_group'] == 'Adults (21 and over)')]['values'])]
    })
    g2 = df[(df['sex'] == sex) & (df['age_group'] == 'Adults (21 and over)')].groupby('custody_type')['values'].sum().reset_index()
    g2['sex'] = sex
    g2['age_group'] = 'Adults (21 and over)'

    df2 = pd.concat([g2_t, g2], axis=0, ignore_index=True)

    g3_t = pd.DataFrame({
        'sex': [sex],
        'age_group': ['18 to 20 year olds'],
        'custody_type': ['All custody types'],
        'values': [np.sum(df[(df['sex'] == sex) & (df['age_group'] == '18 to 20 year olds')]['values'])]
    })
    g3 = df[(df['sex'] == sex) & (df['age_group'] == '18 to 20 year olds')].groupby('custody_type')['values'].sum().reset_index()
    g3['sex'] = sex
    g3['age_group'] = '18 to 20 year olds'

    df3 = pd.concat([g3_t, g3], axis=0, ignore_index=True)

    g4_t = pd.DataFrame({
        'sex': [sex],
        'age_group': ['15 to 17 year olds'],
        'custody_type': ['All custody types'],
        'values': [np.sum(df[(df['sex'] == sex) & (df['age_group'] == '15 to 17 year olds')]['values'])]
    })
    g4 = df[(df['sex'] == sex) & (df['age_group'] == '15 to 17 year olds')].groupby('custody_type')['values'].sum().reset_index()
    g4['sex'] = sex
    g4['age_group'] = '15 to 17 year olds'

    df4 = pd.concat([g4_t, g4], axis=0, ignore_index=True)

    result = pd.concat([df1, df2, df3, df4], axis=0, ignore_index=True)
    final_df = pd.concat([final_df, result], axis=0, ignore_index=True)

# Rename and reorder columns
final_df.columns = ['Sex', 'Age group', 'Custody type group', '31 Mar 2023']

# Format the '31 Mar 2023' column to have thousand separators
final_df['31 Mar 2023'] = final_df['31 Mar 2023'].apply(lambda x: f"{x:,}")

# Displaying the final DataFrame
print(final_df.to_string(index=False))




#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888

# Define the unique values
sex_vals = ['Male and female'] + list(df['sex'].unique())
age_vals = ['All ages'] + list(df['age_group'].unique())
custype_vals = ['All custody types'] + list(df['custody_type'].unique())

# Function to calculate and append summaries
def calculate_summaries(df, sex_vals, age_vals, custype_vals):
    summary_list = []
    
    for sex in sex_vals:
        for age in age_vals:
            if age == 'All ages':
                temp_df = df if sex == 'Male and female' else df[df['sex'] == sex]
            else:
                temp_df = df[df['age_group'] == age] if sex == 'Male and female' else df[(df['sex'] == sex) & (df['age_group'] == age)]
            
            total_value = np.sum(temp_df['values'])
            summary_list.append({
                'Sex': sex,
                'Age group': age,
                'Custody type group': 'All custody types',
                '31 Mar 2023': total_value
            })
            
            for custype in custype_vals[1:]:  # Skip 'All custody types' in this loop
                custype_value = np.sum(temp_df[temp_df['custody_type'] == custype]['values'])
                summary_list.append({
                    'Sex': sex,
                    'Age group': age,
                    'Custody type group': custype,
                    '31 Mar 2023': custype_value
                })
    
    return pd.DataFrame(summary_list)

# Calculate summaries
final_df = calculate_summaries(df, sex_vals, age_vals, custype_vals)

# Format the '31 Mar 2023' column to have thousand separators
final_df['31 Mar 2023'] = final_df['31 Mar 2023'].apply(lambda x: f"{x:,}")

# Displaying the final DataFrame
print(final_df.to_string(index=False))

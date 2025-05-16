""" 
GOAL: GET DATA ON SEX DISTRIBUTION FOR MAPPA PUBLICATION.
By Eric Nyame, 31/07/2024
"""

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

# Folder containing the Excel files

returns_folder = 'returns'
list_of_file_names = os.listdir(returns_folder)
list_of_file_names = [name for name in list_of_file_names if name.endswith('.xlsx')]
list_of_file_names.remove('NSD.xlsx') # exclude NSD for now. Will work on it separately
len(list_of_file_names) # should be 42 for now without NSD

# IMPORT DATA FROM EACH FILE IN RETURNS FOLDER

list_of_data_frames = []

# Loop through the files and read the necessary data
for file_name in list_of_file_names:
    file_path = os.path.join(returns_folder, file_name)
    
    # Read the value in cell C2
    area_id = pd.read_excel(file_path, sheet_name='Data entry', usecols='A', nrows=2).iloc[0, 0]
    area_name = pd.read_excel(file_path, sheet_name='Data entry', usecols='C', nrows=2).iloc[0, 0]
    
    # Read the entire sheet to locate the row containing '18' in column B
    sheet_df = pd.read_excel(file_path, sheet_name='Data entry')
    
    # Find the first row where column B contains '18'
    start_row = sheet_df[sheet_df.iloc[:, 1]=='Female'].index[0]
    
    # Define the range to extract data: 8 rows down and 6 columns to the right from the start_row
    data_range = sheet_df.iloc[start_row:start_row+5, 1:8].fillna(value=0)
    
    # Rename the columns appropriately
    data_range.columns = ['SEX', 'CAT1L2', 'CAT1L3', 'CAT2L2', 'CAT2L3', 'CAT3L2', 'CAT3L3']
    
    # Add the 'AREA' column to the dataframe
    data_range['AREA_ID'] = area_id
    data_range['AREA'] = area_name
    # Append to the data list
    list_of_data_frames.append(data_range)

    # Append NSD
file_path = os.path.join(returns_folder, 'NSD.xlsx')
sheet_df = pd.read_excel(file_path, sheet_name='Data entry')
start_row = sheet_df[sheet_df.iloc[:, 1]=='Female'].index[0]
data_range = sheet_df.iloc[start_row:start_row+5, 1:4].fillna(value=0)
data_range.columns = ['SEX', 'CAT4L2', 'CAT4L3']
area_id = pd.read_excel(file_path, sheet_name='Data entry', usecols='A', nrows=2).iloc[0, 0]
area_name = pd.read_excel(file_path, sheet_name='Data entry', usecols='C', nrows=2).iloc[0, 0]
data_range['AREA_ID'] = area_id
data_range['AREA'] = area_name

list_of_data_frames.append(data_range)

# Concatenate all the dataframes into one
sex_data = pd.concat(list_of_data_frames, ignore_index=True).fillna(value=0)
sex_data = sex_data[['AREA_ID','AREA'] + [col for col in sex_data.columns if col not in ['AREA_ID','AREA']]]

# Some corrections in free text row
# sex_data.loc[[55,59]]
#sex_data.iloc[55,3] = sex_data.iloc[55,3] + 1
#sex_data.iloc[59,3] = 0

sex_data[sex_data.columns[3:]] = sex_data[sex_data.columns[3:]].astype('int64')

sex_data['TOTAL'] = sex_data[sex_data.columns[3:]].sum(axis=1)

len(sex_data) # should be 215
sex_data['AREA'].value_counts() # 5 each

sex_data.head()

# Bring in Level 2 + Level 3

sex_correction = sex_data.groupby(['AREA_ID','AREA'])['TOTAL'].sum().reset_index(name='TOTAL')

sex_correction = pd.merge(sex_correction, mappa_data[['AREA_ID','LEVEL2TOTT1','LEVEL3TOTT1']], on ='AREA_ID')

sex_correction['L2_L3_TOTAL'] = sex_correction['LEVEL2TOTT1'] +  sex_correction['LEVEL3TOTT1']

sex_correction =  sex_correction.drop(['LEVEL2TOTT1','LEVEL3TOTT1'],axis=1)

sex_correction['DIFFERENCE'] = (sex_correction['TOTAL']  - sex_correction['L2_L3_TOTAL'])
sex_correction['DIFFERENCE'] = sex_correction['DIFFERENCE'].abs()

sex_correction['CHECK']='Yes'
sex_correction.loc[sex_correction['DIFFERENCE']==0,'CHECK'] = ''

sex_correction

# Write to Excel if any to check
with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='replace') as writer:
    sex_correction.to_excel(writer,sheet_name='Sex',index=False)
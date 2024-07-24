
import numpy as np
import pandas as pd

def prepareMatch(df):
    """ 
    This function prepares PPUD data for matching with 
    Nomis data.
    Author: Eric Nyame, based on previous work by Phil Hall using SAS
    """
    data = df.copy()
    # A Capture prison number correctly
    
        # remove all white spaces in prison number
        
    data['PN_TRIM'] = data['PRISON_NUMBER'].str.replace('\s+',"",regex = True)
    data['PN_LENGTH'] = data['PN_TRIM'].str.len()
    
        # select first 6 characters of prison number
        
    data['PN_START'] = data['PN_TRIM'].str[:6] 
    
        # select last 6 characters of prison number if the prison number is at least 6, else empty cell
        
    data['PN_END'] = np.where(pd.notna(data['PN_LENGTH']) & (data['PN_LENGTH'] >= 6),
                              data['PN_TRIM'].str[-6:],"") 
    
    # data['PN_END'] = data['PN_END'].astype('string')
    
    # B Capture nomis id correctly
    
        # remove all white spaces in nomis id
        
    data['NOMS_TRIM'] = data['NOMS_ID'].str.replace('\s+',"",regex = True)
    data['NOMS_LENGTH'] = data['NOMS_TRIM'].str.len()
    
         # select first 7 characters of nomis id
        
    data['NOMS_START'] = data['NOMS_TRIM'].str[:7] 
    
        # select last 7 characters of nomis id if the nomis id is at least 7, else empty cell
        
    data['NOMS_END'] = np.where(pd.notna(data['NOMS_LENGTH']) & (data['NOMS_LENGTH'] >= 7),data['NOMS_TRIM'].str[-7:],"") 
    
    # data['NOMS_END'] = data['NOMS_END'].astype('string')
    
    # Remove anything after a bracket, AKA, formerly or Duplicate*
    
    pattern = r'(?i)\(| AKA| DUPLICATE| FORMERLY'
    data['FAMILY_NAME'] = data['FAMILY_NAME'].str.split(pattern).str[0].str.upper().str.strip()
    
    # data['FAMILY_NAME'] = data['FAMILY_NAME'].astype('string')
    
        # Initials
    data['INIT'] = data['FIRST_NAMES'].str[0].str.upper()
    
    # C We are not matching based on names
    return data
import pandas as pd

#---------------- Calculate the number of full months between two dates

def month_diff(d1, d2):
    # Initial month difference between two dates
    diff = (d2.year - d1.year) * 12 + d2.month - d1.month
    
    # Decrease the diff by one if the day in d2 is less than the day in d1
    if d2.day < d1.day:
        diff -= 1
    
    return diff

#---------------- Calculate the number of full years between two dates

def year_diff(d1, d2):
    # Initial year difference between two dates
    diff = d2.year - d1.year
    
    # Decrease the diff by one if the month-day combination in d2 is before that in d1
    if (d2.month, d2.day) < (d1.month, d1.day):
        diff -= 1
    
    return diff
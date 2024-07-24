# 1 POPULATION
1. You will get population data from the MHCS team
2. But run, <u> on the same date</u>, your own reports for **population**, **all movements after 31 December** and **Offences** (details below).
3. For population, run the report: 
> MHU -> Detention Authority -> "z DAs pub"

Change the date parameters and save on AWS as "population_reconstruct_{31DecYYYY}". The rationale of this report is to capture all currently live cases that had hospital orders by 31 December or all currently non-active cases that became non-active after 31 December. It tries to determine active cases on 31 December of a particular year.

4. For all movements after 31 December, run the report:
> MHU -> Movements -> "Z All Movements - Raw"

Change the date parameters and save on AWS as "moves_Jan{YYYY}\_{Extract Date}". The rationale of this report is to capture all movements in and out of hospital after 31 December to the date of running the above two reports. We will use these two reports to reconstruct the active population on 31 December. 

5. For offences, run the report:
> MHU -> Court Appearance -> "Z offence pub"

Change the date parameters and save on AWS as "offences\_{31DecYYYY}". The rationale of this report is to capture all offences associated with the active population on 31 December. 

7. Follow the code, in the relevant year's code folder, "1. Reconstruct pop".

8. **Replace “–” with “-“ throughout** the excel datasets.

# 2 ADMISSIONS AND RECALLS
MHU -> Movement - > Admissions – Last Month
	Move type separately changed from ‘recall’ to admissions
Date parameters cover a year
Remove existing parameters to capture everything and sort yourself.
1. Check Table 6&7 matches last year’s
2. Rename admissions sheet to ‘Admissions’, and recall sheet to ‘Recalls’
3. Remove all filters in (2)
4. Save file as “Admissions & Recalls.xls”
5. Check TO_ESTABLISHMENT_DESCRIPTION with hospital type in reference file and make changes

Offence
MHU -> Court Appearnace - > Offences on Live DAs
	Remove existing parameters to capture everything and sort yourself.
2. Check offences under OFFENCE_DESCRIPTION that are not in the reference offence file (sheet “Offences_New”) and make changes in both files.
3. You can get rid of the other sheets?
6. Eliminate bottom blank entries


# 3 DISPOSALS AND DISCHARGES
MHU -> Movement - > Disposals
	Don’t include discharges report as disposals cover discharges
Remove existing parameters to capture everything and sort yourself.
1. Copy de-duplicated file and name the copy as ‘DispDisch’
2. Check move type description with reference file and make changes


Code
Change previous year to current year (e.g., 2017 to 2018) in the file paths and macros.
Check columns and run check program before exporting
Export Manually
Don’t close the SAS program yet until you have populated tables

Tables
Save and use copies of input files as xls
Make sure the imports have picked up all new fields
Get rid of bizzare columns in impopicked up 
Modify all import sources before import to recalibrate
Inspect imported data manually
Run TablesYYYY

You may have to hide columns in populated input file
Table 2
If gender is missing, correct manually

It’s vlookup so don’t worry about new paste matching in category names with the old paste
Some fields may have been entered manually – may need to reinstate their vlookups

Table 4
Check cases should come under ‘other’

Table 5
Replace the zero at the end of “Transferred from Scotland, Northern Ireland etc0” with a dot

Table 7
May have to manually correct check cases


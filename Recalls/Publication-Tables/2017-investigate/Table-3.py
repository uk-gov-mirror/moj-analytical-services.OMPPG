""" 
GOAL: PRODUCE TABLE 3 - CONTINUATION FROM TABLE 2 CODE
By Eric Nyame, 17/04/2024
"""

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Calculate summaries for the combined DataFrame
recalls.pivot_table(index=['SUP_BODY','NPS_CRC_NAME'],columns='QUARTER',aggfunc='size').reset_index()[['SUP_BODY','NPS_CRC_NAME'] + quarters]


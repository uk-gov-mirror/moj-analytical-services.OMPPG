import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

%config InlineBackend.figure_format = 'svg'

#start_year = 2015

# SOPOS data up to 2023/24
so_no_ft = pd.read_excel("Charts_Data.xlsx",sheet_name='SOPOs')

# insert this year's data. There should be a better way to automate this
so_no_ft.loc[18] = ['2024/25',7221, 132,10]

so_no_ft = so_no_ft.tail(11) # keep the last 11 

# Make the Year column a categorical column
so_no_ft['Year'] = pd.Categorical(so_no_ft['Year'], categories = so_no_ft['Year'], ordered=True)

# so_no_ft

# Run everything below in one
# Define figure and axes
fig, axes = plt.subplots(3, 1, figsize=(10,8), 
                         sharex=True, 
                         gridspec_kw={'height_ratios': [2, 1, 1],'hspace': 0.25})

# Plot each line on a separate axis
line1, = axes[0].plot(so_no_ft['Year'], so_no_ft['SOPO_SHPO'], label="SOPOs/SHPOs", marker='^', color='black', linewidth=1,zorder=2)
line2, = axes[1].plot(so_no_ft['Year'], so_no_ft['Nos'], label="Notification Orders", marker='o', color='purple', linewidth=1,zorder=2)
line3, = axes[2].plot(so_no_ft['Year'], so_no_ft['FTOs_SHPOs_FTR'], label="FTO/FTR within SHPO or SRO", marker='D', color='#00B0F0', linewidth=1,zorder=2)

# Set limits of each axis
axes[0].set_ylim(0,8000)
axes[1].set_ylim(0,150)
axes[2].set_ylim(0,24)

# Hide top, right and bottom spines for first two subplots
for ax in axes[:2]:
    # Hide the top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Set the x-axis spine to a faint color
    ax.spines['bottom'].set_color('lightgray')
    
    # Remove x-axis ticks and labels
    ax.tick_params(axis='x', bottom=False, labelbottom=False)

# Hide top and right spines for last subplot
axes[2].spines['top'].set_visible(False)
axes[2].spines['right'].set_visible(False)

# Add shared x-axis ticks and labels
axes[2].set_xticks(range(len(so_no_ft['Year'])))
axes[2].set_xticklabels(so_no_ft['Year'], rotation=25)
axes[2].set_xlim(-0.5, len(so_no_ft['Year']) - 0.5)

# Set y ticks for each subplot
axes[0].set_yticks(np.arange(0,8000,1000))
axes[0].set_yticklabels(np.arange(0,8000,1000))

axes[1].set_yticks(np.arange(0,160,50))
axes[1].set_yticklabels(np.arange(0,160,50))

axes[2].set_yticks(np.arange(0,25,8))
axes[2].set_yticklabels(np.arange(0,25,8))

# Add vertical reference line across the entire figure
highlight_year = '2015/16'
highlight_index = so_no_ft['Year'].tolist().index(highlight_year)

axes[0].axvline(x=highlight_index, color='lightgray', ymin=-1.2, ymax=1,linestyle='--', linewidth=1, zorder=1, clip_on=False)
axes[1].axvline(x=highlight_index, color='lightgray', ymin=-1.2, ymax=1,linestyle='--', linewidth=1, zorder=1, clip_on=False)
axes[2].axvline(x=highlight_index, color='lightgray', ymin=0, ymax=1,linestyle='--', linewidth=1, zorder=1, clip_on=False)

# Add annotations
axes[0].annotate("SHPOs replaced SOPOs\nSOPOs in 2015/16",               # text
                 xy=(highlight_index, 2000),                             # arrow point
                 xytext=(highlight_index + 0.5, 2500),                   # text location
                 arrowprops=dict(arrowstyle="->", color='gray'), 
                 fontsize=8)

# Shared legend on top
fig.legend([line1, line2, line3], 
           ['SOPOs/SHPOs', 'Notification Orders', 'FTO/FTR within SHPO or SRO'],
           bbox_to_anchor=(0.7, 0.7), # precise location of legend
           loc='upper center', ncol=1, fontsize=10, frameon=False)

#plt.savefig("sopo_no_ft.svg",bbox_inches='tight',pad_inches=0)    
plt.show()

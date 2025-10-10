import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

%config InlineBackend.figure_format = 'svg'

start_year = 2015

# Sample data
cats = pd.read_excel("Charts_Data.xlsx",sheet_name='Categories',skiprows=3)

cats = cats.loc[cats['Year'] >= start_year].reset_index()

cats = cats.drop(columns='index')

cats.loc[10] = [2025,73047,23237,557,209,97050]

# Define color palette
# colors = ["#00B0F0", "lightsteelblue", "#0070C0", "darkviolet"]
colors = ["steelblue", "#00B0F0", "#0070C0","darkorange"]
# Create a figure and axis object
fig, ax = plt.subplots(figsize=(10, 6))

# Define bar width and offset
bar_width = 0.3
#offset = 0.15  # Adjusted for overlap
x = np.arange(len(cats["Year"]))

# Plot the total22
ax.bar(x, cats["Total"], width=bar_width, label="All",color='lightgrey', alpha=0.9,zorder=1)

# Only plot Cat1, Cat2, and Cat3 for years up to 2022
ax.bar(x[:9] - bar_width/2, cats.loc[range(0,9), "Cat1"], width=bar_width, label="Cat1", color=colors[0], zorder=2)
ax.bar(x[:9], cats.loc[range(0,9), "Cat2"], width=bar_width, label="Cat2", color=colors[1], zorder=3)
ax.bar(x[:9] + bar_width/2, cats.loc[range(0,9), "Cat3"], width=bar_width, label="Cat3",color='darkblue', zorder=4)

# Plot all four categories for 2023 with adjusted offsets for four bars
ax.bar(x[9:] - 0.75 * bar_width, cats.loc[9:10, "Cat1"], width=bar_width, label="", color=colors[0], zorder=2)
ax.bar(x[9:] - 0.25 * bar_width, cats.loc[9:10, "Cat2"], width=bar_width, label="", color=colors[1], zorder=3)
ax.bar(x[9:] + 0.25 * bar_width, cats.loc[9:10, "Cat3"], width=bar_width, label="", color='darkblue',zorder=4)
ax.bar(x[9:] + 0.75 * bar_width, cats.loc[9:10, "Cat4"], width=bar_width, label="Cat4",color=colors[3], zorder=5)

# Remove x and y labels for a cleaner look
ax.set_xlabel("")
ax.set_ylabel("")

# Set x-ticks with bold font and format y-axis as comma-separated
ax.set_xticks(x)
ax.tick_params(axis='x', which='both', pad=3,color='white')
ax.set_xticklabels(cats["Year"],fontweight = 'bold')
ax.set_yticks(np.arange(0,110000,10000))
ax.set_yticklabels(np.arange(0,110000,10000),fontweight = 'bold')
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x):,}"))

# Customizing the legend
ax.legend(bbox_to_anchor=(0.025, 1), loc="upper left", fontsize=10.5, frameon=False,ncol=3)

# Hide all axes lines for a minimalistic look
for spine in ax.spines.values():
    spine.set_visible(False)

# Add faint reference lines behind bars for context
for y_value in range(10000, 100001, 10000):
    ax.axhline(y=y_value, color="lightgray", linestyle="--", linewidth=1, alpha=0.3, zorder=1)

plt.savefig("cats.svg",bbox_inches='tight',pad_inches=0)    
# Display the plot
plt.show()


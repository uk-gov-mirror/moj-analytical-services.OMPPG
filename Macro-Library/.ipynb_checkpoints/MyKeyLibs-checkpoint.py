# Import libraries

import pandas as pd
import numpy as np
import sys # for adding folders to the search path
import duckdb
import s3fs

# Set view options
pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.options.display.precision = 2
# pd.set_option('max_colwidth',None)


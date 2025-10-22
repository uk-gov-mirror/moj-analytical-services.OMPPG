import pandas as pd
import numpy as np
from typing import Dict, List, Optional

def find_offending_dates(
    df: pd.DataFrame,
    cols: List[str],
    *,
    dayfirst: bool = True,
    formats: Optional[Dict[str, str]] = None,   # per-column explicit formats, e.g. {"LATEST_RELEASE_DATE": "%Y-%m-%d"}
    empty_tokens: Optional[set] = None
):
    """
    Returns:
      parsed:     dict of parsed Series per column (datetime64[ns])
      bad_masks:  dict of boolean masks per column for rows that failed parsing
      bad_counts: dict of Series (value_counts) of offending raw strings per column
    """
    if empty_tokens is None:
        empty_tokens = {'', 'na', 'n/a', 'null', 'none', 'unknown', 'tbc', 'n/k'}
    if formats is None:
        formats = {}

    parsed, bad_masks, bad_counts = {}, {}, {}

    for col in cols:
        # 1) normalise text
        s = (df[col]
             .astype('string')        # handles pd.NA cleanly
             .str.strip()
             .str.replace(r'\s+', ' ', regex=True)
        )
        s = s.mask(s.str.lower().isin(empty_tokens), pd.NA)

        # 2) parse: prefer explicit format if provided for this column
        fmt = formats.get(col)
        if fmt:
            out = pd.to_datetime(s, format=fmt, errors='coerce')
        else:
            # start permissive; if you know typical formats, do multi-pass instead
            out = pd.to_datetime(s, errors='coerce', dayfirst=dayfirst)

        # 3) offenders = non-missing originals that became NaT
        bad_mask = s.notna() & out.isna()
        bad_date_data = df[bad_mask]
        bad_date_data = bad_date_data[[col] + [c for c in df.columns if c != col]]

    return bad_date_data

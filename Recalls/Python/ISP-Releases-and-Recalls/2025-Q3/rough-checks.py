import re

# 1) Normalise the raw strings a bit

df = disch20132015.copy()
s = (df['DATEDIS']
       .astype('string')
       .str.strip()
       .str.replace(r'\s+', ' ', regex=True))
"""
# s.head()
"""
# 2) Define patterns to recognise (order matters: most specific first)
PATTERNS = [
    # ISO-like
    (r'^\d{4}-\d{2}-\d{2}$',                          'yyyy-mm-dd'),
    (r'^\d{4}/\d{2}/\d{2}$',                          'yyyy/mm/dd'),
    (r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$',              'yyyy-mm-dd HH:MM'),
    (r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$',        'yyyy-mm-dd HH:MM:SS'),

    # Day-first numeric (UK style)
    (r'^\d{2}/\d{2}/\d{4}$',                          'dd/mm/yyyy'),
    (r'^\d{1,2}/\d{1,2}/\d{4}$',                      'd/m/yyyy'),
    (r'^\d{2}/\d{2}/\d{2}$',                          'dd/mm/yy'),
    (r'^\d{1,2}/\d{1,2}/\d{2}$',                      'd/m/yy'),
    (r'^\d{2}-\d{2}-\d{4}$',                          'dd-mm-yyyy'),
    (r'^\d{1,2}-\d{1,2}-\d{4}$',                      'd-m-yyyy'),

    # With times (24h)
    (r'^\d{1,2}/\d{1,2}/\d{4} \d{2}:\d{2}$',          'd/m/yyyy HH:MM'),
    (r'^\d{1,2}/\d{1,2}/\d{4} \d{2}:\d{2}:\d{2}$',    'd/m/yyyy HH:MM:SS'),

    # Month names
    (r'^\d{1,2} [A-Za-z]{3} \d{4}$',                  'd Mon yyyy'),     # e.g., 5 Jan 2015
    (r'^\d{1,2} [A-Za-z]{3} \d{2}$',                  'd Mon yy'),
    (r'^\d{1,2} [A-Za-z]+ \d{4}$',                    'd Month yyyy'),   # e.g., 5 January 2015
    (r'^[A-Za-z]{3} \d{1,2}, \d{4}$',                 'Mon d, yyyy'),    # e.g., Jan 5, 2015
    (r'^[A-Za-z]+ \d{1,2}, \d{4}$',                   'Month d, yyyy'),

    # With AM/PM
    (r'^\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2} ?[APap][Mm]$', 'd/m/yyyy h:MM AM/PM'),
    (r'^\d{1,2} [A-Za-z]{3} \d{4} \d{1,2}:\d{2} ?[APap][Mm]$', 'd Mon yyyy h:MM AM/PM'),
    
    # ddMONYYYY without separators
    (r'^\d{2}[A-Za-z]{3}\d{4}$',                'ddMONyyyy'),
]

"""
# Check out PATTERNS
print("=== PATTERNS ===")
for p, l in PATTERNS:
    print(f"Pattern: {p}, Label: {l}")
"""
compiled = [(re.compile(p), label) for p, label in PATTERNS]

"""
# Check contents of compiled
print("=== COMPILED PATTERNS ===")
for p, l in compiled:
    print(f"Pattern: {p}, Label: {l}")
"""
# Function to classify a single string
def classify(x: str) -> str:
    if pd.isna(x) or x is None or x == '':
        return 'NA/empty'
    x = str(x)
    for rx, label in compiled:
        if rx.match(x):
            return label
    return 'unknown'

formats = s.map(classify)

# 3) Summary counts
format_counts = formats.value_counts(dropna=False)

# 4) A few examples per bucket
examples = (
    pd.DataFrame({'raw': s, 'format': formats})
      .groupby('format')['raw']
      .apply(lambda g: g.dropna().unique()[:5])  # up to 5 examples per format
)

print("=== Format counts ===")
print(format_counts)
print("\n=== Examples per format (up to 5) ===")
for fmt, vals in examples.items():
    print(f"\n[{fmt}]")
    for v in vals:
        print("  ", v)

print(x)
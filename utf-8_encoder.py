import pandas as pd

df = pd.read_csv('encoded-Reviews.csv', encoding='latin-1', dtype=str)
df.to_csv('utf8-Reviews.csv', encoding='utf-8', index=False)
print("File re-encoded to UTF-8 and saved as 'utf8-Reviews.csv'")
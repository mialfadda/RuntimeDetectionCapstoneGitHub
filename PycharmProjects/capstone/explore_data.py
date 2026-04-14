import pandas as pd

df = pd.read_csv('data/dataset.csv')

print("=== Label Column ===")
print(df['label'].value_counts())

print("\n=== Type Column ===")
print(df['type'].value_counts())

print("\n=== Sample URL + Label ===")
print(df[['url', 'type', 'label']].head(10))
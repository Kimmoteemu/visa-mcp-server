import pandas as pd

df = pd.read_csv('questions.csv', names=['question','answer'])
df.to_json('questions.json', orient='records', indent=2)
print(df.head())
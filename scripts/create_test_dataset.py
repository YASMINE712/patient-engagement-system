"""Create synthetic software-test data only; never replace an existing dataset."""
import csv
from pathlib import Path

target = Path(__file__).resolve().parents[1] / 'data' / 'raw' / 'legacy_wellness.csv'
if target.exists():
    raise SystemExit('Dataset already exists; refusing to replace it.')
target.parent.mkdir(parents=True, exist_ok=True)
categories = ['Stress Management', 'Sleep Hygiene', 'Exercise and Physical Activity', 'Diet and Nutrition']
fields = ['Person ID', 'Gender', 'Age', 'BMI Category', 'Stress Level', 'Sleep Duration'] + categories + ['source']
with target.open('w', newline='', encoding='utf-8') as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for i in range(6):
        row = {'Person ID': i + 1, 'Gender': 'Female' if i % 2 else 'Male',
               'Age': 25 + i, 'BMI Category': 'Normal', 'Stress Level': 3 + i,
               'Sleep Duration': 6 + i / 10, 'source': 'synthetic_software_test_fixture'}
        row.update({category: f'Synthetic test suggestion {i} for {category}' for category in categories})
        writer.writerow(row)
print('Created synthetic software-test data. This is not a recommendation benchmark.')

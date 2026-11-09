#!/usr/bin/env python
# Send two example wines to the prediction service.
# Usage:
#   python test.py                                   # local service
#   python test.py https://<your-app>/predict        # any other URL
#   SERVICE_URL=https://<your-app>/predict python test.py

import os
import sys

import requests


url = sys.argv[1] if len(sys.argv) > 1 else os.getenv('SERVICE_URL', 'http://localhost:9696/predict')

examples = {
    'batch A (rated 8 by the panel)': {
        'fixed_acidity': 7.9, 'volatile_acidity': 0.35, 'citric_acid': 0.46, 'residual_sugar': 3.6,
        'chlorides': 0.078, 'free_sulfur_dioxide': 15.0, 'total_sulfur_dioxide': 37.0,
        'density': 0.9973, 'ph': 3.35, 'sulphates': 0.86, 'alcohol': 12.8,
    },
    'batch B (rated 5 by the panel)': {
        'fixed_acidity': 7.4, 'volatile_acidity': 0.70, 'citric_acid': 0.0, 'residual_sugar': 1.9,
        'chlorides': 0.076, 'free_sulfur_dioxide': 11.0, 'total_sulfur_dioxide': 34.0,
        'density': 0.9978, 'ph': 3.51, 'sulphates': 0.56, 'alcohol': 9.4,
    },
}

print(f'service: {url}\n')

for name, wine in examples.items():
    response = requests.post(url, json=wine, timeout=30)
    response.raise_for_status()
    result = response.json()

    if result['is_good']:
        decision = '-> send to premium tasting panel'
    else:
        decision = '-> standard line'

    print(f"{name}: good_probability = {result['good_probability']:.3f} "
          f"(threshold {result['threshold']}) {decision}")

#!/usr/bin/env python
# Train the final red wine quality model and save it to model.bin.
# The model and its parameters were chosen in notebook.ipynb; this script only
# reproduces the final training step (notebook §12) without the exploration.

import pickle
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler


# parameters

DATA_PATH = 'data/winequality-red.csv'
OUTPUT_FILE = 'model.bin'
SEED = 1

C = 0.1            # notebook §6: best val ROC AUC for log1p + scaling, class_weight=None
THRESHOLD = 0.24   # notebook §11: F1-optimal threshold on validation

print(f'scikit-learn {sklearn.__version__}, xgboost {xgboost.__version__}, pandas {pd.__version__}')


# data preparation

df = pd.read_csv(DATA_PATH, sep=None, engine='python')   # works for the comma (Kaggle) and semicolon (UCI) versions
df.columns = df.columns.str.lower().str.replace(' ', '_')

# exact duplicates would land in both train and test -> drop them before splitting (notebook §2)
df = df.drop_duplicates().reset_index(drop=True)
df['good'] = (df.quality >= 7).astype(int)

features = [c for c in df.columns if c not in ['quality', 'good']]

# same split as the notebook: 80% full_train / 20% test, stratified
df_full_train, df_test = train_test_split(df, test_size=0.2, random_state=SEED, stratify=df.good)

y_full_train = df_full_train.good.values
y_test = df_test.good.values

print(f'rows after dedup: {len(df)}, full_train: {len(df_full_train)}, test: {len(df_test)}')


# training

pipeline = make_pipeline(
    DictVectorizer(sparse=False),
    FunctionTransformer(np.log1p),
    StandardScaler(),
    LogisticRegression(C=C, max_iter=1000),
)
pipeline.fit(df_full_train[features].to_dict(orient='records'), y_full_train)


# evaluation on test (should match notebook §12)

y_pred = pipeline.predict_proba(df_test[features].to_dict(orient='records'))[:, 1]
y_pred_label = y_pred >= THRESHOLD

print(f'test ROC AUC: {roc_auc_score(y_test, y_pred):.4f}')
print(f'test PR AUC:  {average_precision_score(y_test, y_pred):.4f}')
print(f'at threshold {THRESHOLD}: precision {precision_score(y_test, y_pred_label):.3f}, '
      f'recall {recall_score(y_test, y_pred_label):.3f}, F1 {f1_score(y_test, y_pred_label):.3f}')


# saving

artifact = {
    'pipeline': pipeline,
    'threshold': THRESHOLD,
    'features': features,
    'model_name': f'log1p + StandardScaler + LogisticRegression(C={C})',
    'trained_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    'sklearn_version': sklearn.__version__,
    'xgboost_version': xgboost.__version__,
}

with open(OUTPUT_FILE, 'wb') as f_out:
    pickle.dump(artifact, f_out)

print(f'model saved to {OUTPUT_FILE}')

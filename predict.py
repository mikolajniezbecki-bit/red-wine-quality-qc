#!/usr/bin/env python
# FastAPI service: lab analysis of a red wine batch -> probability that the
# tasting panel rates it good (quality >= 7).
# Run: uvicorn predict:app --host 0.0.0.0 --port 9696

import pickle

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field


MODEL_FILE = 'model.bin'

with open(MODEL_FILE, 'rb') as f_in:
    artifact = pickle.load(f_in)

pipeline = artifact['pipeline']
threshold = artifact['threshold']


# Bounds are plausible physical ranges, a bit wider than what the dataset contains.
# Values outside them are almost certainly typos (or a different kind of wine),
# so the API rejects them with HTTP 422 instead of returning a meaningless score.
class WineSample(BaseModel):
    fixed_acidity: float = Field(..., ge=3, le=20, description='g(tartaric acid)/dm³')
    volatile_acidity: float = Field(..., ge=0, le=2.5, description='g(acetic acid)/dm³')
    citric_acid: float = Field(..., ge=0, le=1.5, description='g/dm³')
    residual_sugar: float = Field(..., ge=0, le=30, description='g/dm³')
    chlorides: float = Field(..., ge=0, le=1, description='g(sodium chloride)/dm³')
    free_sulfur_dioxide: float = Field(..., ge=0, le=150, description='mg/dm³')
    total_sulfur_dioxide: float = Field(..., ge=0, le=350, description='mg/dm³')
    density: float = Field(..., ge=0.98, le=1.01, description='g/cm³')
    ph: float = Field(..., ge=2.5, le=4.5, description='pH')
    sulphates: float = Field(..., ge=0, le=3, description='g(potassium sulphate)/dm³')
    alcohol: float = Field(..., ge=7, le=16, description='% vol.')

    model_config = {
        'json_schema_extra': {
            'examples': [{
                'fixed_acidity': 7.9, 'volatile_acidity': 0.35, 'citric_acid': 0.46,
                'residual_sugar': 3.6, 'chlorides': 0.078, 'free_sulfur_dioxide': 15.0,
                'total_sulfur_dioxide': 37.0, 'density': 0.9973, 'ph': 3.35,
                'sulphates': 0.86, 'alcohol': 12.8,
            }]
        }
    }


class PredictResponse(BaseModel):
    good_probability: float
    is_good: bool
    threshold: float


app = FastAPI(title='red-wine-quality-qc')


def predict_single(sample: dict) -> float:
    return float(pipeline.predict_proba([sample])[0, 1])


@app.post('/predict')
def predict(sample: WineSample) -> PredictResponse:
    prob = predict_single(sample.model_dump())
    return PredictResponse(
        good_probability=prob,
        is_good=prob >= threshold,
        threshold=threshold,
    )


@app.get('/health')
def health():
    return {'status': 'ok'}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=9696)

from fastapi.testclient import TestClient

from predict import app


client = TestClient(app)

GOOD_WINE = {  # rated 8 in the dataset
    'fixed_acidity': 7.9, 'volatile_acidity': 0.35, 'citric_acid': 0.46, 'residual_sugar': 3.6,
    'chlorides': 0.078, 'free_sulfur_dioxide': 15.0, 'total_sulfur_dioxide': 37.0,
    'density': 0.9973, 'ph': 3.35, 'sulphates': 0.86, 'alcohol': 12.8,
}
AVERAGE_WINE = {  # rated 5 in the dataset
    'fixed_acidity': 7.4, 'volatile_acidity': 0.70, 'citric_acid': 0.0, 'residual_sugar': 1.9,
    'chlorides': 0.076, 'free_sulfur_dioxide': 11.0, 'total_sulfur_dioxide': 34.0,
    'density': 0.9978, 'ph': 3.51, 'sulphates': 0.56, 'alcohol': 9.4,
}


def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_predict_returns_probability():
    response = client.post('/predict', json=GOOD_WINE)
    assert response.status_code == 200
    result = response.json()
    assert 0 <= result['good_probability'] <= 1
    assert result['is_good'] == (result['good_probability'] >= result['threshold'])


def test_examples_are_ranked_sensibly():
    p_good = client.post('/predict', json=GOOD_WINE).json()['good_probability']
    p_average = client.post('/predict', json=AVERAGE_WINE).json()['good_probability']
    assert p_good > p_average
    assert client.post('/predict', json=GOOD_WINE).json()['is_good'] is True
    assert client.post('/predict', json=AVERAGE_WINE).json()['is_good'] is False


def test_out_of_range_value_is_rejected():
    response = client.post('/predict', json={**GOOD_WINE, 'alcohol': -1})
    assert response.status_code == 422


def test_missing_field_is_rejected():
    wine = dict(GOOD_WINE)
    del wine['sulphates']
    response = client.post('/predict', json=wine)
    assert response.status_code == 422

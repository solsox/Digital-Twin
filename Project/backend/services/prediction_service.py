from ml.model import predict_risk

def run_prediction(patient_data):
    score, level = predict_risk(patient_data)

    return {
        "score": score,
        "level": level
    }
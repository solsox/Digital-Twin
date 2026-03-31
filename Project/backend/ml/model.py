import numpy as np

def predict_risk(data):
    score = (
        data["age"] * 0.2 +
        data["systolic_bp"] * 0.3 +
        data["cholesterol"] * 0.5
    ) / 300

    if score > 0.7:
        level = "alto"
    elif score > 0.4:
        level = "medio"
    else:
        level = "bajo"

    return score, level
import sys
sys.path.insert(0, '/Users/aljohara/PycharmProjects/capstone')
import joblib

feature_names = joblib.load("backend/app/models/saved/feature_names.pkl")
print(feature_names)
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import logging
from pathlib import Path
from database import cursor
from config import intent_classes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

vectorizer = None
classifier = None

def train_intent_classifier():
    """Train or load a simple intent classifier"""
    global vectorizer, classifier
    model_path = Path('intent_classifier.pkl')
    vectorizer_path = Path('vectorizer.pkl')
    
    if model_path.exists() and vectorizer_path.exists():
        with open(model_path, 'rb') as f:
            classifier = pickle.load(f)
        with open(vectorizer_path, 'rb') as f:
            vectorizer = pickle.load(f)
        return

    cursor.execute("SELECT query, intent FROM conversations WHERE intent != 'unknown'")
    data = cursor.fetchall()
    if len(data) < 10:
        logging.warning("Not enough data to train classifier")
        return

    queries, intents = zip(*data)
    vectorizer = TfidfVectorizer(max_features=1000)
    X = vectorizer.fit_transform(queries)
    classifier = LogisticRegression(max_iter=1000)
    classifier.fit(X, intents)

    with open(model_path, 'wb') as f:
        pickle.dump(classifier, f)
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)

def predict_intent(query):
    """Predict intent for a query using the trained classifier"""
    if vectorizer is None or classifier is None:
        return 'unknown'
    X = vectorizer.transform([query])
    return classifier.predict(X)[0]
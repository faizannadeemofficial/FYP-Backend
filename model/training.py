import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_class_weight
import numpy as np
import joblib

# Load and clean the data
df = pd.read_csv("model/clean_file.csv")

# Remove rows with NaN values in text or is_offensive columns
df = df.dropna(subset=["is_offensive", "text"])

# Convert text column to string type to ensure all values are strings
df["text"] = df["text"].astype(str)

# Compute class weights
classes = np.array([0, 1])  # Convert to numpy array
class_weights = compute_class_weight(
    class_weight="balanced", classes=classes, y=df["is_offensive"]
)
weights_dict = {cls: weight for cls, weight in zip(classes, class_weights)}

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    df["text"], df["is_offensive"], test_size=0.2, random_state=42
)

# TF-IDF
vectorizer = TfidfVectorizer(max_features=100000)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Train with class weights
model = LogisticRegression(class_weight=weights_dict, max_iter=1000)
model.fit(X_train_tfidf, y_train)

# Evaluate
y_pred = model.predict(X_test_tfidf)
print(classification_report(y_test, y_pred))

# Save the model and vectorizer
joblib.dump(model, "model/offensive_classifier.joblib")
joblib.dump(vectorizer, "model/tfidf_vectorizer.joblib")
print(
    "\nModel and vectorizer have been saved to 'model/offensive_classifier.joblib' and 'model/tfidf_vectorizer.joblib'"
)

import joblib


class ProfanityDetectionModel:
    def __init__(self) -> None:
        # Load the saved model and vectorizer
        self.model = joblib.load("model/offensive_classifier.joblib")
        self.vectorizer = joblib.load("model/tfidf_vectorizer.joblib")

    def __str__(self) -> str:
        pass

    def predict_text(self, text) -> bool:
        """
        Predict if a single text is offensive or not.

        Args:
            text (str): The text to classify

        Returns:
            dict: Dictionary containing prediction (0 or 1) and probability
        """
        # Convert text to TF-IDF features
        text_tfidf = self.vectorizer.transform([text])

        # Get prediction
        prediction = self.model.predict(text_tfidf)[0]

        # Get probability scores
        proba = self.model.predict_proba(text_tfidf)[0]

        # print("Word is: " + text + "\n" + str(int(prediction)) + " is prediction\n" + str(float(proba[1])) + " is probation percentage")
        if int(prediction) == 1 and float(proba[1]) * 100 > 50.0:
            return True
        else:
            return False


# pd = ProfanityDetectionModel()
# print(pd.predict_text("You are a fucking asshole"))

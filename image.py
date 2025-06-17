import time
import torch
import clip
from PIL import Image, ImageFilter


class ImageProfanityFilter:
    def __init__(self, model_name="ViT-B/32", device=None, threshold=0.3):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.preprocess = clip.load(model_name, device=self.device)
        self.threshold = threshold

        self.harmful_categories = [
            "harmful content involving harassment",
            "harmful content involving hate",
            "harmful content involving illicit activities",
            "harmful content involving self-harm",
            "harmful content involving sexual content",
            "harmful content involving violence",
            "harmful content involving weapons",
            "harmful content involving exposed car license plates",
            "harmful content involving graphic gore",
            "harmful content involving child exploitation",
            "harmful content involving tobacco use or promotion",
            "harmful content involving alcohol use or promotion",
            "harmful content involving gambling",
        ]

        self.text_tokens = clip.tokenize(self.harmful_categories).to(self.device)

    def blur_image(self, input_path, blur_radius=10):
        # Open the input image
        image = Image.open(input_path)

        # Apply Gaussian blur
        blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        # Save the output
        output_path = f"storage/imgs/{int(time.time())}.jpg"
        blurred_image.save(output_path)

        return output_path

    def detect(self, image_path: str):
        # print("Started detection...")
        image = self.preprocess(Image.open(image_path)).unsqueeze(0).to(self.device)

        with torch.no_grad():
            self.model.encode_image(image)
            self.model.encode_text(self.text_tokens)
            logits_per_image, _ = self.model(image, self.text_tokens)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy().flatten()

        results = list(zip(self.harmful_categories, probs))
        harmful = [label for label, prob in results if prob > self.threshold]

        return {
            "isFlagged": True if len(harmful) > 0 else False,
            "harmful_detected": harmful,
        }

    def pretty_print(self, result):
        print("\n--- Harmful Content Probabilities ---")
        for label, prob in result["all_categories"]:
            print(f"{label}: {prob:.4f}")

        if result["harmful_detected"]:
            print("\n⚠️ Potentially harmful content detected:")
            for label, prob in result["harmful_detected"]:
                print(f" - {label} (Confidence: {prob:.2%})")
        else:
            print("\n✅ No harmful content detected.")

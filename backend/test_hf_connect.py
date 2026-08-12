import torch
from transformers import pipeline

def run_huggingface_demo():
    print("🔄 Connecting to Hugging Face Hub and loading model...")

    # 1. Pipeline automatically connects to HF Hub, downloads DistilBERT, and sets up inference
    classifier = pipeline(
        task="sentiment-analysis",
        model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
        device_map="auto" if torch.cuda.is_available() else "cpu"
    )

    print("✅ Model loaded successfully from Hugging Face Hub!")
    print("-" * 50)

    # 2. Test Input: Driver voice transcript
    driver_speech = "The rear tires are slipping, I'm losing time on sector 2!"

    # 3. Model Inference
    result = classifier(driver_speech)

    print(f"🏎️ Driver Input: '{driver_speech}'")
    print(f"📊 Hugging Face Model Output: {result}")

if __name__ == "__main__":
    run_huggingface_demo()

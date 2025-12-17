from ultralytics import YOLO
from transformers import AutoProcessor, LlavaNextForConditionalGeneration
import torch

def download_models():
    print("📥 Downloading YOLOv10...")
    yolo_model = YOLO("yolov10m.pt")
    print("✅ YOLOv10 downloaded")

    print("📥 Downloading LLaVA-NeXT 7B...")
    
    model_id = "llava-hf/llava-v1.6-mistral-7b-hf"  # LLaVA-NeXT-7B
    
    processor = AutoProcessor.from_pretrained(model_id)

    vlm_model = LlavaNextForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map="auto"
    )

    print("✅ LLaVA-NeXT 7B downloaded")
    print("✅ All models ready!")

    return yolo_model, processor, vlm_model

if __name__ == "__main__":
    download_models()

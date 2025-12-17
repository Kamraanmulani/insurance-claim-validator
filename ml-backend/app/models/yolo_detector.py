from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
import os

class YOLODamageDetector:
    def __init__(self, model_path: str = "yolov10m.pt"):
        """Initialize YOLO model for damage detection"""
        # Note: User changed to yolov10m.pt in download_models.py, so defaulting to that
        if not os.path.exists(model_path):
             # Fallback or check if n version exists if m is missing, but user downloaded m
             pass
        
        print(f"Loading YOLO model from {model_path}...")
        self.model = YOLO(model_path)
        
        # Define vehicle parts we're interested in
        # Note: Using COCO classes as base, will detect relevant objects
        self.relevant_classes = [
            'car', 'truck', 'bus', 'motorcycle', 'bicycle'
        ]
        
        # Define custom damage-related mappings
        self.damage_indicators = {
            'dent': ['deformed', 'crushed', 'bent'],
            'crack': ['broken', 'cracked', 'shattered'],
            'scratch': ['scratched', 'scraped'],
            'missing': ['missing', 'detached', 'fallen']
        }
        
        print("✅ YOLO model loaded successfully")
    
    def detect_objects(self, image_path: str, conf_threshold: float = 0.25) -> List[Dict[str, Any]]:
        """Detect objects and potential damage in image"""
        
        # Run inference
        results = self.model(image_path, conf=conf_threshold)
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Extract detection info
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                
                detection = {
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": round(confidence, 3),
                    "class_id": class_id,
                    "class_name": class_name,
                    "area": int((x2 - x1) * (y2 - y1))
                }
                
                detections.append(detection)
        
        return detections
    
    def generate_annotated_image(self, 
                                 image_path: str, 
                                 detections: List[Dict[str, Any]], 
                                 output_path: str) -> str:
        """Generate image with bounding boxes and labels"""
        
        # Load image
        image = cv2.imread(image_path)
        
        # Draw detections
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            confidence = det["confidence"]
            class_name = det["class_name"]
            
            # Draw bounding box
            color = (0, 255, 0)  # Green for detected objects
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name} {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(
                image,
                (x1, y1 - label_size[1] - 5),
                (x1 + label_size[0], y1),
                color,
                -1
            )
            cv2.putText(
                image,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1
            )
        
        # Save annotated image
        cv2.imwrite(output_path, image)
        return output_path
    
    def analyze_damage_regions(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze detected objects to identify potential damage regions"""
        
        analysis = {
            "total_detections": len(detections),
            "primary_vehicle_detected": False,
            "vehicle_type": None,
            "detected_objects": [],
            "damage_indicators": []
        }
        
        # Find primary vehicle
        vehicles = [d for d in detections if d["class_name"] in self.relevant_classes]
        
        if vehicles:
            # Get largest vehicle (likely the claim subject)
            primary_vehicle = max(vehicles, key=lambda x: x["area"])
            analysis["primary_vehicle_detected"] = True
            analysis["vehicle_type"] = primary_vehicle["class_name"]
        
        # Categorize all detections
        for det in detections:
            analysis["detected_objects"].append({
                "type": det["class_name"],
                "confidence": det["confidence"],
                "bbox": det["bbox"]
            })
        
        return analysis
    
    def get_damage_score_from_detections(self, detections: List[Dict[str, Any]]) -> float:
        """Calculate initial damage score based on detections"""
        
        # Simple heuristic for prototype
        # More sophisticated scoring will come from LLaVA
        
        if not detections:
            return 0.0
        
        # Base score on number of detections and confidence
        score = 0.0
        
        for det in detections:
            # Higher confidence = more likely actual damage
            score += det["confidence"] * 2
        
        # Normalize to 0-10 scale
        normalized_score = min(score, 10.0)
        
        return round(normalized_score, 2)
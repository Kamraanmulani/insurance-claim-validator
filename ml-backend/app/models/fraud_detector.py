import imagehash
from PIL import Image
from typing import Dict, Any, List, Optional
import numpy as np
from datetime import datetime
import os
import json

class FraudDetector:
    def __init__(self, use_qdrant: bool = None, qdrant_host: str = None, qdrant_port: int = None):
        """Initialize fraud detection system with optional Qdrant support"""
        
        # Get settings from environment variables or parameters
        if use_qdrant is None:
            use_qdrant = os.getenv("USE_QDRANT", "false").lower() == "true"
        
        if qdrant_host is None:
            qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        
        if qdrant_port is None:
            qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        
        self.use_qdrant = use_qdrant
        self.storage_file = "data/image_hashes.json"
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        if use_qdrant:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import Distance, VectorParams, PointStruct
                
                # Connect to Qdrant
                print(f"🔗 Connecting to Qdrant at {qdrant_host}:{qdrant_port}")
                self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
                self.collection_name = "claim_images"
                
                # Initialize collection if it doesn't exist
                self._init_collection()
                print("✅ Fraud Detector initialized with Qdrant")
            except Exception as e:
                print(f"⚠️  Qdrant not available: {e}")
                print("   Falling back to file-based storage")
                self.use_qdrant = False
                self._init_file_storage()
        else:
            # Use file-based storage as fallback
            self._init_file_storage()
            print("✅ Fraud Detector initialized with file-based storage")
    
    def _init_file_storage(self):
        """Initialize file-based storage for image hashes"""
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, 'w') as f:
                json.dump([], f)
    
    def _init_collection(self):
        """Initialize Qdrant collection for image hashes"""
        try:
            from qdrant_client.models import Distance, VectorParams
            
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=64, distance=Distance.COSINE)
                )
                print(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            print(f"Error initializing Qdrant collection: {e}")
            raise
    
    def compute_perceptual_hash(self, image_path: str) -> Dict[str, Any]:
        """Compute multiple perceptual hashes for robust duplicate detection"""
        
        image = Image.open(image_path)
        
        # Compute different hash types
        phash = imagehash.phash(image)
        dhash = imagehash.dhash(image)
        whash = imagehash.whash(image)
        average_hash = imagehash.average_hash(image)
        
        # Convert to vectors for Qdrant (using phash as main)
        phash_vector = self._hash_to_vector(phash)
        
        return {
            "phash": str(phash),
            "dhash": str(dhash),
            "whash": str(whash),
            "average_hash": str(average_hash),
            "phash_vector": phash_vector
        }
    
    def _hash_to_vector(self, hash_obj) -> List[float]:
        """Convert image hash to vector for Qdrant"""
        # Convert hash to binary string, then to vector
        binary_str = format(int(str(hash_obj), 16), '064b')
        vector = [float(bit) for bit in binary_str]
        return vector
    
    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate Hamming distance between two hashes"""
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    
    def check_duplicate(self, image_path: str, job_id: str, threshold: float = 0.9) -> Dict[str, Any]:
        """Check if image is a duplicate or reused from previous claims"""
        
        # Compute hash
        hashes = self.compute_perceptual_hash(image_path)
        
        if self.use_qdrant:
            return self._check_duplicate_qdrant(hashes, job_id, threshold)
        else:
            return self._check_duplicate_file(hashes, job_id, threshold)
    
    def _check_duplicate_qdrant(self, hashes: Dict[str, Any], job_id: str, threshold: float) -> Dict[str, Any]:
        """Check duplicates using Qdrant vector database"""
        try:
            from qdrant_client.models import PointStruct
            
            # Search for similar images in Qdrant
            search_results = None

            # Newer clients: `query_points` (returns QueryResponse with .points)
            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=hashes["phash_vector"],
                    limit=5,
                    score_threshold=threshold,
                )
                search_results = response.points

            # Older clients: `search` or `search_points` (return list[ScoredPoint])
            elif hasattr(self.client, "search") or hasattr(self.client, "search_points"):
                search_method = getattr(self.client, "search", None) or getattr(self.client, "search_points", None)
                search_results = search_method(
                    collection_name=self.collection_name,
                    query_vector=hashes["phash_vector"],
                    limit=5,
                    score_threshold=threshold,
                )

            else:
                raise AttributeError("QdrantClient has no compatible search method (query_points/search/search_points)")
            
            is_duplicate = len(search_results) > 0
            duplicate_details = []
            
            if is_duplicate:
                for result in search_results:
                    duplicate_details.append({
                        "job_id": result.payload.get("job_id"),
                        "similarity_score": result.score,
                        "timestamp": result.payload.get("timestamp")
                    })
            
            # Store current image hash
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=abs(hash(job_id)) % (10 ** 8),  # Convert to positive integer ID
                        vector=hashes["phash_vector"],
                        payload={
                            "job_id": job_id,
                            "timestamp": datetime.now().isoformat(),
                            "phash": hashes["phash"],
                            "dhash": hashes["dhash"]
                        }
                    )
                ]
            )
            
            return {
                "is_duplicate": is_duplicate,
                "duplicate_count": len(search_results),
                "duplicate_details": duplicate_details,
                "hashes": hashes
            }
        except Exception as e:
            print(f"Error in Qdrant duplicate check: {e}")
            # Fallback to file-based method
            return self._check_duplicate_file(hashes, job_id, threshold)
    
    def _check_duplicate_file(self, hashes: Dict[str, Any], job_id: str, threshold: float) -> Dict[str, Any]:
        """Check duplicates using file-based storage"""
        
        # Load existing hashes
        try:
            with open(self.storage_file, 'r') as f:
                stored_hashes = json.load(f)
        except:
            stored_hashes = []
        
        is_duplicate = False
        duplicate_details = []
        
        # Compare with stored hashes (using Hamming distance)
        # threshold of 0.9 similarity = max 6 bits different (out of 64)
        max_hamming = int((1 - threshold) * 64)
        
        for stored in stored_hashes:
            distance = self._hamming_distance(hashes["phash"], stored["phash"])
            if distance <= max_hamming:
                is_duplicate = True
                similarity = 1 - (distance / 64)
                duplicate_details.append({
                    "job_id": stored["job_id"],
                    "similarity_score": round(similarity, 3),
                    "timestamp": stored["timestamp"]
                })
        
        # Store current hash
        stored_hashes.append({
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "phash": hashes["phash"],
            "dhash": hashes["dhash"],
            "whash": hashes["whash"],
            "average_hash": hashes["average_hash"]
        })
        
        # Save updated hashes
        with open(self.storage_file, 'w') as f:
            json.dump(stored_hashes, f, indent=2)
        
        return {
            "is_duplicate": is_duplicate,
            "duplicate_count": len(duplicate_details),
            "duplicate_details": duplicate_details,
            "hashes": hashes
        }
    
    def calculate_metadata_fraud_score(self, 
                                       metadata: Dict[str, Any],
                                       validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate fraud risk score based on metadata"""
        
        fraud_score = 0
        fraud_indicators = []
        
        # Base score from validation
        fraud_score += validation_result.get("risk_score", 0)
        
        # Check for missing EXIF
        if not metadata.get("has_exif"):
            fraud_score += 3
            fraud_indicators.append("Missing EXIF data")
        
        # Check for editing software
        if metadata.get("software"):
            software = metadata["software"].lower()
            editing_tools = ["photoshop", "gimp", "pixlr", "lightroom", "snapseed"]
            for tool in editing_tools:
                if tool in software:
                    fraud_score += 2
                    fraud_indicators.append(f"Edited with {tool}")
                    break
        
        # Check for suspicious metadata patterns
        if metadata.get("camera_make") == "Unknown" and metadata.get("has_exif"):
            fraud_score += 1
            fraud_indicators.append("Camera information missing despite EXIF presence")
        
        # Add validation issues
        if validation_result.get("issues"):
            fraud_indicators.extend(validation_result["issues"])
        
        # Normalize to 0-10 scale
        fraud_score = min(fraud_score, 10)
        
        return {
            "metadata_fraud_score": fraud_score,
            "fraud_indicators": fraud_indicators,
            "risk_level": self._get_risk_level(fraud_score)
        }
    
    def calculate_consistency_fraud_score(self, 
                                         consistency_score: float,
                                         is_consistent: bool) -> Dict[str, Any]:
        """Calculate fraud risk based on claim-image consistency"""
        
        # Inverse relationship: low consistency = high fraud risk
        if consistency_score >= 7:
            fraud_score = 1
            risk_indicators = []
        elif consistency_score >= 4:
            fraud_score = 5
            risk_indicators = ["Moderate inconsistency between claim and image"]
        else:
            fraud_score = 9
            risk_indicators = ["Severe inconsistency between claim and image"]
        
        if not is_consistent:
            risk_indicators.append("Claim description does not match visual evidence")
        
        return {
            "consistency_fraud_score": fraud_score,
            "risk_indicators": risk_indicators
        }
    
    def calculate_overall_fraud_score(self,
                                     metadata_score: float,
                                     duplicate_check: Dict[str, Any],
                                     consistency_score: float) -> Dict[str, Any]:
        """Calculate final fraud risk score combining all factors"""
        
        # Weight different factors
        weights = {
            "metadata": 0.3,
            "duplicate": 0.4,
            "consistency": 0.3
        }
        
        # Calculate weighted score
        duplicate_score = 10 if duplicate_check["is_duplicate"] else 0
        
        overall_score = (
            weights["metadata"] * metadata_score +
            weights["duplicate"] * duplicate_score +
            weights["consistency"] * consistency_score
        )
        
        overall_score = round(overall_score, 2)
        
        # Compile all indicators
        all_indicators = []
        
        if duplicate_check["is_duplicate"]:
            all_indicators.append(
                f"Image reused from {duplicate_check['duplicate_count']} previous claim(s)"
            )
        
        return {
            "overall_fraud_score": overall_score,
            "risk_level": self._get_risk_level(overall_score),
            "breakdown": {
                "metadata_score": metadata_score,
                "duplicate_score": duplicate_score,
                "consistency_score": consistency_score
            },
            "all_fraud_indicators": all_indicators
        }
    
    def _get_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level"""
        if score <= 3:
            return "LOW"
        elif score <= 7:
            return "MEDIUM"
        else:
            return "HIGH"

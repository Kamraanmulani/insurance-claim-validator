import requests
import json
import base64
from typing import Dict, Any, List
import re
from pathlib import Path

class LLaVADamageAnalyzer:
    def __init__(self, model_name: str = "llava:13b", ollama_host: str = "http://localhost:11434"):
        """Initialize LLaVA analyzer using Ollama"""
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.api_endpoint = f"{ollama_host}/api/generate"
        
        # Severity mapping
        self.severity_levels = {
            "minor": 2,
            "moderate": 5,
            "severe": 8,
            "total loss": 10,
            "total_loss": 10,
            "totalloss": 10
        }
        
        # Check if Ollama is running
        try:
            response = requests.get(f"{ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"✅ Connected to Ollama at {ollama_host}")
                models = response.json().get('models', [])
                model_names = [m.get('name') for m in models]
                if model_name in model_names:
                    print(f"✅ Model '{model_name}' is available")
                else:
                    print(f"⚠️  Model '{model_name}' not found. Available models: {model_names}")
                    print(f"   Run: ollama pull {model_name}")
            else:
                print(f"⚠️  Ollama API returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Cannot connect to Ollama at {ollama_host}")
            print(f"   Error: {e}")
            print(f"   Make sure Ollama is running: ollama serve")
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for Ollama API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_damage(self, 
                       image_path: str, 
                       claim_description: str,
                       metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze damage using Vision-Language Model via Ollama"""
        
        print(f"🔍 Analyzing damage with {self.model_name}...")
        
        # Create comprehensive prompt
        prompt = self._create_analysis_prompt(claim_description, metadata)
        
        # Encode image
        image_base64 = self._encode_image_to_base64(image_path)
        
        # Prepare request payload
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 512  # Max tokens to generate
            }
        }
        
        try:
            # Make request to Ollama
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=300  # 5 minutes timeout for LLaVA 13B
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            generated_text = result.get('response', '')
            
            print(f"✅ Analysis complete. Generated {len(generated_text)} characters")
            
            # Parse structured output
            parsed_analysis = self._parse_response(generated_text)
            
            # Calculate damage score
            damage_score = self._calculate_damage_score(parsed_analysis)
            
            return {
                "raw_response": generated_text,
                "parsed_analysis": parsed_analysis,
                "damage_score": damage_score,
                "severity_level": parsed_analysis.get("severity", "Unknown")
            }
            
        except requests.exceptions.Timeout:
            print("❌ Request timeout - Ollama took too long")
            raise Exception("Analysis timeout - please try again")
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            raise
    
    def _create_analysis_prompt(self, claim_description: str, metadata: Dict) -> str:
        """Create structured prompt for damage analysis"""
        
        prompt = f"""You are an expert insurance claim assessor. Analyze the damage in this vehicle image and provide a detailed assessment.

CLAIM DESCRIPTION:
{claim_description}

IMAGE METADATA:
- Camera: {metadata.get('camera_make', 'Unknown')} {metadata.get('camera_model', 'Unknown')}
- Capture Date: {metadata.get('date_time_original', 'Unknown')}
- Location: GPS {metadata.get('gps_latitude', 'N/A')}, {metadata.get('gps_longitude', 'N/A')}

INSTRUCTIONS:
Please analyze the image carefully and provide your assessment in this exact format:

DAMAGED PARTS:
[List each damaged part on a new line with a bullet point, e.g., "- rear bumper", "- right tail light"]

DAMAGE DESCRIPTION:
[Describe the type and extent of damage for each part in 2-3 sentences. Be specific about size, severity, and nature of damage]

SEVERITY RATING:
[Choose ONE: Minor, Moderate, Severe, or Total Loss]

CONSISTENCY CHECK:
[State if the visible damage matches the claim description. Answer "Consistent" or "Inconsistent" and explain why in 1-2 sentences]

ADDITIONAL OBSERVATIONS:
[Note any suspicious elements, unusual patterns, or important details]

Provide clear, specific observations based solely on what you see in the image."""
        
        return prompt
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLaVA's response into structured format"""
        
        parsed = {
            "damaged_parts": [],
            "damage_description": "",
            "severity": "Unknown",
            "consistency": "Unknown",
            "consistency_explanation": "",
            "additional_observations": ""
        }
        
        # Extract sections using regex
        sections = {
            "damaged_parts": r"DAMAGED PARTS:?\s*(.*?)(?=DAMAGE DESCRIPTION:|$)",
            "damage_description": r"DAMAGE DESCRIPTION:?\s*(.*?)(?=SEVERITY RATING:|$)",
            "severity": r"SEVERITY RATING:?\s*(.*?)(?=CONSISTENCY CHECK:|$)",
            "consistency": r"CONSISTENCY CHECK:?\s*(.*?)(?=ADDITIONAL OBSERVATIONS:|$)",
            "additional_observations": r"ADDITIONAL OBSERVATIONS:?\s*(.*?)$"
        }
        
        for key, pattern in sections.items():
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                
                if key == "damaged_parts":
                    # Extract list of parts (look for bullet points or lines)
                    parts = re.findall(r'[-•*]\s*([^\n]+)', content)
                    if not parts:
                        # If no bullet points, split by newlines or commas
                        parts = [p.strip() for p in re.split(r'[,\n]', content) if p.strip()]
                    parsed[key] = [p for p in parts if len(p) > 2]  # Filter out empty/short strings
                
                elif key == "severity":
                    # Extract severity level
                    severity_lower = content.lower()
                    for level in ["total loss", "severe", "moderate", "minor"]:
                        if level in severity_lower:
                            parsed[key] = level.title().replace(" ", " ")
                            break
                
                elif key == "consistency":
                    # Determine if consistent
                    content_lower = content.lower()
                    if "consistent" in content_lower and "inconsistent" not in content_lower:
                        parsed[key] = "Consistent"
                    elif "inconsistent" in content_lower:
                        parsed[key] = "Inconsistent"
                    else:
                        parsed[key] = "Unclear"
                    parsed["consistency_explanation"] = content
                
                else:
                    parsed[key] = content
        
        return parsed
    
    def _calculate_damage_score(self, parsed_analysis: Dict[str, Any]) -> float:
        """Calculate numeric damage score (0-10) from analysis"""
        
        score = 0.0
        
        # Base score from severity
        severity = parsed_analysis.get("severity", "Unknown").lower()
        severity_score = self.severity_levels.get(severity, 5)
        score = severity_score
        
        # Adjust based on number of damaged parts
        num_parts = len(parsed_analysis.get("damaged_parts", []))
        if num_parts >= 5:
            score = min(score + 2, 10)
        elif num_parts >= 3:
            score = min(score + 1, 10)
        
        # Adjust based on consistency
        if parsed_analysis.get("consistency") == "Inconsistent":
            # If inconsistent, might indicate exaggeration or fraud
            score = max(score - 1, 0)
        
        return round(score, 2)
    
    def check_consistency(self, 
                         image_path: str,
                         claim_description: str,
                         detected_damage: str) -> Dict[str, Any]:
        """Specific consistency check between claim and visual evidence"""
        
        print(f"🔍 Checking consistency with {self.model_name}...")
        
        prompt = f"""Compare the claim description with the visible damage in the image.

CLAIM DESCRIPTION:
{claim_description}

DETECTED DAMAGE FROM IMAGE ANALYSIS:
{detected_damage}

Please answer these questions clearly and concisely:

1. Does the visible damage match the claim description? (Yes/No/Partially)
2. Is the severity described in the claim accurate? (Underestimated/Accurate/Overestimated)
3. Are there any contradictions between the claim and image?
4. Rate consistency on 0-10 scale (0=completely inconsistent, 10=perfectly consistent)

Provide a brief, direct answer."""
        
        # Encode image
        image_base64 = self._encode_image_to_base64(image_path)
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.5,
                "num_predict": 256
            }
        }
        
        try:
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=300  # 5 minutes timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            result = response.json()
            consistency_response = result.get('response', '')
            
            print(f"✅ Consistency check complete")
            
            # Parse consistency score
            consistency_score = 5.0  # Default
            score_match = re.search(r'(\d+)\s*[/:]?\s*10|(\d+)\s*out of\s*10', consistency_response)
            if score_match:
                consistency_score = float(score_match.group(1) or score_match.group(2))
            
            return {
                "consistency_response": consistency_response,
                "consistency_score": consistency_score,
                "is_consistent": consistency_score >= 7
            }
            
        except Exception as e:
            print(f"❌ Consistency check error: {e}")
            # Return default values on error
            return {
                "consistency_response": f"Error during consistency check: {str(e)}",
                "consistency_score": 5.0,
                "is_consistent": False
            }
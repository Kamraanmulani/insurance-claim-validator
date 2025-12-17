from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from app.services.preprocessing import PreprocessingService
from app.services.detection_service import DetectionService
from app.services.scoring_engine import ScoringEngine
import shutil
import os
import uvicorn
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Insurance Claim Validation API",
    description="AI-powered insurance claim validation using VLMs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
preprocessing_service = PreprocessingService()
detection_service = DetectionService()
scoring_engine = ScoringEngine()

# Store processed claims in memory (for prototype)
claims_db = {}

@app.get("/")
async def root():
    return {
        "message": "Insurance Claim Validation API",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "analyze_claim": "/api/analyze-claim",
            "get_claim": "/api/claim/{job_id}",
            "list_claims": "/api/claims",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "preprocessing": "✓",
            "yolo_detection": "✓",
            "llava_analysis": "✓",
            "fraud_detection": "✓",
            "scoring_engine": "✓"
        }
    }

@app.post("/api/analyze-claim")
async def analyze_claim(
    image: UploadFile = File(...),
    claim_date: str = Form(...),
    claim_description: str = Form(...),
    claim_location: str = Form(default="Unknown"),
    policy_id: str = Form(default="")
):
    """
    Complete claim validation pipeline
    
    Steps:
    1. Preprocess image and extract metadata
    2. Run YOLO damage detection
    3. Perform LLaVA damage analysis
    4. Check for fraud indicators
    5. Generate final recommendation
    """
    
    # Validate inputs
    if not claim_description or len(claim_description) < 10:
        raise HTTPException(
            status_code=400,
            detail="Claim description must be at least 10 characters"
        )
    
    # Save uploaded file
    os.makedirs("data/uploads", exist_ok=True)
    temp_path = f"data/uploads/{image.filename}"
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        print(f"\n{'='*70}")
        print(f"Processing claim: {claim_description[:50]}...")
        print(f"{'='*70}\n")
        
        # Step 1: Preprocess
        print("📋 Step 1/5: Preprocessing...")
        preprocess_result = await preprocessing_service.process_claim_image(
            temp_path,
            claim_date,
            claim_description
        )
        print("✓ Preprocessing complete")
        
        # Step 2-4: Complete analysis (detection + fraud)
        print("🔍 Step 2-4/5: Running AI analysis...")
        analysis_result = await detection_service.complete_claim_analysis(
            preprocess_result["processed_path"],
            preprocess_result["job_id"],
            claim_description,
            preprocess_result["metadata"],
            preprocess_result["validation"]
        )
        print("✓ AI analysis complete")
        
        # Step 5: Make decision
        print("⚖️  Step 5/5: Generating recommendation...")
        decision = scoring_engine.make_decision(
            analysis_result["final_scores"]["damage_score"],
            analysis_result["final_scores"]["fraud_score"],
            analysis_result["final_scores"]["consistency_score"],
            preprocess_result["validation"]
        )
        print("✓ Recommendation generated")
        
        # Generate detailed report
        report = scoring_engine.generate_detailed_report(
            analysis_result,
            decision
        )
        
        # Store in database
        claim_record = {
            "job_id": preprocess_result["job_id"],
            "timestamp": datetime.now().isoformat(),
            "claim_info": {
                "date": claim_date,
                "description": claim_description,
                "location": claim_location,
                "policy_id": policy_id
            },
            "metadata": preprocess_result["metadata"],
            "report": report,
            "annotated_image": analysis_result["yolo_detection"]["annotated_image_path"]
        }
        
        claims_db[preprocess_result["job_id"]] = claim_record
        
        print(f"\n✅ Analysis complete!")
        print(f"Recommendation: {decision['recommendation']}")
        print(f"{'='*70}\n")
        
        return {
            "success": True,
            "job_id": preprocess_result["job_id"],
            "claim_info": claim_record["claim_info"],
            "report": report,
            "annotated_image_url": f"/api/annotated-image/{preprocess_result['job_id']}"
        }
    
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/claim/{job_id}")
async def get_claim(job_id: str):
    """Retrieve processed claim by job ID"""
    
    if job_id not in claims_db:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return claims_db[job_id]

@app.get("/api/claims")
async def list_claims():
    """List all processed claims"""
    
    claims_list = []
    for job_id, claim in claims_db.items():
        claims_list.append({
            "job_id": job_id,
            "timestamp": claim["timestamp"],
            "claim_description": claim["claim_info"]["description"][:100],
            "recommendation": claim["report"]["decision"]["recommendation"],
            "fraud_score": claim["report"]["fraud_analysis"]["overall_score"],
            "damage_score": claim["report"]["damage_assessment"]["score"]
        })
    
    return {
        "total": len(claims_list),
        "claims": sorted(claims_list, key=lambda x: x["timestamp"], reverse=True)
    }

@app.get("/api/annotated-image/{job_id}")
async def get_annotated_image(job_id: str):
    """Retrieve annotated image with bounding boxes"""
    image_path = f"data/uploads/annotated/{job_id}_annotated.jpg"
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Annotated image not found")
    
    return FileResponse(image_path, media_type="image/jpeg")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 Starting Insurance Claim Validation API")
    print("="*70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
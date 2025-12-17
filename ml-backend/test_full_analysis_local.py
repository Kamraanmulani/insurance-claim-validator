from fastapi.testclient import TestClient
from app.main import app
import os
import json

client = TestClient(app)

def test_full_analysis_local():
    test_image_path = "test_images/damaged_car.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found at {test_image_path}")
        return

    with open(test_image_path, "rb") as f:
        files = {"image": ("damaged_car.jpg", f, "image/jpeg")}
        data = {
            "claim_date": "2025-12-05",
            "claim_description": "Rear-end collision at traffic signal around 8 PM. Rear bumper severely dented and right tail light is completely broken.",
            "claim_location": "Pune"
        }
        
        print("🚀 Sending claim for analysis (Local Test)...")
        try:
            response = client.post(
                "/api/analyze-claim",
                files=files,
                data=data
            )
            
            print(f"Response Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print("❌ Request failed")
                print(response.text)
                return

            result = response.json()
            
            if not result.get("success"):
                print(f"❌ Error in response: {result.get('error')}")
                print(json.dumps(result, indent=2))
                return
            
            # Print comprehensive results
            print("\n" + "=" * 70)
            print("COMPREHENSIVE CLAIM ANALYSIS RESULTS")
            print("=" * 70)
            
            print(f"\n📋 Job ID: {result['job_id']}")
            
            # Metadata
            print("\n🔍 METADATA VALIDATION:")
            metadata_risk = result['metadata']['metadata_risk_score']
            print(f"  Risk Score: {metadata_risk}/10")
            if result['metadata']['validation']['issues']:
                print(f"  Issues: {', '.join(result['metadata']['validation']['issues'])}")
            else:
                print("  ✓ No metadata issues detected")
            
            # Summary
            summary = result['analysis']['summary']
            print("\n📊 DAMAGE ASSESSMENT SUMMARY:")
            print(f"  Severity Level: {summary['severity']}")
            print(f"  Damage Score: {summary['damage_score']}/10")
            print(f"  Consistency Score: {summary['consistency_score']}/10")
            print(f"  Claim Consistent: {'✓ Yes' if summary['is_consistent'] else '✗ No'}")
            
            # Damaged Parts
            print("\n🔧 DAMAGED PARTS IDENTIFIED:")
            for part in summary['damaged_parts']:
                print(f"  • {part}")
            
            # LLaVA Analysis
            llava = result['analysis']['llava_analysis']
            print("\n🤖 AI DETAILED ANALYSIS:")
            print(f"  {llava['parsed_analysis'].get('damage_description', 'N/A')}")
            
            # Consistency
            print("\n✅ CONSISTENCY CHECK:")
            print(f"  {result['analysis']['consistency_check']['consistency_response'][:200]}...")
            
            # YOLO Detection
            yolo_summary = result['analysis']['yolo_detection']['analysis']['detection_summary']
            print("\n🎯 OBJECT DETECTION:")
            print(f"  Vehicle Detected: {yolo_summary.get('vehicle_detected', False)}")
            print(f"  Objects Found: {yolo_summary.get('total_objects', 0)}")
            
            print(f"\n📸 Annotated image available at: {result['annotated_image_url']}")
            
            print("\n" + "=" * 70)

        except Exception as e:
            print(f"❌ Exception during test: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_full_analysis_local()

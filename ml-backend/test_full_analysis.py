import requests
import json

def test_full_analysis():
    test_image_path = "test_images/damaged_car.jpg"
    
    with open(test_image_path, "rb") as f:
        files = {"image": f}
        data = {
            "claim_date": "2025-12-05",
            "claim_description": "Rear-end collision at traffic signal around 8 PM. Rear bumper severely dented and right tail light is completely broken.",
            "claim_location": "Pune"
        }
        
        print("🚀 Sending claim for analysis...")
        response = requests.post(
            "http://localhost:8000/api/analyze-claim",
            files=files,
            data=data,
            timeout=600  # 10 minutes timeout for LLaVA 13B analysis
        )
        
        result = response.json()
        
        if not result.get("success"):
            print(f"❌ Error: {result.get('error')}")
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
        consistency_resp = result['analysis']['consistency_check']['consistency_response']
        # Print full response
        print(f"  Full Response:\n  {consistency_resp}")
        print(f"  Consistency Score: {result['analysis']['consistency_check']['consistency_score']}/10")
        print(f"  Is Consistent: {result['analysis']['consistency_check']['is_consistent']}")
        
        # YOLO Detection
        yolo_analysis = result['analysis']['yolo_detection']['analysis']
        print("\n🎯 OBJECT DETECTION:")
        print(f"  Vehicle Detected: {yolo_analysis.get('primary_vehicle_detected', False)}")
        print(f"  Vehicle Type: {yolo_analysis.get('vehicle_type', 'Unknown')}")
        print(f"  Total Detections: {yolo_analysis.get('total_detections', 0)}")
        
        print(f"\n📸 Annotated image available at: {result['annotated_image_url']}")
        
        # Download annotated image
        img_url = f"http://localhost:8000{result['annotated_image_url']}"
        img_response = requests.get(img_url)
        if img_response.status_code == 200:
            output_path = f"output_{result['job_id']}_annotated.jpg"
            with open(output_path, "wb") as f:
                f.write(img_response.content)
            print(f"✅ Downloaded: {output_path}")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    test_full_analysis()

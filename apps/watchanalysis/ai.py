import openai
import base64
import json
from pathlib import Path

# Set your OpenAI API key
openai.api_key = "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"

def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_watch(front_image, back_image, bracelet_image):
    """Analyze watch images and return structured JSON report"""
    
    # Encode images
    front_b64 = encode_image(front_image)
    back_b64 = encode_image(back_image)
    bracelet_b64 = encode_image(bracelet_image)
    
    prompt = """Analyze these three watch images (front, back, bracelet) and provide a detailed authenticity report.

Return ONLY a JSON object with this exact structure:

{
  "report_id": "AWC-TEST-XXX",
  "date_of_issue": "DD/MM/YYYY",
  "watch_information": {
    "brand": "",
    "model": "",
    "serial_ref_no": "",
    "date_of_analysis": "DD/MM/YYYY"
  },
  "detailed_analysis": [
    {
      "component": "Dial",
      "match_score": "XX%",
      "observations": ""
    },
    {
      "component": "Caseback",
      "match_score": "XX%",
      "observations": ""
    },
    {
      "component": "Bracelet / Clasp",
      "match_score": "XX%",
      "observations": ""
    },
    {
      "component": "Crown",
      "match_score": "XX%",
      "observations": ""
    },
    {
      "component": "Bezel",
      "match_score": "XX%",
      "observations": ""
    },
    {
      "component": "Hands",
      "match_score": "XX%",
      "observations": ""
    },
    {
      "component": "Crystal",
      "match_score": "XX%",
      "observations": ""
    },
    {
      "component": "Overall Proportions",
      "match_score": "XX%",
      "observations": ""
    }
  ],
  "conclusion": {
    "overall_authenticity_score": "XX%",
    "verdict": "Authentic/Counterfeit/Uncertain",
    "expert_note": ""
  }
}

Analyze each component carefully and provide match scores and detailed observations."""

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{front_b64}"
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{back_b64}"
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{bracelet_b64}"
                        }
                    }
                ],
            }
        ],
        max_tokens=2000,
        temperature=0.3
    )
    
    # Extract JSON from response
    result = response.choices[0].message.content
    
    # Try to parse JSON (remove markdown code blocks if present)
    if "```json" in result:
        result = result.split("```json")[1].split("```")[0].strip()
    elif "```" in result:
        result = result.split("```")[1].split("```")[0].strip()
    
    return json.loads(result)

# Main execution
if __name__ == "__main__":
    # Replace with your image paths
    front_image = "/content/Front.jpg"
    back_image = "/content/Back.jpg"
    bracelet_image = "/content/Bracelet.jpg"
    
    try:
        report = analyze_watch(front_image, back_image, bracelet_image)
        
        # Save to JSON file
        with open("watch_authenticity_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("Report generated successfully!")
        print(json.dumps(report, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")
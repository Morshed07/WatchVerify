import openai
import base64
import json
import re
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class WatchAIAnalyzer:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL or "gpt-4o"
    
    def encode_image(self, image_file):
        # print("Encoding image for AI analysis ai.py works") # clean up print statements for production
        try:
            # If it's a Django FieldFile
            if hasattr(image_file, 'read'):
                # Check if file is closed and reopen if necessary
                if image_file.closed:
                    image_file.open('rb')
                image_file.seek(0)  # Reset file pointer
                image_data = image_file.read()
            else:
                # If it's a file path
                with open(image_file, "rb") as f:
                    image_data = f.read()
            
            return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {str(e)}")
            raise
    
    def analyze_watch(self, front_image, back_image, bracelet_image):
        try:
            # Encode images
            front_b64 = self.encode_image(front_image)
            back_b64 = self.encode_image(back_image)
            bracelet_b64 = self.encode_image(bracelet_image)
            
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

Analyze each component carefully and provide match scores and detailed observations. Be very thorough and critical in your analysis."""

            response = openai.chat.completions.create(
                model=self.model,
                # Force JSON mode to ensure valid JSON structure is returned
                response_format={"type": "json_object"}, 
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
            
            # Extract content
            raw_result = response.choices[0].message.content
            
            # --- CLEANING LOGIC START ---
            if not raw_result:
                raise ValueError("OpenAI returned an empty response.")

            # 1. Attempt to find JSON object boundaries using Regex
            # This looks for the first '{' and the last '}' across multiple lines
            match = re.search(r'\{.*\}', raw_result, re.DOTALL)
            
            if match:
                clean_json_str = match.group(0)
            else:
                # If regex fails, fallback to simple strip (unlikely if valid JSON exists)
                clean_json_str = raw_result.strip()

            try:
                parsed_result = json.loads(clean_json_str)
            except json.JSONDecodeError:
                # If regex failed us, try one last aggressive clean for markdown
                clean_json_str = clean_json_str.replace("```json", "").replace("```", "").strip()
                parsed_result = json.loads(clean_json_str)
            # --- CLEANING LOGIC END ---

            logger.info(f"AI analysis completed successfully")
            return parsed_result
            
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"AI analysis failed: {str(e)}")
        except json.JSONDecodeError as e:
            # Log the raw response so you can see what actually failed
            logger.error(f"JSON parsing error: {str(e)} | Raw Content: {raw_result[:200]}...") 
            raise Exception(f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in AI analysis: {str(e)}")
            raise
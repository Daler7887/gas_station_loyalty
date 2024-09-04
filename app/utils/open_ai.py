from openai import OpenAI
from config import *
import json
client = OpenAI(api_key=OPENAI_API_TOKEN)

def recognize_plate(image_base64):
    response = client.chat.completions.create(
    model="gpt-4o",
    
    messages=[
        {
        "role": "system",
        "content": [
            {
            "type": "text",
            "text": "You are an AI assistant specialized in recognizing and extracting complete license plate numbers, including city codes, from images. Analyze the provided image of a vehicle's license plate and extract the entire license plate number, including any city code. Return the result in JSON format: {\"plateNumber\": \"LICENSE_PLATE_NUMBER\"}. If you cannot detect a license plate, return an empty string for 'plateNumber'. For example, if the license plate number is \"30A123BC\" (including city code \"30\"), the JSON output should be: {\"plateNumber\": \"30A123BC\"}. If the image does not contain a recognizable license plate, the JSON output should be: {\"plateNumber\": \"\"}."
            }
        ]
        },
        {
        "role": "user",
        "content": [
            {
            "type": "image_url",
            "image_url": {
                "url": "data:image/jpeg;base64,"+ image_base64 
            }
            }
        ]
        }
    ],
    temperature=1,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    response_text = response.choices[0].message.content
    plate_num = response_text.replace("```", "").replace("json", "").replace(" ", "")
    return json.loads(plate_num)["plateNumber"]

import json, os, uuid, decimal
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
import openai
import urllib.parse

# initialize boto3 resources
s3 = boto3.resource("s3")
ddb = boto3.resource("dynamodb")
bucket_name = os.environ["FF_BUCKET_NAME"]
card_table_name = ddb.Table(os.environ["FF_CARD_TABLE_NAME"])

# load openai api key from .secret
with open(".secret", "r") as f:
    api_key = f.read()

# setup openai api key
openai.api_key = api_key
os.environ["OPENAI_API_KEY"] = api_key
os.environ["TRANSFORMERS_CACHE"] = "/tmp"

# CORS (Cross-Origin Resource Sharing) headers to support cross-site HTTP requests
HEADERS = {
    "Access-Control-Allow-Origin": "*",
}

# this custom class is to handle decimal.Decimal objects in json.dumps()
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

# API handlers
def handler(event, context):
    """
    API handler for GET /user/{user_id}/en2jp/{prompt_txt}
    """
    
    try:
        path_params = event.get("pathParameters", {})
        prompt_txt = path_params.get("prompt_txt", "")
        user_id = path_params.get("user_id", "")
        prompt_txt = urllib.parse.unquote(prompt_txt)
        user_id = urllib.parse.unquote(user_id)
        print("user_id: ", user_id, "prompt_txt: ", prompt_txt)
        if not prompt_txt:
            raise ValueError("Invalid request. The path parameter 'prompt_txt' is missing")

        # read text file
        with open("prompt.txt", "r") as f:
            system_context = f.read()

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.0,
            messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": prompt_txt+'\n{"words":{"en":["'+prompt_txt+'"],"jp":["'}
                ]
            )
        output = '{"words":{"en":["'+prompt_txt+'"],"jp":["'+completion["choices"][0]["message"]["content"]
        # convert output to json
        output = json.loads(output)

        resp = {"description": "success", "input": str(prompt_txt), 
                "output": str(output)}
        print("input: ", prompt_txt, "output: ", output)

        status_code = 200
    except ValueError as e:
        status_code = 400
        resp = {"description": f"Bad request. {str(e)}"}
    except Exception as e:
        status_code = 500
        resp = {"description": str(e)}
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(resp, cls=DecimalEncoder)
    }

# http GET "${ENDPOINT_URL}/user/username/en2jp/proof of concept"
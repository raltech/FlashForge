import json, os, uuid, decimal
import openai
import urllib.parse
import time
import ast
import boto3

# load openai api key from .secret
with open(".secret", "r") as f:
    api_key = f.read()

# setup openai api key
openai.api_key = api_key
os.environ["OPENAI_API_KEY"] = api_key
os.environ["TRANSFORMERS_CACHE"] = "/tmp"

# initialize boto3 resources
ddb = boto3.resource("dynamodb")
user_table_name = ddb.Table(os.environ["FF_USER_TABLE_NAME"])

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
    API handler for GET /user/{user_id}/en2jp/word/{word}
    """
    
    try:
        path_params = event.get("pathParameters", {})
        word = path_params.get("word", "")
        user_id = path_params.get("user_id", "")
        word = urllib.parse.unquote(word)
        user_id = urllib.parse.unquote(user_id)
        print("user_id: ", user_id, "word: ", word)
        if not word:
            raise ValueError("Invalid request. The path parameter 'word' is missing")

        # check if user exists
        response = user_table_name.get_item(
            Key={
                "user_id": user_id
            }
        )
        if "Item" not in response:
            raise ValueError(f"User '{user_id}' not found")
        # read text file
        with open("prompt.txt", "r") as f:
            system_context = f.read()
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.0,
            messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": str(["aufstehen"])},
                    {"role": "assistant","content": str(["stand up", "get up", "rise"])},
                    {"role": "user","content": str(["sehnen"])},
                    {"role": "assistant","content": str(["long for", "yearn for", "pine for"])},
                    {"role": "user","content": str(["Geschwindigkeitsbegrenzung"])},
                    {"role": "assistant","content": str(["speed limit", "velocity restriction"])},
                    {"role": "user","content": str(["Betriebswirtschaftslehre"])},
                    {"role": "assistant","content": str(["business administration", "management studies"])},
                    {"role": "user","content": str(["Erinnerungsvermögen"])},
                    {"role": "assistant","content": str(["memory", "recollection", "remembrance"])},
                    {"role": "user","content": str(["Abrechnung"])},
                    {"role": "assistant","content": str(["settlement", "billing", "accounting", "reckoning", "invoice"])},
                    {"role": "user","content": str(["nichtexistiert"])},
                    {"role": "assistant","content": str(["ERROR: No translation found for nichtexistiert"])},
                    {"role": "user","content": word},
                ]
            )
        output = completion["choices"][0]["message"]["content"]

        # convert output to json
        print("raw output: ", output)
        output = ast.literal_eval(output)
        print("json output: ", output)

        # if json contains "error", raise ValueError
        if "error" in output:
            raise ValueError(output["error"])

        resp = {"description": "success", "input": str(word), 
                "output": output}
        print("input: ", word, "output: ", output)

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

# http GET "${ENDPOINT_URL}/user/114514/en2jp/word/behave"
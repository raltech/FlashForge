import json, os, uuid, decimal
import openai
import urllib.parse
import ast

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
    API handler for GET /user/{user_id}/en2jp_sentence/difficulty/{difficulty}/context/{context}
    """
    
    try:
        path_params = event.get("pathParameters", {})
        difficulty = path_params.get("difficulty", "")
        context = path_params.get("context", "")
        difficulty = urllib.parse.unquote(difficulty)
        context = urllib.parse.unquote(context)
        print("difficulty: ", difficulty , "context: ", context)

        # read text file
        with open("prompt.txt", "r") as f:
            system_context = f.read()

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.7,
            messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": '\ncontext:' + context + '\ndifficulty:' + difficulty + '\noutput:'}
                ]
            )
        output = completion["choices"][0]["message"]["content"]

        # convert output to json
        print("raw output: ", output)
        output = json.loads(output)
        print("json output: ", output)

        # if json contains "error", raise ValueError
        if "error" in output:
            raise ValueError(output["error"])

        resp = {"description": "success", "context": context, "difficulty": difficulty, "output": output}

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
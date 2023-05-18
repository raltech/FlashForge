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
        start = time.time()
        path_params = event.get("pathParameters", {})
        word = path_params.get("word", "")
        user_id = path_params.get("user_id", "")
        word = urllib.parse.unquote(word)
        user_id = urllib.parse.unquote(user_id)
        print("user_id: ", user_id, "word: ", word)
        if not word:
            raise ValueError("Invalid request. The path parameter 'word' is missing")
        print("1: time elapsed: ", time.time() - start)

        # check if user exists
        response = user_table_name.get_item(
            Key={
                "user_id": user_id
            }
        )
        if "Item" not in response:
            raise ValueError(f"User '{user_id}' not found")

        start = time.time()
        # read text file
        with open("prompt.txt", "r") as f:
            system_context = f.read()
        print("2: time elapsed: ", time.time() - start)

        start = time.time()
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.0,
            messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": "rise to one's feet"},
                    {"role": "assistant", "content": '["立ち上がる"]'},
                    {"role": "user", "content": "corroborate"},
                    {"role": "assistant", "content": '["裏付ける","確証する"]'},
                    {"role": "user", "content": "initialize"},
                    {"role": "assistant", "content": '["初期化する","初期設定する"]'},
                    {"role": "user", "content": "proof of concept"},
                    {"role": "assistant", "content": '["概念実証"]'},
                    {"role": "user", "content": "long to"},
                    {"role": "assistant", "content": '["...したいと思う","...を望む"]'},
                    {"role": "user", "content": "be in charge of"},
                    {"role": "assistant", "content": '["...を担当している","...を管理している"]'},
                    {"role": "user", "content": "bazinga"},
                    {"role": "assistant", "content": '["バジンガ"]'},
                    {"role": "user", "content": "jiszap"},
                    {"role": "assistant", "content": '["ERROR: No translation found for jiszap"]'},
                    {"role": "user", "content": word}
                ]
            )
        print("3: time elapsed: ", time.time() - start)

        start = time.time()
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
        print("4: time elapsed: ", time.time() - start)

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
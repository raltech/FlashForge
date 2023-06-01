import json, os, uuid, decimal
import openai
import urllib.parse
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
    API handler for GET /user/{user_id}/en2jp/story/{word_diff}/{content_diff}/{grammar_diff}/{story_context}
    """
    
    try:
        path_params = event.get("pathParameters", {})
        user_id = path_params.get("user_id", "")
        word_diff = path_params.get("word_diff", "")
        content_diff = path_params.get("content_diff", "")
        grammar_diff = path_params.get("grammar_diff", "")
        story_context = path_params.get("story_context", "")


        user_id = urllib.parse.unquote(user_id)
        word_diff = urllib.parse.unquote(word_diff)
        content_diff = urllib.parse.unquote(content_diff)
        grammar_diff = urllib.parse.unquote(grammar_diff)
        story_context = urllib.parse.unquote(story_context)
        print("word_diff: ", word_diff)
        print("content_diff: ", content_diff)
        print("grammar_diff: ", grammar_diff)
        print("story_context: ", story_context)

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
            temperature=0.8,
            messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": '\n' + 'word difficulty' + word_diff + '\n' + 'content difficulty' + content_diff + '\n' + 'grammar difficulty' + grammar_diff + '\n' + 'story context:' + story_context}
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

        resp = {"description": "success", "output": output, "word_diff": word_diff, "content_diff": content_diff, "grammar_diff": grammar_diff, "story_context": story_context}

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
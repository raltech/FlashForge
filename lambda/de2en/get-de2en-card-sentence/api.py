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
    API handler for GET /user/{user_id}/en2jp/word/{word}/sentence/
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
                    {"role": "user", "content": str([["aufstehen"], ["stand up", "get up", "rise"]])},
                    {"role": "assistant", "content": str([
                        ["Sie muss jeden Morgen um sechs Uhr aufstehen.", "She has to get up every morning at six o'clock."], 
                        ["Alle mussten aufstehen, als der Richter den Raum betrat.", "Everyone had to stand up when the judge entered the room."]])},
                    {"role": "user", "content": str([["bestätigen"], ["confirm", "corroborate", "verify"]])},
                    {"role": "assistant", "content": str([
                        ["Können Sie Ihre E-Mail-Adresse bestätigen?", "Can you confirm your email address?"], 
                        ["Die Experimente bestätigen die Theorie.", "The experiments corroborate the theory."]])},
                    {"role": "user", "content": str([["initialisieren"], ["initialize", "set up", "start"]])},
                    {"role": "assistant", "content": str([
                        ["Wir müssen das System neu initialisieren.", "We need to initialize the system again."], 
                        ["Bevor wir beginnen, müssen wir die Einstellungen initialisieren.", "Before we start, we need to set up the settings."]])},
                    {"role": "user", "content": str([["sehnen"], ["long for", "yearn for", "pine for"]])},
                    {"role": "assistant", "content": str([
                        ["Er sehnt sich nach einer besseren Zukunft.", "He longs for a better future."], 
                        ["Sie sehnte sich danach, die Welt zu sehen.", "She yearned to see the world."]])},
                    {"role": "user", "content": str([["verantwortlich sein für"], ["be responsible for", "be in charge of"]])},
                    {"role": "assistant", "content": str([
                        ["Er ist verantwortlich für den gesamten Projektverlauf.", "He is responsible for the entire course of the project."], 
                        ["Als Teamleiterin bin ich für die Einhaltung der Fristen verantwortlich.", "As team leader, I'm in charge of meeting deadlines."]])},
                    {"role": "user", "content": word}
                ]
            )
        print("3: time elapsed: ", time.time() - start)

        start = time.time()
        output = completion["choices"][0]["message"]["content"]

        # convert output to json
        print("raw output: ", output)
        output = ast.literal_eval(output)
        print("literal_eval output: ", output)

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

# http GET "${ENDPOINT_URL}/user/114514/en2jp/word/[[\"behave\"], [\"振る舞う\", \"行動する\"]]/sentence"
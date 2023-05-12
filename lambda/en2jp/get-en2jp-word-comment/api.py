import json, os, uuid, decimal
import openai
import urllib.parse
import time
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
    API handler for GET /user/{user_id}/en2jp/word/{word}/comment
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
                    {"role": "user", "content": str([["obsessed"],["取り憑かれた","夢中になった","執着する"]])},
                    {"role": "assistant", "content": str([["Often used with the preposition 'with' to indicate the object of obsession (e.g., obsessed with a hobby, person, or idea)"],["しばしば、前置詞「with」と一緒に使用されます。"]])},
                    {"role": "user", "content": str([["step"],["ステップ","一歩","足音"]])},
                    {"role": "assistant", "content": str([["Often used in the phrase 'step up' or 'stepping stone'","Can be used to describe something that is a necessary but difficult or unpleasant part of a process (e.g., a stepping stone to success)"],["「Step up」や「 Stepping stone」というフレーズがしばしば使用されます。"]])},
                    {"role": "user", "content": str([["personal"],["個人的な","個人の","パーソナルな"]])},
                    {"role": "assistant", "content": str([["Often used to describe something that is related to a particular person or is specific to them (e.g., personal belongings, personal opinions), Can also be used in the phrase 'take it personally' to mean that someone is offended or upset by something that was not meant to be taken as a personal attack"],["ある特定の人に関連するものや、彼らに特有のものを表すのによく使われます。", "「take it personally」というフレーズにも使われ、個人的な攻撃として受け取るべきではないことに対して、人が攻撃されたと感じることを意味します。"]])},
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
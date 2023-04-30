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
                    {"role": "user", "content": str([["rise to one's feet"],"立ち上がる"])},
                    {"role": "assistant", "content": str([["After feeling defeated, she mentally rose to her feet and regained her confidence.","敗北感を感じた後、彼女は精神的に立ち上がり、自信を取り戻した。"],["She quickly rose to her feet when the teacher entered the room.","先生が部屋に入ったとき、彼女はすぐに立ち上がりました。"]])},
                    {"role": "user", "content": str([["corroborate"], ["裏付ける", "確証する"]])},
                    {"role": "assistant", "content": str([["The witness's testimony helped corroborate the defendant's alibi.","証人の証言が被告人のアリバイを裏付けるのに役立った。"],["The evidence found at the scene corroborates the victim's story.","現場で見つかった証拠が、被害者の話を確証する。"]])},
                    {"role": "user", "content": str([["initialize"], ["初期化する", "初期設定する"]])},
                    {"role": "assistant", "content": str([["The computer must be initialized before it can be used.","コンピューターを使用する前に初期化する必要があります。"],["The program was initialized with the default settings.","プログラムはデフォルトの設定で初期化されました。"]])},
                    {"role": "user", "content": str([["long to"], ["...したいと思う", "...を望む"]])},
                    {"role": "assistant", "content": str([["I long to see my family again.","家族に再び会いたいと切望しています。"],["She longed to be free of her responsibilities.","彼女は自分の責任から自由になりたいと望んでいました。"]])},
                    {"role": "user", "content": str([["be in charge of"], ["...を担当している", "...を管理している"]])},
                    {"role": "assistant", "content": str([["The manager is in charge of the sales department.","マネージャーは営業部を担当しています。"],["Who is in charge of the project?","プロジェクトの責任者は誰ですか？"]])},
                    {"role": "user", "content": str([["bazinga"], ["バジンガ"]])},
                    {"role": "assistant", "content": str([["After successfully pulling off the prank, John turned to his friends and triumphantly exclaimed, 'Bazinga!'"],["ジョンがいたずらに成功した後、友達に向かって得意げに叫んだ、「バジンガ！」"]])},
                    {"role": "user", "content": word}
                ]
            )
        print("3: time elapsed: ", time.time() - start)

        start = time.time()
        output = completion["choices"][0]["message"]["content"]

        # convert output to json
        print("raw output: ", output)
        output = ast.literal_eval(output)
        # output = json.loads(output)
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

# http GET "${ENDPOINT_URL}/user/114514/en2jp/word/'[[\"behave\"],[\"ふるまう\"]]'/sentence"
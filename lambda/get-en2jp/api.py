import json, os, uuid, decimal
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
import openai


# initialize boto3 resources
s3 = boto3.resource("s3")
ddb = boto3.resource("dynamodb")
bucket_name = os.environ["FF_BUCKET_NAME"]
table_name = ddb.Table(os.environ["FF_TABLE_NAME"])

# setup openai api key
openai.api_key = "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"
os.environ["OPENAI_API_KEY"] = "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"
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
        print("user_id: ", user_id, "prompt_txt: ", prompt_txt)
        if not prompt_txt:
            raise ValueError("Invalid request. The path parameter 'prompt_txt' is missing")

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                    {"role": "system", "content": """与えられた日本語に対応する英単語を複数個出力し、それらを使った例文を日本語訳とともに出力してください。スラングなど若者が使う言葉にも対応すること。
            見る
            see, watch, look\n
            I can see the mountains from my window. (私は窓から山を見ることができます。)\n
            Let's watch a movie tonight. (今晩映画を見ましょう。)\n
            She looked at me and smiled. (彼女は私を見て笑顔を見せた。)\n

            食べる
            eat, consume, dine\n
            I usually eat breakfast at 7 am. (私は普段、朝7時に朝食を食べます。)\n
            He consumes a lot of caffeine every day. (彼は毎日たくさんのカフェインを摂取します。)\n
            Let's dine at that new restaurant tonight. (今晩はあの新しいレストランで食事しましょう。)\n

            美しい
            beautiful, gorgeous, lovely\n
            The sunset was beautiful. (日没が美しかった。)\n
            She looked gorgeous in her new dress. (彼女は新しいドレスで美しかった。)\n
            The city was surrounded by lovely scenery. (この街は素敵な風景に囲まれていました。)\n

            太陽
            sun, solar\n
            The sun was shining brightly. (太陽が明るく輝いていました。)\n
            Solar panels are used to generate electricity. (太陽光パネルは電気を生成するために使われます。)\n


            印象的な
            impressive, striking, memorable\n
            The architecture of the building was impressive. (建物の建築様式は印象的だった。)\n
            The performance was striking. (パフォーマンスは印象的だった。)\n
            The view was memorable. (景色は覚えに残るものだった。)\n"""},


                    {"role": "user", "content": "棚から牡丹餅"},
                ]
            )
        output = completion["choices"][0]["message"]["content"]

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
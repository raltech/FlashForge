import json, os, uuid, decimal
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
import urllib.parse


# initialize boto3 resources
s3 = boto3.resource("s3")
ddb = boto3.resource("dynamodb")
bucket_name = os.environ["FF_BUCKET_NAME"]
card_table_name = ddb.Table(os.environ["FF_CARD_TABLE_NAME"])
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
    API handler for GET /user/{user_id}/get_user_cards
    """
    
    try:
        # get path parameters
        path_params = event.get("pathParameters", {})
        user_id = path_params.get("user_id", "")

        # decode url encoded parameters
        user_id = urllib.parse.unquote(user_id)

        # validate parameters
        if not user_id:
            raise ValueError("Invalid request. The path parameter 'user_id' is missing")
        
        # get item from dynamodb
        response = card_table_name.query(
            KeyConditionExpression=Key("user_id").eq(user_id)
        )
        
        # get order of cards from user table
        user_response = user_table_name.get_item(
            Key={
                "user_id": user_id
            }
        )
        user_item = user_response.get("Item", {})
        card_order = user_item.get("card_order", [])

        # # sort cards by order
        # sorted_cards = []
        # for card_id in card_order:
        #     for card in response["Items"]:
        #         if card["card_id"] == card_id:
        #             sorted_cards.append(card)
        #             break

        # # set response
        # response["Items"] = sorted_cards

        # return response
        resp = {"description": "success", "data": response["Items"], "card_order": card_order}

        # set status code
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

# http GET "${ENDPOINT_URL}/user/user01/get_user_cards"
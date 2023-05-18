import json, os, uuid, decimal
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
import urllib.parse


# initialize boto3 resources
s3 = boto3.resource("s3")
ddb = boto3.resource("dynamodb")
bucket_name = os.environ["FF_BUCKET_NAME"]
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
    API handler for DELETE /user/{user_id}/lang_pair/{lang_pair}/{card_id}
    """
    
    try:
        # get path parameters
        path_params = event.get("pathParameters", {})
        user_id = path_params.get("user_id", "")
        card_id = path_params.get("card_id", "")
        pair = path_params.get("lang_pair", "")

        # decode url encoded parameters
        user_id = urllib.parse.unquote(user_id)
        card_id = urllib.parse.unquote(card_id)
        pair = urllib.parse.unquote(pair)

        # validate parameters
        if not user_id:
            raise ValueError("Invalid request. The path parameter 'user_id' is missing")
        if not card_id:
            raise ValueError("Invalid request. The path parameter 'card_id' is missing")
        
        # check if user exists
        response = user_table_name.get_item(
            Key={
                "user_id": user_id
            }
        )
        if "Item" not in response:
            raise ValueError(f"User '{user_id}' not found")
        
        if pair == "en2jp":
            card_table_name = ddb.Table(os.environ["EN2JP_CARD_TABLE_NAME"])
        else:
            card_table_name = ddb.Table(os.environ["FF_CARD_TABLE_NAME"])
        
        # check if card exists
        response = card_table_name.get_item(
            Key={
                "user_id": user_id,
                "card_id": card_id
            }
        )
        if "Item" not in response:
            raise ValueError(f"Card '{card_id}' not found")
        
        # delete card
        card_table_name.delete_item(
            Key={
                "user_id": user_id,
                "card_id": card_id
            }
        )

        # update order entry in user table
        # get order of cards from user table
        user_response = user_table_name.get_item(
            Key={
                "user_id": user_id
            }
        )
        user_item = user_response.get("Item", {})
        card_order = user_item.get("card_order", [])
        # remove card_id from card_order
        card_order.remove(card_id)
        # update card_order in user table
        user_table_name.update_item(
            Key={
                "user_id": user_id
            },
            UpdateExpression="set card_order = :card_order, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":card_order": card_order,
                ":updated_at": datetime.now(timezone.utc).isoformat()
            }
        )

        # return response
        resp = {"description": f"Card '{card_id}' deleted successfully"}

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

# http DELETE "${ENDPOINT_URL}/user/user01/123456"
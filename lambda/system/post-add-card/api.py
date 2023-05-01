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
    API handler for POST /user/{user_id}/add_card/{card_id}/{card_detail}
    """
    
    try:
        # get path parameters
        path_params = event.get("pathParameters", {})
        user_id = path_params.get("user_id", "")
        card_id = path_params.get("card_id", "")
        card_detail = path_params.get("card_detail", "")

        # decode url encoded parameters
        user_id = urllib.parse.unquote(user_id)
        card_id = urllib.parse.unquote(card_id)
        card_detail = urllib.parse.unquote(card_detail)

        # convert card_detail to json
        card_detail = json.loads(card_detail)

        # validate parameters
        if not user_id:
            raise ValueError("Invalid request. The path parameter 'user_id' is missing")
        if not card_id:
            raise ValueError("Invalid request. The path parameter 'card_id' is missing")
        if not card_detail:
            raise ValueError("Invalid request. The path parameter 'card_detail' is missing")
        
        # check if user exists
        response = user_table_name.get_item(
            Key={
                "user_id": user_id
            }
        )
        if "Item" not in response:
            raise ValueError(f"The user '{user_id}' does not exist")
        else:
            # get user card_order
            card_order = response["Item"]["card_order"]
        
        # check if card already exists
        response = card_table_name.get_item(
            Key={
                "user_id": user_id,
                "card_id": card_id
            }
        )

        if "Item" in response:
            # update card_detail
            current_time = datetime.now(timezone.utc).isoformat()
            card_table_name.update_item(
                Key={
                    "user_id": user_id,
                    "card_id": card_id
                },
                UpdateExpression="set card_detail = :card_detail, updated_at = :updated_at",
                ExpressionAttributeValues={
                    ":card_detail": card_detail,
                    ":updated_at": current_time
                }
            )
        else:
            # add new item to dynamodb
            current_time = datetime.now(timezone.utc).isoformat()
            card_table_name.put_item(
                Item={
                    "user_id": user_id,
                    "card_id": card_id,
                    "card_detail": card_detail,
                    "created_at": current_time,
                    "updated_at": current_time
                }
            )

            # add card_id to user card_order
            card_order.append(card_id)
            user_table_name.update_item(
                Key={
                    "user_id": user_id
                },
                UpdateExpression="set card_order = :card_order, updated_at = :updated_at",
                ExpressionAttributeValues={
                    ":card_order": card_order,
                    ":updated_at": current_time
                }
            )

        # return response
        resp = {"description": "success", "card_order": card_order}

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

# http POST "${ENDPOINT_URL}/user/user01/add_card/123456/{\"words\":{\"en\":[\"see\",\"watch\",\"look\"],\"jp\":[\"見る\"]},\"sentences\":{\"en\":[\"I can see the mountains from my window.\",\"Let's watch a movie tonight.\",\"She looked at me and smiled.\"],\"jp\":[\"私は窓から山を見ることができます。\",\"今晩映画を見ましょう。\",\"彼女は私を見て笑顔を見せた。\"]}}"
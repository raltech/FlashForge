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
    API handler for POST /user/{user_id}/user_name/{user_name}
    """
    
    try:
        # get path parameters
        path_params = event.get("pathParameters", {})
        user_id = path_params.get("user_id", "")
        user_name = path_params.get("user_name", "")

        # decode url encoded parameters
        user_id = urllib.parse.unquote(user_id)
        user_name = urllib.parse.unquote(user_name)

        # validate parameters
        if not user_id:
            raise ValueError("Invalid request. The path parameter 'user_id' is missing")
        if not user_name:
            raise ValueError("Invalid request. The path parameter 'user_name' is missing")
        
        # check if user exists
        response = user_table_name.get_item(
            Key={
                "user_id": user_id
            }
        )
        if "Item" not in response:
            # create user
            print(f"The user '{user_id}' does not exist. Creating user...")
            current_time = datetime.now(timezone.utc).isoformat()
            user_table_name.put_item(
                Item={
                    "user_id": user_id,
                    "user_name": user_name,
                    "card_order": [],
                    "created_at": current_time,
                    "updated_at": current_time
                }
            )
            resp = {"description": "successful", "message": "user created"}
            status_code = 200
        else:
            resp = resp = {"description": "unsuccessful", "message": "user already exists"}
            status_code = 400
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

# http POST "${ENDPOINT_URL}/user/123456/user_name/Hayato%20Nakamura"
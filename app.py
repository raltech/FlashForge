from typing_extensions import runtime
from aws_cdk import (
    core,
    aws_dynamodb as ddb,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_lambda as _lambda,
    aws_lambda_python as python_lambda,
    aws_ssm as ssm,
    aws_apigateway as apigw,
    aws_iam as _iam,
    aws_events as events,
    aws_events_targets as targets,
)
import os

class FlashForge(core.Stack):

    def __init__(self, scope: core.App, name: str, **kwargs) -> None:
        super().__init__(scope, name, **kwargs)

        # define dynamoDB for storing chat history
        ff_table = ddb.Table(
            self, "FF_Table",
            partition_key = ddb.Attribute(
                name="item_id", 
                type=ddb.AttributeType.STRING
            ),
            billing_mode = ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy = core.RemovalPolicy.DESTROY
        )

        # define s3 bucket for temporary storage (store reward distribution)
        bucket = s3.Bucket(
            self, "FF_Bucket",
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # define common params for lambda funcs
        common_params = {
            # "runtime": _lambda.Runtime.PYTHON_3_8,
            "environment": {
                "FF_TABLE_NAME": ff_table.table_name,
                "FF_BUCKET_NAME": bucket.bucket_name,
            }
        }

        # define lambda functions
        get_jp2en_lambda = _lambda.DockerImageFunction(
            self, "GETJP2EN",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/get-jp2en"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params) 
        get_en2jp_lambda = _lambda.DockerImageFunction(
            self, "GETEN2JP",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/get-en2jp"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params) 

        # grant permission
        get_jp2en_lambda.add_to_role_policy(
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["*"],
                resources=["*"],
            )
        )
        get_en2jp_lambda.add_to_role_policy(
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["*"],
                resources=["*"],
            )
        )

        # Grant table permissions to lambda functions to table
        ff_table.grant_read_write_data(get_jp2en_lambda)
        ff_table.grant_read_write_data(get_en2jp_lambda)

        # Grant bucket permissions to lambda functions
        bucket.grant_read_write(get_jp2en_lambda)
        bucket.grant_read_write(get_en2jp_lambda)

        # define API Gateway
        api = apigw.RestApi(
            self, "MULTIONAPI",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            )
        )

        # Link API calls to lambda functions
        user = api.root.add_resource("user")
        user_api = user.add_resource("{user_id}")
        jp2en_prompt = user_api.add_resource("jp2en")
        jp2en_prompt_api = jp2en_prompt.add_resource("{prompt_txt}")
        jp2en_prompt_api.add_method(
            "GET",
            apigw.LambdaIntegration(get_jp2en_lambda)
        )
        en2jp_prompt = user_api.add_resource("en2jp")
        en2jp_prompt_api = en2jp_prompt.add_resource("{prompt_txt}")
        en2jp_prompt_api.add_method(
            "GET",
            apigw.LambdaIntegration(get_en2jp_lambda)
        )

        # store parameters in SSM
        ssm.StringParameter(
            self, "FF_TABLE_NAME",
            parameter_name="FF_TABLE_NAME",
            string_value=ff_table.table_name
        )

        # Output parameters
        core.CfnOutput(self, 'BucketName', value=bucket.bucket_name)

app = core.App()
FlashForge(
    app, "FlashForge",
    env={
        "region": os.environ["CDK_DEFAULT_REGION"],
        # "region": "us-east-1", ap-northeast-1
        "account": os.environ["CDK_DEFAULT_ACCOUNT"],
    }
)

app.synth()

"""
export ENDPOINT_URL=https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/prod
http GET "${ENDPOINT_URL}/prompt/thisisatest"
"""
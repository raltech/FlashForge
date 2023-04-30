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

        # define dynamoDB for storing card data
        ff_card_table = ddb.Table(
            self, "FF_Card_Table",
            partition_key = ddb.Attribute(
                name="user_id", 
                type=ddb.AttributeType.STRING
            ),
            sort_key = ddb.Attribute(
                name="card_id",
                type=ddb.AttributeType.STRING
            ),
            billing_mode = ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy = core.RemovalPolicy.DESTROY
        )

        # define dynamoDB for storing user data
        ff_user_table = ddb.Table(
            self, "FF_User_Table",
            partition_key = ddb.Attribute(
                name="user_id",
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
                "FF_CARD_TABLE_NAME": ff_card_table.table_name,
                "FF_USER_TABLE_NAME": ff_user_table.table_name,
                "FF_BUCKET_NAME": bucket.bucket_name,
            }
        }

        # define lambda functions for en2jp (base is jp, target is en)
        get_en2jp_word_lambda = _lambda.DockerImageFunction(
            self, "GET-EN2JP-WORD",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/en2jp/get-en2jp-word"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params) 
        get_en2jp_word_sentence_lambda = _lambda.DockerImageFunction(
            self, "GET-EN2JP-WORD-SENTENCE",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/en2jp/get-en2jp-word-sentence"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        get_en2jp_sentence_lambda = _lambda.DockerImageFunction(
            self, "GET-EN2JP-SENTENCE",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/en2jp/get-en2jp-sentence"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        
        # define lambda functions for system
        post_add_card_lambda = _lambda.DockerImageFunction(
            self, "POST-ADD-CARD",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/system/post-add-card"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        get_user_cards_lambda = _lambda.DockerImageFunction(
            self, "GET-USER-CARDS",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/system/get-user-cards"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        delete_user_card_lambda = _lambda.DockerImageFunction(
            self, "DELETE-USER-CARD",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/system/delete-user-card"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        post_add_user_lambda = _lambda.DockerImageFunction(
            self, "POST-ADD-USER",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/system/post-add-user"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        get_user_name_lambda = _lambda.DockerImageFunction(
            self, "GET-USER-NAME",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/system/get-user-name"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)

        # grant permission to lambda functions to access dynamoDB
        post_add_card_lambda.add_to_role_policy(
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["*"],
                resources=["*"],
            )
        )
        get_user_cards_lambda.add_to_role_policy(
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["*"],
                resources=["*"],
            )
        )
        delete_user_card_lambda.add_to_role_policy(
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["*"],
                resources=["*"],
            )
        )
        post_add_user_lambda.add_to_role_policy(
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["*"],
                resources=["*"],
            )
        )
        get_user_name_lambda.add_to_role_policy(
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["*"],
                resources=["*"],
            )
        )

        # Grant table permissions to lambda functions to card table
        ff_card_table.grant_read_write_data(post_add_card_lambda)
        ff_card_table.grant_read_write_data(get_user_cards_lambda)
        ff_card_table.grant_read_write_data(delete_user_card_lambda)
        ff_card_table.grant_read_write_data(post_add_user_lambda)
        ff_card_table.grant_read_write_data(get_user_name_lambda)

        # Grant table permissions to lambda functions to user table
        ff_user_table.grant_read_write_data(post_add_card_lambda)
        ff_user_table.grant_read_write_data(get_user_cards_lambda)
        ff_user_table.grant_read_write_data(delete_user_card_lambda)
        ff_user_table.grant_read_write_data(post_add_user_lambda)
        ff_user_table.grant_read_write_data(get_user_name_lambda)

        # Grant bucket permissions to lambda functions
        bucket.grant_read_write(post_add_card_lambda)
        bucket.grant_read_write(get_user_cards_lambda)
        bucket.grant_read_write(delete_user_card_lambda)
        bucket.grant_read_write(post_add_user_lambda)
        bucket.grant_read_write(get_user_name_lambda)

        # define API Gateway
        api = apigw.RestApi(
            self, "FFAPI",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            )
        )

        # Link API calls to lambda functions
        user = api.root.add_resource("user")
        user_api = user.add_resource("{user_id}")
        # get user cards
        get_user_cards = user_api.add_resource("get_user_cards")
        get_user_cards.add_method(
            "GET",
            apigw.LambdaIntegration(get_user_cards_lambda)
        )
        # get user name
        get_user_name = user_api.add_resource("get_user_name")
        get_user_name.add_method(
            "GET",
            apigw.LambdaIntegration(get_user_name_lambda)
        )
        # delete user card
        delete_user_card_api = user_api.add_resource("{card_id}")
        delete_user_card_api.add_method(
            "DELETE",
            apigw.LambdaIntegration(delete_user_card_lambda)
        )
        # add user
        add_user_api = user_api.add_resource("user_name")
        add_user_name_api = add_user_api.add_resource("{user_name}")
        add_user_name_api.add_method(
            "POST",
            apigw.LambdaIntegration(post_add_user_lambda)
        )
        # add card
        add_card = user_api.add_resource("add_card")
        add_card_api = add_card.add_resource("{card_id}")
        add_card_detail_api = add_card_api.add_resource("{card_detail}")
        add_card_detail_api.add_method(
            "POST",
            apigw.LambdaIntegration(post_add_card_lambda)
        )

        """Base Japanese -> Target English"""
        # word completion
        en2jp = user_api.add_resource("en2jp")

        en2jp_word = en2jp.add_resource("word")
        en2jp_word_api = en2jp_word.add_resource("{word}")
        en2jp_word_api.add_method(
            "GET",
            apigw.LambdaIntegration(get_en2jp_word_lambda)
        )
        # sentence completion
        en2jp_word_sentence_api = en2jp_word_api.add_resource("sentence")
        en2jp_word_sentence_api.add_method(
            "GET",
            apigw.LambdaIntegration(get_en2jp_word_sentence_lambda)
        )
        # generate en2jp sentences
        en2jp_sentence = en2jp.add_resource("sentence")
        en2jp_sentence_diff = en2jp_sentence.add_resource("difficulty")
        en2jp_sentence_diff_api = en2jp_sentence_diff.add_resource("{difficulty}")
        en2jp_sentence_context = en2jp_sentence_diff_api.add_resource("context")
        en2jp_sentence_context_api = en2jp_sentence_context.add_resource("{context}")
        en2jp_sentence_context_api.add_method(
            "GET",
            apigw.LambdaIntegration(get_en2jp_sentence_lambda)
        )

        # store parameters in SSM
        ssm.StringParameter(
            self, "FF_CARD_TABLE_NAME",
            parameter_name="FF_CARD_TABLE_NAME",
            string_value=ff_card_table.table_name
        )
        ssm.StringParameter(
            self, "FF_USER_TABLE_NAME",
            parameter_name="FF_USER_TABLE_NAME",
            string_value=ff_user_table.table_name
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
export ENDPOINT_URL=https://6in8tizdac.execute-api.us-east-1.amazonaws.com/prod/
http GET "${ENDPOINT_URL}/user/username/jp2en/概念実証"
"""
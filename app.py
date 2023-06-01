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
        en2jp_card_table = ddb.Table(
            self, "EN2JP_Card_Table",
            partition_key = ddb.Attribute(
                name="user_id",
                type=ddb.AttributeType.STRING
            ),
            sort_key = ddb.Attribute(
                name="card_id",
                type=ddb.AttributeType.STRING
            ),
            billing_mode = ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy = core.RemovalPolicy.RETAIN
        )
        de2en_card_table = ddb.Table(
            self, "DE2EN_Card_Table",
            partition_key = ddb.Attribute(
                name="user_id",
                type=ddb.AttributeType.STRING
            ),
            sort_key = ddb.Attribute(
                name="card_id",
                type=ddb.AttributeType.STRING
            ),
            billing_mode = ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy = core.RemovalPolicy.RETAIN
        )

        # define dynamoDB for storing user data
        ff_user_table = ddb.Table(
            self, "FF_User_Table",
            partition_key = ddb.Attribute(
                name="user_id",
                type=ddb.AttributeType.STRING
            ),
            billing_mode = ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy = core.RemovalPolicy.RETAIN
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
                "EN2JP_CARD_TABLE_NAME": en2jp_card_table.table_name,
                "DE2EN_CARD_TABLE_NAME": de2en_card_table.table_name,
                "FF_USER_TABLE_NAME": ff_user_table.table_name,
                "FF_BUCKET_NAME": bucket.bucket_name,
            }
        }

        # define lambda functions for en2jp (base is jp, target is en)
        get_en2jp_card_word_lambda = _lambda.DockerImageFunction(
            self, "GET-EN2JP-CARD-WORD",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/en2jp/get-en2jp-card-word"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params) 
        get_en2jp_card_sentence_lambda = _lambda.DockerImageFunction(
            self, "GET-EN2JP-CARD-SENTENCE",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/en2jp/get-en2jp-card-sentence"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        get_en2jp_card_comment_lambda = _lambda.DockerImageFunction(
            self, "GET-EN2JP-CARD-COMMENT",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/en2jp/get-en2jp-card-comment"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        get_en2jp_story_lambda = _lambda.DockerImageFunction(
            self, "GET-EN2JP-STORY",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/en2jp/get-en2jp-story"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        
        # define lambda functions for de2en (base is en, target is de)
        get_de2en_card_word_lambda = _lambda.DockerImageFunction(
            self, "GET-DE2EN-CARD-WORD",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/de2en/get-de2en-card-word"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params) 
        get_de2en_card_sentence_lambda = _lambda.DockerImageFunction(
            self, "GET-DE2EN-CARD-SENTENCE",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/de2en/get-de2en-card-sentence"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        get_de2en_card_comment_lambda = _lambda.DockerImageFunction(
            self, "GET-DE2EN-CARD-COMMENT",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/de2en/get-de2en-card-comment"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        get_de2en_story_lambda = _lambda.DockerImageFunction(
            self, "GET-DE2EN-STORY",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/de2en/get-de2en-story"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        
        # define lambda functions for system
        post_card_lambda = _lambda.DockerImageFunction(
            self, "POST-CARD",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/system/post-card"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        get_user_cards_lambda = _lambda.DockerImageFunction(
            self, "GET-USER-CARDS",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/system/get-user-cards"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        delete_card_lambda = _lambda.DockerImageFunction(
            self, "DELETE-USER-CARD",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/system/delete-card"),
            memory_size=256,
            timeout=core.Duration.seconds(60),
            **common_params)
        post_user_lambda = _lambda.DockerImageFunction(
            self, "POST-USER",
            code=_lambda.DockerImageCode.from_image_asset("./lambda/system/post-user"),
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
        post_card_lambda.add_to_role_policy(
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
        delete_card_lambda.add_to_role_policy(
            _iam.PolicyStatement(
                effect=_iam.Effect.ALLOW,
                actions=["*"],
                resources=["*"],
            )
        )
        post_user_lambda.add_to_role_policy(
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

        # Grant table permissions to lambda functions
        # en2jp
        en2jp_card_table.grant_read_write_data(post_card_lambda)
        en2jp_card_table.grant_read_write_data(get_user_cards_lambda)
        en2jp_card_table.grant_read_write_data(delete_card_lambda)
        # de2en
        de2en_card_table.grant_read_write_data(post_card_lambda)
        de2en_card_table.grant_read_write_data(get_user_cards_lambda)
        de2en_card_table.grant_read_write_data(delete_card_lambda)

        # Grant table permissions to lambda functions to user table
        ff_user_table.grant_read_write_data(post_card_lambda)
        ff_user_table.grant_read_write_data(get_user_cards_lambda)
        ff_user_table.grant_read_write_data(delete_card_lambda)
        ff_user_table.grant_read_write_data(post_user_lambda)
        ff_user_table.grant_read_write_data(get_user_name_lambda)
        # en2jp
        ff_user_table.grant_read_write_data(get_en2jp_card_word_lambda)
        ff_user_table.grant_read_write_data(get_en2jp_card_sentence_lambda)
        ff_user_table.grant_read_write_data(get_en2jp_card_comment_lambda)
        ff_user_table.grant_read_write_data(get_en2jp_story_lambda)
        # de2en
        ff_user_table.grant_read_write_data(get_de2en_card_word_lambda)
        ff_user_table.grant_read_write_data(get_de2en_card_sentence_lambda)
        ff_user_table.grant_read_write_data(get_de2en_card_comment_lambda)
        ff_user_table.grant_read_write_data(get_de2en_story_lambda)

        # Grant bucket permissions to lambda functions
        # bucket.grant_read_write(post_card_lambda)
        # bucket.grant_read_write(get_user_cards_lambda)
        # bucket.grant_read_write(delete_card_lambda)
        # bucket.grant_read_write(post_user_lambda)
        # bucket.grant_read_write(get_user_name_lambda)

        # define API Gateway
        api = apigw.RestApi(
            self, "FFAPI",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            )
        )

        # Set up API Gateway for lambda functions
        user = api.root.add_resource("{user_id}")

        # post user
        post_user = user.add_resource("post_user")
        post_user_name = post_user.add_resource("{user_name}")
        post_user_name.add_method("POST", apigw.LambdaIntegration(post_user_lambda))
        # user.add_resource("post_user").add_resource("{user_name}").add_method("POST", apigw.LambdaIntegration(post_user_lambda))

        # get user name
        get_user_name = user.add_resource("get_user_name")
        get_user_name.add_method("GET", apigw.LambdaIntegration(get_user_name_lambda))

        # get user cards
        get_user_cards = user.add_resource("get_user_cards")
        # get_user_cards_base_lang = get_user_cards.add_resource("base_lang")
        get_user_cards_base_lang = get_user_cards.add_resource("{base_lang}")
        # get_user_cards_target_lang = get_user_cards_base_lang.add_resource("target_lang")
        get_user_cards_target_lang = get_user_cards_base_lang.add_resource("{target_lang}")
        get_user_cards_target_lang.add_method("GET", apigw.LambdaIntegration(get_user_cards_lambda))

        # post card
        post_card = user.add_resource("post_card")
        post_card_base_lang = post_card.add_resource("{base_lang}")
        post_card_target_lang = post_card_base_lang.add_resource("{target_lang}")
        post_card_id = post_card_target_lang.add_resource("{card_id}")
        post_card_detail = post_card_id.add_resource("{card_detail}")
        post_card_detail.add_method("POST", apigw.LambdaIntegration(post_card_lambda))

        # delete card
        delete_card = user.add_resource("delete_card")
        delete_card_base_lang = delete_card.add_resource("{base_lang}")
        delete_card_target_lang = delete_card_base_lang.add_resource("{target_lang}")
        delete_card_id = delete_card_target_lang.add_resource("{card_id}")
        delete_card_id.add_method("DELETE", apigw.LambdaIntegration(delete_card_lambda))

        ## en2jp
        # get en2jp card word
        en2jp = user.add_resource("en2jp")
        en2jp_card = en2jp.add_resource("card")
        en2jp_card_word = en2jp_card.add_resource("{word}")
        en2jp_card_word.add_method("GET", apigw.LambdaIntegration(get_en2jp_card_word_lambda))
        # get en2jp card sentence
        en2jp_card_sentence = en2jp_card_word.add_resource("sentence")
        en2jp_card_sentence.add_method("GET", apigw.LambdaIntegration(get_en2jp_card_sentence_lambda))
        # get en2jp card comment
        en2jp_card_comment = en2jp_card_word.add_resource("comment")
        en2jp_card_comment.add_method("GET", apigw.LambdaIntegration(get_en2jp_card_comment_lambda))
        # get en2jp story
        en2jp_story = en2jp.add_resource("story")
        en2jp_story_context = en2jp_story.add_resource("{word_diff}").add_resource("{content_diff}")\
                                 .add_resource("{grammar_diff}").add_resource("{story_context}")
        en2jp_story_context.add_method("GET", apigw.LambdaIntegration(get_en2jp_story_lambda))

        ## de2en
        # get de2en card word
        de2en = user.add_resource("de2en")
        de2en_card = de2en.add_resource("card")
        de2en_card_word = de2en_card.add_resource("{word}")
        de2en_card_word.add_method("GET", apigw.LambdaIntegration(get_de2en_card_word_lambda))
        # get de2en card sentence
        de2en_card_sentence = de2en_card_word.add_resource("sentence")
        de2en_card_sentence.add_method("GET", apigw.LambdaIntegration(get_de2en_card_sentence_lambda))
        # get de2en card comment
        de2en_card_comment = de2en_card_word.add_resource("comment")
        de2en_card_comment.add_method("GET", apigw.LambdaIntegration(get_de2en_card_comment_lambda))
        # get de2en story
        de2en_story = de2en.add_resource("story")
        de2en_story_context = de2en_story.add_resource("{word_diff}").add_resource("{content_diff}")\
                                 .add_resource("{grammar_diff}").add_resource("{story_context}")
        de2en_story_context.add_method("GET", apigw.LambdaIntegration(get_de2en_story_lambda))

        # store parameters in SSM
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
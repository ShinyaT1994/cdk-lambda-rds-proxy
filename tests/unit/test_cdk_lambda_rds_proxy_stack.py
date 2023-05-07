import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_lambda_rds_proxy.cdk_lambda_rds_proxy_stack import CdkLambdaRdsProxyStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_lambda_rds_proxy/cdk_lambda_rds_proxy_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkLambdaRdsProxyStack(app, "cdk-lambda-rds-proxy")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })

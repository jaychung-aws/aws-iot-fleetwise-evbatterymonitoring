from aws_cdk import (
    aws_events as events,
    aws_lambda as lambda_,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_sns as sns,
    App, Duration, Stack, CfnParameter, CfnOutput, RemovalPolicy
)

from constructs import Construct


class BatteryhealthmonitoringStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fleetwise_db = CfnParameter(self, "fleetwisedatabase")

        fleetwise_table = CfnParameter(self, "fleetwisetable")

        health_monitoring_function = lambda_.Function(self, "batteryHealthMonitoring_lambda",
                                                      function_name="batteryHealthMonitoring_lambda",
                                                      runtime=lambda_.Runtime.PYTHON_3_9,
                                                      handler="batteryHealthMonitoring_lambda.handler",
                                                      code=lambda_.Code.from_asset("lambda/"),
                                                      timeout=Duration.seconds(5)
                                                      )

        boto3_latest_lambda_layer = lambda_.LayerVersion(self, "boto3latest", removal_policy=RemovalPolicy.RETAIN,
                                                         code=lambda_.Code.from_asset("lambdalibs/python.zip"),
                                                         compatible_runtimes=[lambda_.Runtime.PYTHON_3_8, lambda_.Runtime.PYTHON_3_7, lambda_.Runtime.PYTHON_3_9],
                                                         compatible_architectures=[lambda_.Architecture.X86_64])

        health_monitoring_function.add_layers(boto3_latest_lambda_layer)

        health_monitoring_function.add_permission(
            "lambdaPermission", principal=iam.ServicePrincipal("events.amazonaws.com")
        )

        health_monitoring_function.add_environment("fleetwisedatabase", fleetwise_db.value_as_string)
        health_monitoring_function.add_environment("fleetwisetable", fleetwise_table.value_as_string)

        health_monitoring_function.add_to_role_policy(iam.PolicyStatement(
            actions=["timestream:*"],
            effect=iam.Effect.ALLOW,
            resources=["*"]
        ))

        health_monitoring_function.add_to_role_policy(iam.PolicyStatement(
            actions=["sns:publish"],
            effect=iam.Effect.ALLOW,
            resources=["*"]
        ))

        health_monitoring_function.add_to_role_policy(iam.PolicyStatement(
            actions=["iotfleetwise:*"],
            effect=iam.Effect.ALLOW,
            resources=["*"]
        ))

        # events.Rule(self, "batteryHealthMonitoring_schedule",
        #             rule_name="batteryHealthMonitoring_schedule",
        #             schedule=events.Schedule.rate(Duration.hours(1)),
        #             targets=[targets.LambdaFunction(health_monitoring_function, retry_attempts=2)]
        #             )

        events.Rule(self, "batteryHealthMonitoring_schedule",
                    rule_name="batteryHealthMonitoring_schedule",
                    schedule=events.Schedule.rate(Duration.hours(1)),
                    targets=[targets.LambdaFunction(health_monitoring_function, retry_attempts=2)]
                    )

        sns_mail_address = CfnParameter(self, "batteryHealthMonitoringmail")

        fleet_operator_topic = sns.Topic(self, "batteryHealthMonitoring_topic",
                                         display_name="batteryHealthMonitoring_topic")

        health_monitoring_function.add_environment("snstopic", fleet_operator_topic.topic_arn)

        fleet_operator_subscription = sns.Subscription(self, "batteryHealthMonitoring_subscription",
                                                       topic=fleet_operator_topic,
                                                       protocol=sns.SubscriptionProtocol.EMAIL,
                                                       endpoint=sns_mail_address.value_as_string
                                                       )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value="The Name of the Lambda Function is {}.".format(health_monitoring_function.function_name),
            description="Navigate to AWS Lambda in the console to get better insights into the Lambda function."
        )

        CfnOutput(
            self,
            "SnsTopicName",
            value="The topic used to notify the Fleet Operator is {}.".format(fleet_operator_topic.topic_name),
            description="Create other subscriptions to leverage different protocols/formats for notifications."
        )

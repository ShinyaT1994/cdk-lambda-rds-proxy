from constructs import Construct
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_lambda as _lambda,
    aws_rds as rds,
    aws_secretsmanager as sm,
)


class CdkLambdaRdsProxyStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPCの作成
        vpc = ec2.Vpc(self, "MyVPC",
            max_azs=2
        )

        # RDSのセキュリティグループの作成
        rds_security_group = ec2.SecurityGroup(self, "RdsSecurityGroup",
            vpc=vpc,
            description="Allow Lambda access to RDS"
        )

        # RDSの作成
        rds_instance = rds.DatabaseInstance(self, "RDS",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_14_5),
            vpc=vpc,
            security_groups=[rds_security_group],
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL),
            allocated_storage=20,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False,
            database_name="MyDatabase",
            auto_minor_version_upgrade=True,
            multi_az=False
        )

        # Lambdaのセキュリティグループの作成
        lambda_security_group = ec2.SecurityGroup(self, "LambdaSecurityGroup",
            vpc=vpc,
            description="Allow Lambda to access RDS Proxy"
        )

        # RDS Proxyの作成
        rds_proxy = rds.DatabaseProxy(self, "RDSProxy",
            proxy_target=rds.ProxyTarget.from_instance(rds_instance),
            vpc=vpc,
            security_groups=[lambda_security_group],
            db_proxy_name="MyRDSProxy",
            debug_logging=False,
            secrets=[rds_instance.secret],
            require_tls=True
        )
        
        # psycopg2のLambda Layer
        psycopg2_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "Psycoog2Layer",
            'arn:aws:lambda:ap-northeast-1:898466741470:layer:psycopg2-py38:1'
        )
        
        # Lambda関数の作成
        lambda_function = _lambda.Function(self, "LambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="lambda_function.handler",
            code=_lambda.Code.from_asset("cdk_lambda_rds_proxy/lambda"),
            layers=[psycopg2_layer],
            vpc=vpc,
            security_groups=[lambda_security_group],
            vpc_subnets=ec2.SubnetSelection(subnets=vpc.private_subnets),
            environment={
                "DB_SECRET_ARN": rds_instance.secret.secret_arn,
                "DB_PROXY_ENDPOINT": rds_proxy.endpoint
            }
        )
    
        # RDSインスタンスとLambda関数のアクセス許可
        rds_instance.connections.allow_from(
            lambda_security_group,
            port_range=ec2.Port.tcp(5432)
        )
        rds_proxy.connections.allow_from(
            lambda_security_group,
            port_range=ec2.Port.tcp(5432)
        )
        
        # Secretへのアクセス許可
        rds_instance.secret.grant_read(lambda_function)

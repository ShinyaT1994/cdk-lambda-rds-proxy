import os
import json
import psycopg2
import boto3
from botocore.exceptions import ClientError

def get_db_credentials(secret_arn):
    secrets_manager = boto3.client("secretsmanager")
    try:
        response = secrets_manager.get_secret_value(SecretId=secret_arn)
        return json.loads(response["SecretString"])
    except ClientError as e:
        print(e)
        return None

def handler(event, context):
    secret_arn = os.environ["DB_SECRET_ARN"]
    db_proxy_endpoint = os.environ["DB_PROXY_ENDPOINT"]

    credentials = get_db_credentials(secret_arn)

    if not credentials:
        return {
            "statusCode": 500,
            "body": "Error retrieving database credentials"
        }
    
    connection_string = f"dbname={credentials['dbname']} user={credentials['username']} password={credentials['password']} host={db_proxy_endpoint} port={credentials['port']} sslmode=require"
    
    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        result = cursor.fetchone()

        return {
            "statusCode": 200,
            "body": f"Database version: {result[0]}"
        }

    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            "body": "Error connecting to the database"
        }
import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

class DynamodbReader:
    """High performance data retrival with pagination."""

    def __init__(self, table_name: str):
        self._table_name = table_name
        if not self._table_name:
            raise ValueError("DYNAMODB_TABLE_NAME not found in SSM configs.")
        self.db_resource = boto3.resource('dynamodb')
        self.table = self.db_resource.Table(self._table_name)

    def fetch_all_telemetry(self, limit=100):
        all_items = []
        try:
            response = self.table.scan(Limit=limit)
            all_items.extend(response.get('Items', []))

            while 'LastEvaluatedKey' in response:
                logger.info("Fetching next page of DynamoDB data ...")
                response = self.table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey'],
                    Limit=limit
                )
                all_items.extend(response.get('Items', []))

            logger.info(f"Successfully retrieved {len(all_items)} records from DynamoDB table: {self._table_name}")
            return all_items
        except ClientError as e:
            logger.error(f"Failed to fetch data from DynamoDB: {e.response['Error']['Message']}")
            return []

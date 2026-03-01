
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DynamodbClient:
    def __init__(self, table_name: str):
        self._table_name = table_name
        if not self._table_name:
            raise ValueError("DYNAMODB_TABLE_NAME not found in SSM configs.")
        self.db_resource = boto3.resource('dynamodb')
        self.table = self.db_resource.Table(self._table_name)

    def check_processed(self, record_id: str) -> bool:
        """Check if record already exists in DynamoDB.."""
        try:
            response = self.table.get_item(
                Key={'request_id': record_id}
            )
            if 'Item' in response:
                logger.info(f"Record {record_id} found in {self._table_name}")
                return True
            else:
                logger.info(f"Record {record_id} not found in {self._table_name}, new commit detected. Starting analysis for {record_id}")
                return False

        except ClientError as e:
            logger.error(f"Error accessing DynamoDB: {str(e)}")
            return False

    def mark_as_processed(self, record_id: str, status: str, metadata: dict, result: dict) -> bool:
        try:
            self.table.put_item(
                Item={'request_id': record_id,
                      'status': status,
                      'metadata': metadata,
                      'result': result},
                ConditionExpression='attribute_not_exists(request_id)'
            )
            logger.info(f"Successfully added record: {record_id}")
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Record {record_id} already exists.")
            else:
                logger.error(f"PutItem failed: {e}")
            return False

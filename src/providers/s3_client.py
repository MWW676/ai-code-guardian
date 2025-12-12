import os
import json
import time
import datetime
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class S3Uploader:
    def __init__(self):
        self._bucket_name = os.environ.get('AWS_S3_BUCKET')
        self.s3_client = boto3.client('s3')

    def save_report(self, report_data: dict) -> bool:
        """Save analysis report to AMS S3."""
        report_data_json = json.dumps(report_data)

        now = datetime.datetime.now()
        s3_object_key = f"reports/{now.strftime('%Y-%m-%d')}/report-{int(time.time())}.json"

        try:
            response = self.s3_client.put_object(
                Bucket=self._bucket_name,
                Key=s3_object_key,
                Body=report_data_json.encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"Successfully uploaded {s3_object_key} to {self._bucket_name}")
            logger.info(f"S3 Response:{response}")
            return True

        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            return False

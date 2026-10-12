import boto3
from botocore.exceptions import ClientError
import logging

logging.basicConfig(level=logging.INFO)


def test_aws_credentials():
    """
    Checks if boto3 can successfully assume an identity using default credentials.
    """
    try:
        # Boto3 will automatically look up the credentials chain here.
        sts_client = boto3.client('sts')

        # Calling get_caller_identity is a minimal, cheap way to verify auth.
        response = sts_client.get_caller_identity()

        print("\n✅ Credentials Test Successful!")
        print("-" * 30)
        print(f"User ARN: {response.get('Arn')}")
        print(f"Account ID: {response.get('Account')}")

    except ClientError as e:
        # If credentials are not found or are invalid, a ClientError is raised.
        error_code = e.response['Error']['Code']

        if error_code == 'InvalidClientTokenId':
            print("\n❌ FAILED: Invalid or expired credentials found.")
            print("Action: Check your Access Key ID and Secret Access Key.")

        elif error_code == 'NoCredentialsError':
            print("\n❌ FAILED: No credentials found in any standard location.")
            print("Action: Ensure ~/.aws/credentials file exists and is populated.")

        else:
            print(f"\n❌ FAILED: An unexpected AWS error occurred: {error_code}")

    except Exception as e:
        print(f"\n❌ FAILED: A non-AWS error occurred: {e}")

def test_split(s):
    print(s.split())

def solution(words, maxWidth):
    res = []
    line, length = [], 0
    i = 0

    while i < len(words):
        if length + len(line) + len(words[i]) > maxWidth:
            # Line complete
            extra_space = maxWidth - length
            spaces = extra_space // max(1, len(line) - 1)
            remainder = extra_space % max(1, len(line) - 1)

            for j in range(max(1, len(line) - 1)):
                line[j] += ' ' * spaces
                if remainder:
                    line[j] += ' '
                    remainder -= 1
            res.append(''.join(line))
            # Reset line
            line, length = [], 0

        line.append(words[i])
        length += len(words[i])
        i += 1

    # Handle last line
    last_line = ' '.join(line)
    trail_space = maxWidth - len(last_line)
    last_line += ' ' * trail_space
    res.append(last_line)
    return res

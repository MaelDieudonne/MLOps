import os
import pytest
import s3fs

from dotenv import load_dotenv


def test_s3():
    try:
        s3_endpoint = os.environ.get('AWS_S3_ENDPOINT')
        s3_key = os.environ.get("AWS_ACCESS_KEY_ID")
        s3_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
        s3_token = os.environ.get("AWS_SESSION_TOKEN")

        if not all([s3_endpoint, s3_key, s3_secret, s3_token]):
            # Fall back on the .env file
            logger.warning("s3 credentials not found in the environment, trying to load the .env file")
            try:
                load_dotenv()
                s3_endpoint = os.getenv('AWS_S3_ENDPOINT')
                s3_key = os.getenv("AWS_ACCESS_KEY_ID")
                s3_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
                s3_token = os.getenv("AWS_SESSION_TOKEN")
                logger.debug("s3 credentials loaded from .env file")
            except Exception as e:
                logger.error(f"Failed to load s3 credentials from .env file: {e}")

        fs = s3fs.S3FileSystem(
            client_kwargs={'endpoint_url': 'https://' + s3_endpoint},
            key = s3_key,
            secret = s3_secret,
            token = s3_token)
        bucket_name = 'maeldieudonne'
        destination = bucket_name + '/diffusion/'
        target_file = destination + "movies.csv"
        
        try:
            fs.put("data/sample/movies.csv", target_file, content_type="csv", encoding="utf-8")
        finally:
            if fs.exists(target_file):
                fs.rm(target_file)

    except Exception as e:
        pytest.fail(f"s3 failed: {e}")

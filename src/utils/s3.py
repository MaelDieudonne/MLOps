import os
import pandas as pd
import re
import s3fs

from datetime import datetime
from dotenv import load_dotenv
from src.utils.logger import get_backend_logger

logger = get_backend_logger()


class s3:
    def __init__(self):
        """
        Initialize s3 connection parameters
        """
        # Look for variables in the environment
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

        self.fs = s3fs.S3FileSystem(
            client_kwargs={'endpoint_url': 'https://' + s3_endpoint},
            key = s3_key,
            secret = s3_secret,
            token = s3_token)
        bucket_name = 'maeldieudonne'
        self.destination = bucket_name + '/diffusion/'

    @staticmethod
    def get_latest_local_backup(table_name):
        """
        Check if other save files are present and select the newest
        """
        backup_files = [f for f in os.listdir("data/backups") if f.startswith(table_name)]

        if not backup_files:
            logger.info(f"No local backup found for {table_name}")
            return None

        else:
            latest_backup = max(backup_files, key=lambda f: os.path.getctime(os.path.join("data/backups", f)))
            file_path = os.path.join("data/backups", latest_backup)
            return file_path


    def upload_backup(self, file_path):
        try:
            self.fs.put(file_path, self.destination, content_type="parquet", encoding="utf-8")
            os.remove(file_path)
            logger.info(f"Successfully uploaded {file_path} to {self.destination}")
        except Exception as e:
            logger.error(f"Failed uploading {file_path} to {self.destination}: {e}")

    
    def upload_covers(self, local_directory='data/covers'):
        try:
            s3_target = os.path.join(self.destination, 'covers').replace("\\", "/")

            for root, _, files in os.walk(local_directory):
                for file in files:
                    local_file = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file, local_directory)
                    s3_file = os.path.join(s3_target, relative_path).replace("\\", "/")
                    self.fs.put(local_file, s3_file)

            logger.info("Successfully synced covers to s3")
        except Exception as e:
            logger.error(f"Failed to sync covers to s3: {e}")


    def clean_backup_directory(self):
        pattern = re.compile(r"([^/]+)_(\d{8}_\d{6})\.parquet$")

        # List all files
        files = self.fs.ls(self.destination)

        # Group by table name
        table_files = {}
        for file in files:
            match = pattern.search(file)
            if match:
                table_name, timestamp = match.groups()
                if table_name not in table_files:
                    table_files[table_name] = []
                table_files[table_name].append((file, timestamp))

        files_to_delete = []
        for table_name, file_list in table_files.items():
            file_list.sort(key=lambda x: x[1], reverse=True)  # Sort by timestamp (newest first)
            old_files = file_list[3:]  # Keep only 3 newest
            files_to_delete.extend([f[0] for f in old_files])

        if not files_to_delete:
            logger.info("No files to delete")
        else:
            logger.info(f"{len(files_to_delete)} files to delete")

        try:
            for file in files_to_delete:
                logger.debug(f"Attempting to delete {file}")
                self.fs.rm(file)
                logger.info(f"Deleted {file}")
        except Exception as e:
            logger.error(f"Failed to remove files from S3: {e}")


    @staticmethod
    def extract_timestamp(file_name):
        match = re.search(r'(\d{8}_\d{6})', file_name)
        if match:
            return datetime.strptime(match.group(1), '%Y%m%d_%H%M%S')
        return None


    def load_latest_backup(self, table_name):
        # Look for a backup in S3
        try:
            all_files = [f['name'] for f in self.fs.listdir(self.destination)]
            backup_files = [f for f in all_files if f.startswith(f"{self.destination}{table_name}")]
        except Exception as e:
            logger.warning(f"Unable to access distant backup directory: {e}")

        if not backup_files:
            # Look for sample data locally
            try:
                backup = pd.read_csv(f"data/sample/{table_name}.csv")
                logger.info(f"Loading sample data for {table_name}")
                return backup
            except Exception as e:
                logger.warning(f"No distant or local backup found for {table_name}: {e}")

        else:
            file_path = max(backup_files, key=s3.extract_timestamp)
            timestamp = s3.extract_timestamp(file_path).strftime('%Y-%m-%d %H:%M:%S')
            with self.fs.open(f's3://{file_path}', 'rb') as f:
                backup = pd.read_parquet(f)
            logger.info(f"Loading distant backup for {table_name}: {timestamp}")
            return backup


    def restore_covers(self, local_directory='data/covers'):
        try:
            s3_source = os.path.join(self.destination, 'covers', '*').replace("\\", "/")
            os.makedirs(local_directory, exist_ok=True)

            self.fs.get(s3_source, local_directory, recursive=True)
            logger.info(f"Successfully restored covers from s3")
        except Exception as e:
            logger.error(f"Failed to restore covers from s3: {e}")


    def retrieve_cover(self, movie_id, local_folder = 'data/covers/'):
        """
        Retrieves a single cover image (movie_id.jpg) from the S3 bucket and copies it to data/covers/ locally.
        If retrieval fails, creates an empty blank JPEG to avoid display issues.
        """
        s3_file = os.path.join(self.destination, 'covers', f"{movie_id}.jpg").replace("\\", "/")
        os.makedirs(local_folder, exist_ok=True)
        local_file = os.path.join(local_folder, f"{movie_id}.jpg")

        try:
            self.fs.get(s3_file, local_file)
            logger.info(f"Successfully retrieved {s3_file} and saved it to {local_file}")
        except Exception as e:
            logger.error(f"Failed to retrieve {s3_file}: {e}")

            try:
                logger.info(f"Creating an empty JPEG at {local_file}")
                empty_image = Image.new('RGB', (100, 100), color=(255, 255, 255))
                empty_image.save(local_file, 'jpg')
                logger.info(f"Created empty JPEG at {local_file}")
            except Exception as e:
                logger.error(f"Failed to create empty JPEG: {e}")

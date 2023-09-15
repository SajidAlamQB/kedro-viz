"""`kedro_viz.integrations.deployment.s3_deployer` defines
deployment class for S3"""

import json
import logging
from datetime import datetime
from pathlib import Path

import fsspec
from kedro.io.core import get_protocol_and_path

from kedro_viz.api.rest.responses import save_api_responses_to_fs

_HTML_DIR = Path(__file__).parent.parent.parent.absolute() / "html"

logger = logging.getLogger(__name__)


class S3Deployer:
    """Deployer class for AWS S3"""

    def __init__(self, region, bucket_name):
        self._region = region
        self._bucket_name = bucket_name
        self._protocol, self._path = get_protocol_and_path(bucket_name)
        self._remote_fs = fsspec.filesystem(self._protocol)

    def _upload_api_responses(self):
        save_api_responses_to_fs(self._bucket_name)

    def _upload_static_files(self):
        logger.debug("""Uploading static html files to %s.""", self._bucket_name)
        try:
            self._remote_fs.put(
                f"{str(_HTML_DIR)}/*", self._bucket_name, recursive=True
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("Upload failed: %s ", exc)
            raise exc

    def _upload_timestamp_file(self):
        logger.debug(
            """Creating and Uploading timestamp file to %s.""", self._bucket_name
        )

        try:
            with self._remote_fs.open(
                f"{self._bucket_name}/api/timestamp", "w"
            ) as timestamp_file:
                timestamp_file.write(
                    json.dumps(
                        {"timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
                    )
                )
        except Exception as exc:  # pragma: no cover
            logger.exception("Upload failed: %s ", exc)
            raise exc

    def _deploy(self):
        self._upload_api_responses()
        self._upload_static_files()
        self._upload_timestamp_file()

    def get_deployed_url(self):
        """Returns an S3 URL where Kedro viz is deployed"""
        self._deploy()
        return f"http://{self._path}.s3-website.{self._region}.amazonaws.com"
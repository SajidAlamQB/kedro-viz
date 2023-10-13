"""`kedro_viz.constants` defines constants to be used throughout the application."""
import kedro
from semver import VersionInfo
from pathlib import Path

DEFAULT_REGISTERED_PIPELINE_ID = "__default__"
KEDRO_VERSION = VersionInfo.parse(kedro.__version__)
ROOT_MODULAR_PIPELINE_ID = "__root__"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 4141
_HTML_DIR = Path(__file__).parent.absolute() / "html"
_METADATA_PATH = "api/deploy-viz-metadata"

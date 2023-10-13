"""`kedro_viz.launchers.cli` launches the viz server as a CLI app."""
import json
import logging
import multiprocessing
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict

import click
import fsspec
from jinja2 import Environment, FileSystemLoader
from kedro.framework.cli.project import PARAMS_ARG_HELP
from kedro.framework.cli.utils import KedroCliError, _split_params
from kedro_viz import __version__
from kedro_viz.api.rest.responses import save_api_responses_to_fs
from kedro_viz.constants import (_HTML_DIR, _METADATA_PATH, DEFAULT_HOST,
                                 DEFAULT_PORT)
from kedro_viz.data_access import DataAccessManager, data_access_manager
from kedro_viz.integrations.kedro import data_loader as kedro_data_loader
from kedro_viz.integrations.kedro import telemetry as kedro_telemetry
from kedro_viz.integrations.pypi import (get_latest_version,
                                         is_running_outdated_version)
from kedro_viz.launchers.utils import _check_viz_up, _start_browser, _wait_for
from kedro_viz.server import populate_data
from semver import VersionInfo
from watchgod import RegExpWatcher, run_process

logger = logging.getLogger(__file__)

_VIZ_PROCESSES: Dict[str, int] = {}


@click.group(name="Kedro-Viz")
def commands():  # pylint: disable=missing-function-docstring
    pass


@commands.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--host",
    default=DEFAULT_HOST,
    help="Host that viz will listen to. Defaults to localhost.",
)
@click.option(
    "--port",
    default=DEFAULT_PORT,
    type=int,
    help="TCP port that viz will listen to. Defaults to 4141.",
)
@click.option(
    "--browser/--no-browser",
    default=True,
    help="Whether to open viz interface in the default browser or not. "
    "Browser will only be opened if host is localhost. Defaults to True.",
)
@click.option(
    "--load-file",
    default=None,
    help="Load Kedro-Viz using JSON files from the specified directory.",
)
@click.option(
    "--save-file",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Save all API responses from the backend as JSON files in the specified directory.",
)
@click.option(
    "--pipeline",
    type=str,
    default=None,
    help="Name of the registered pipeline to visualise. "
    "If not set, the default pipeline is visualised",
)
@click.option(
    "--env",
    "-e",
    type=str,
    default=None,
    multiple=False,
    envvar="KEDRO_ENV",
    help="Kedro configuration environment. If not specified, "
    "catalog config in `local` will be used",
)
@click.option(
    "--autoreload",
    "-a",
    is_flag=True,
    help="Autoreload viz server when a Python or YAML file change in the Kedro project",
)
@click.option(
    "--params",
    type=click.UNPROCESSED,
    default="",
    help=PARAMS_ARG_HELP,
    callback=_split_params,
)

# pylint: disable=import-outside-toplevel, too-many-locals
def viz(host, port, browser, load_file, save_file, pipeline, env, autoreload, params):
    """Visualise a Kedro pipeline using Kedro viz."""
    from kedro_viz.server import run_server

    installed_version = VersionInfo.parse(__version__)
    latest_version = get_latest_version()
    if is_running_outdated_version(installed_version, latest_version):
        click.echo(
            click.style(
                "WARNING: You are using an old version of Kedro Viz. "
                f"You are using version {installed_version}; "
                f"however, version {latest_version} is now available.\n"
                "You should consider upgrading via the `pip install -U kedro-viz` command.\n"
                "You can view the complete changelog at "
                "https://github.com/kedro-org/kedro-viz/releases.",
                fg="yellow",
            ),
        )

    try:
        if port in _VIZ_PROCESSES and _VIZ_PROCESSES[port].is_alive():
            _VIZ_PROCESSES[port].terminate()

        run_server_kwargs = {
            "host": host,
            "port": port,
            "load_file": load_file,
            "save_file": save_file,
            "pipeline_name": pipeline,
            "env": env,
            "autoreload": autoreload,
            "extra_params": params,
        }
        if autoreload:
            project_path = Path.cwd()
            run_server_kwargs["project_path"] = project_path
            run_process_kwargs = {
                "path": project_path,
                "target": run_server,
                "kwargs": run_server_kwargs,
                "watcher_cls": RegExpWatcher,
                "watcher_kwargs": {"re_files": r"^.*(\.yml|\.yaml|\.py|\.json)$"},
            }
            viz_process = multiprocessing.Process(
                target=run_process, daemon=False, kwargs={**run_process_kwargs}
            )
        else:
            viz_process = multiprocessing.Process(
                target=run_server, daemon=False, kwargs={**run_server_kwargs}
            )

        viz_process.start()
        _VIZ_PROCESSES[port] = viz_process

        _wait_for(func=_check_viz_up, host=host, port=port)

        print("Kedro Viz Backend Server started successfully...")

        if browser:
            _start_browser(host, port)

    except Exception as ex:  # pragma: no cover
        traceback.print_exc()
        raise KedroCliError(str(ex)) from ex


@commands.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--api-dir",
    default="_sites",
    type=click.Path(dir_okay=True, writable=True),
    help="Save all API responses from the backend as JSON files in the specified directory.",
)
@click.option(
    "--host",
    default=DEFAULT_HOST,
    help="Host that viz will listen to. Defaults to localhost.",
)
@click.option(
    "--port",
    default=DEFAULT_PORT,
    type=int,
    help="TCP port that viz will listen to. Defaults to 4141.",
)
@click.option(
    "--pipeline",
    type=str,
    default=None,
    help="Name of the registered pipeline to visualise. "
    "If not set, the default pipeline is visualised",
)
@click.option(
    "--env",
    "-e",
    type=str,
    default=None,
    multiple=False,
    envvar="KEDRO_ENV",
    help="Kedro configuration environment. If not specified, "
    "catalog config in `local` will be used",
)
@click.option(
    "--params",
    type=click.UNPROCESSED,
    default="",
    help=PARAMS_ARG_HELP,
    callback=_split_params,
)
# pylint: disable=import-outside-toplevel, too-many-locals
def viz_build(api_dir, host, port, pipeline, env, params):
    """Build a static site for Kedro pipelines using Kedro viz."""
    from kedro_viz.server import run_server

    installed_version = VersionInfo.parse(__version__)
    latest_version = get_latest_version()
    if is_running_outdated_version(installed_version, latest_version):
        click.echo(
            click.style(
                "WARNING: You are using an old version of Kedro Viz. "
                f"You are using version {installed_version}; "
                f"however, version {latest_version} is now available.\n"
                "You should consider upgrading via the `pip install -U kedro-viz` command.\n"
                "You can view the complete changelog at "
                "https://github.com/kedro-org/kedro-viz/releases.",
                fg="yellow",
            ),
        )
    def _deploy(api_dir):
        _fs = fsspec.filesystem("file")

        def _copy_static_files(html_dir: Path, destination_dir):
            """Upload static HTML files to S3."""
            logger.debug("Uploading static html files to %s.", destination_dir)


        def _ingest_heap_analytics(destination_dir):
            """Ingest heap analytics to index file in the build folder."""
            project_path = Path.cwd().absolute()
            heap_app_id = kedro_telemetry.get_heap_app_id(project_path)
            heap_user_identity = kedro_telemetry.get_heap_identity()
            should_add_telemetry = bool(heap_app_id) and bool(heap_user_identity)
            html_content = (_HTML_DIR / "index.html").read_text(encoding="utf-8")
            injected_head_content = []

            env = Environment(loader=FileSystemLoader(_HTML_DIR))

            if should_add_telemetry:
                logger.debug("Ingesting heap analytics.")
                telemetry_content = env.get_template("telemetry.html").render(
                    heap_app_id=heap_app_id, heap_user_identity=heap_user_identity
                )
                injected_head_content.append(telemetry_content)

            injected_head_content.append("</head>")
            html_content = html_content.replace("</head>", "\n".join(injected_head_content))

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = f"{temp_dir}/index.html"

                with open(temp_file_path, "w", encoding="utf-8") as temp_index_file:
                    temp_index_file.write(html_content)

                _fs.put(temp_file_path, f"{destination_dir}/")

        def _upload_deploy_viz_metadata_file(destination_dir):
            logger.debug(
                "Creating and Uploading deploy viz metadata file to %s.",
                destination_dir,
            )

            try:
                metadata = {
                    "timestamp": datetime.utcnow().strftime("%d.%m.%Y %H:%M:%S"),
                    "version": str(VersionInfo.parse(__version__)),
                }
                with _fs.open(
                    f"{destination_dir}/{_METADATA_PATH}", "w"
                ) as metadata_file:
                    metadata_file.write(json.dumps(metadata))
            except Exception as exc:  # pragma: no cover
                logger.exception("Upload failed: %s ", exc)
                raise exc

            try:
                print("DEBUG**", _HTML_DIR)
                _fs.put(f"{str(_HTML_DIR)}/*", destination_dir, recursive=True)
                _ingest_heap_analytics(destination_dir)
            except Exception as exc:  # pragma: no cover
                logger.exception("Upload failed: %s ", exc)
                raise exc

        save_api_responses_to_fs(api_dir)
        _copy_static_files(_HTML_DIR, api_dir)
        _upload_deploy_viz_metadata_file(api_dir)

    path = Path.cwd()

    catalog, pipelines, session_store, stats_dict = kedro_data_loader.load_data(
        path, env,params
    )
    pipelines = (
        pipelines
        if pipeline is None
        else {pipeline: pipelines[pipeline]}
    )
    populate_data(
        data_access_manager, catalog, pipelines, session_store, stats_dict
    )
    _deploy(api_dir)
    print("Kedro Viz Static Site Build successfully...")

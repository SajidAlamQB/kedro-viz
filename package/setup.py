# type: ignore
from setuptools import setup

extras_require["test"] = [
    "kedro >=0.17.0",
    "kedro-datasets[pandas.ParquetDataSet, pandas.CSVDataSet, pandas.ExcelDataSet, plotly.JSONDataSet]>=1.0, <1.7.1",
    "kedro-telemetry>=0.1.1",  # for testing telemetry integration
    "bandit~=1.7",
    "behave~=1.2",
    "black~=23.3",
    "boto3~=1.26",
    "flake8~=5.0",
    "fastapi[all]>=0.73.0, <0.96.0",
    "isort~=5.11",
    "matplotlib~=3.5",
    "mypy~=1.0",
    "moto~=4.1.14",
    "psutil==5.9.5",  # same as Kedro for now
    "pylint~=2.17",
    "pytest~=7.4",
    "pytest-asyncio~=0.21",
    "pytest-mock~=3.11",
    "pytest-cov~=4.1",
    "sqlalchemy-stubs~=0.4",
    "strawberry-graphql[cli]>=0.99.0, <1.0",
    "trufflehog~=2.2",
    "types-aiofiles==0.1.3",
    "types-cachetools==0.1.6",
    "types-click==0.1.14",
    "types-futures==0.1.3",
    "types-Jinja2==2.11.2",
    "types-orjson==0.1.0",
    "types-pkg-resources==0.1.2",
    "types-protobuf==0.1.10",
    "types-PyYAML==0.1.5",
    "types-requests==0.1.8",
    "types-toml==0.1.1",
    "types-ujson==0.1.0",
    "typing_extensions~=4.7.0; python_version < '3.9'",
]

setup(
    package_data={
        "kedro-viz"
    },
    extras_require=extras_require,
)x
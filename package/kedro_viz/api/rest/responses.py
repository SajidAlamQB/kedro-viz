"""`kedro_viz.api.rest.responses` defines REST response types."""
# pylint: disable=missing-class-docstring,too-few-public-methods,invalid-name
import abc
from typing import Any, Dict, List, Optional, Union

import fsspec
import orjson
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, ORJSONResponse
from kedro.io.core import get_protocol_and_path
from pydantic import BaseModel

from kedro_viz.data_access import data_access_manager
from kedro_viz.models.flowchart import (
    DataNode,
    DataNodeMetadata,
    ParametersNodeMetadata,
    TaskNode,
    TaskNodeMetadata,
    TranscodedDataNode,
    TranscodedDataNodeMetadata,
)


class APIErrorMessage(BaseModel):
    message: str


class BaseAPIResponse(BaseModel, abc.ABC):
    class Config:
        orm_mode = True


class BaseGraphNodeAPIResponse(BaseAPIResponse):
    id: str
    name: str
    tags: List[str]
    pipelines: List[str]
    type: str

    # If a node is a ModularPipeline node, this value will be None, hence Optional.
    modular_pipelines: Optional[List[str]]


class TaskNodeAPIResponse(BaseGraphNodeAPIResponse):
    parameters: Dict

    class Config:
        schema_extra = {
            "example": {
                "id": "6ab908b8",
                "name": "split_data_node",
                "tags": [],
                "pipelines": ["__default__", "ds"],
                "modular_pipelines": [],
                "type": "task",
                "parameters": {
                    "test_size": 0.2,
                    "random_state": 3,
                    "features": [
                        "engines",
                        "passenger_capacity",
                        "crew",
                        "d_check_complete",
                        "moon_clearance_complete",
                        "iata_approved",
                        "company_rating",
                        "review_scores_rating",
                    ],
                },
            }
        }


class DataNodeAPIResponse(BaseGraphNodeAPIResponse):
    layer: Optional[str]
    dataset_type: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "id": "d7b83b05",
                "name": "master_table",
                "tags": [],
                "pipelines": ["__default__", "dp", "ds"],
                "modular_pipelines": [],
                "type": "data",
                "layer": "primary",
                "dataset_type": "kedro.extras.datasets.pandas.csv_dataset.CSVDataSet",
            }
        }


NodeAPIResponse = Union[
    TaskNodeAPIResponse,
    DataNodeAPIResponse,
]


class TaskNodeMetadataAPIResponse(BaseAPIResponse):
    code: Optional[str]
    filepath: Optional[str]
    parameters: Optional[Dict]
    inputs: List[str]
    outputs: List[str]
    run_command: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "code": "def split_data(data: pd.DataFrame, parameters: Dict) -> Tuple:",
                "filepath": "proj/src/new_kedro_project/pipelines/data_science/nodes.py",
                "parameters": {"test_size": 0.2},
                "inputs": ["params:input1", "input2"],
                "outputs": ["output1"],
                "run_command": "kedro run --to-nodes=split_data",
            }
        }


class DataNodeMetadataAPIResponse(BaseAPIResponse):
    filepath: Optional[str]
    type: str
    plot: Optional[Dict]
    image: Optional[str]
    tracking_data: Optional[Dict]
    run_command: Optional[str]
    preview: Optional[Dict]
    stats: Optional[Dict]

    class Config:
        schema_extra = {
            "example": {
                "filepath": "/my-kedro-project/data/03_primary/master_table.csv",
                "type": "pandas.csv_dataset.CSVDataSet",
                "run_command": "kedro run --to-outputs=master_table",
            }
        }


class TranscodedDataNodeMetadataAPIReponse(BaseAPIResponse):
    filepath: str
    original_type: str
    transcoded_types: List[str]
    run_command: Optional[str]
    stats: Optional[Dict]


class ParametersNodeMetadataAPIResponse(BaseAPIResponse):
    parameters: Dict

    class Config:
        schema_extra = {
            "example": {
                "parameters": {
                    "test_size": 0.2,
                    "random_state": 3,
                    "features": [
                        "engines",
                        "passenger_capacity",
                        "crew",
                        "d_check_complete",
                        "moon_clearance_complete",
                        "iata_approved",
                        "company_rating",
                        "review_scores_rating",
                    ],
                }
            }
        }


NodeMetadataAPIResponse = Union[
    TaskNodeMetadataAPIResponse,
    DataNodeMetadataAPIResponse,
    TranscodedDataNodeMetadataAPIReponse,
    ParametersNodeMetadataAPIResponse,
]


class GraphEdgeAPIResponse(BaseAPIResponse):
    source: str
    target: str


class NamedEntityAPIResponse(BaseAPIResponse):
    """Model an API field that has an ID and a name.
    For example, used for representing modular pipelines and pipelines in the API response.
    """

    id: str
    name: Optional[str]


class ModularPipelineChildAPIResponse(BaseAPIResponse):
    """Model a child in a modular pipeline's children field in the API response."""

    id: str
    type: str


class ModularPipelinesTreeNodeAPIResponse(BaseAPIResponse):
    """Model a node in the tree representation of modular pipelines in the API response."""

    id: str
    name: str
    inputs: List[str]
    outputs: List[str]
    children: List[ModularPipelineChildAPIResponse]


# Represent the modular pipelines in the API response as a tree.
# The root node is always designated with the __root__ key.
# Example:
# {
#     "__root__": {
#            "id": "__root__",
#            "name": "Root",
#            "inputs": [],
#            "outputs": [],
#            "children": [
#                {"id": "d577578a", "type": "parameters"},
#                {"id": "data_science", "type": "modularPipeline"},
#                {"id": "f1f1425b", "type": "parameters"},
#                {"id": "data_engineering", "type": "modularPipeline"},
#            ],
#        },
#        "data_engineering": {
#            "id": "data_engineering",
#            "name": "Data Engineering",
#            "inputs": ["d577578a"],
#            "outputs": [],
#            "children": [],
#        },
#        "data_science": {
#            "id": "data_science",
#            "name": "Data Science",
#            "inputs": ["f1f1425b"],
#            "outputs": [],
#            "children": [],
#        },
#    }
# }
ModularPipelinesTreeAPIResponse = Dict[str, ModularPipelinesTreeNodeAPIResponse]


class GraphAPIResponse(BaseAPIResponse):
    nodes: List[NodeAPIResponse]
    edges: List[GraphEdgeAPIResponse]
    layers: List[str]
    tags: List[NamedEntityAPIResponse]
    pipelines: List[NamedEntityAPIResponse]
    modular_pipelines: ModularPipelinesTreeAPIResponse
    selected_pipeline: str


class EnhancedORJSONResponse(ORJSONResponse):
    @staticmethod
    def encode_to_human_readable(content: Any) -> bytes:
        """A method to encode the given content to JSON, with the
        proper formatting to write a human-readable file.

        Returns:
            A bytes object containing the JSON to write.

        """
        return orjson.dumps(
            content,
            option=orjson.OPT_INDENT_2
            | orjson.OPT_NON_STR_KEYS
            | orjson.OPT_SERIALIZE_NUMPY,
        )


def get_default_response() -> GraphAPIResponse:
    """Default response for `/api/main`."""
    default_selected_pipeline_id = (
        data_access_manager.get_default_selected_pipeline().id
    )

    modular_pipelines_tree = (
        data_access_manager.create_modular_pipelines_tree_for_registered_pipeline(
            default_selected_pipeline_id
        )
    )

    return GraphAPIResponse(
        nodes=data_access_manager.get_nodes_for_registered_pipeline(  # type: ignore
            default_selected_pipeline_id
        ),
        edges=data_access_manager.get_edges_for_registered_pipeline(  # type: ignore
            default_selected_pipeline_id
        ),
        tags=data_access_manager.tags.as_list(),
        layers=data_access_manager.get_sorted_layers_for_registered_pipeline(
            default_selected_pipeline_id
        ),
        pipelines=data_access_manager.registered_pipelines.as_list(),
        modular_pipelines=modular_pipelines_tree,  # type: ignore
        selected_pipeline=default_selected_pipeline_id,
    )


def get_node_metadata_response(node_id: str):
    """API response for `/api/nodes/node_id`."""
    node = data_access_manager.nodes.get_node_by_id(node_id)
    if not node:
        return JSONResponse(status_code=404, content={"message": "Invalid node ID"})

    if not node.has_metadata():
        return JSONResponse(content={})

    if isinstance(node, TaskNode):
        return TaskNodeMetadata(node)

    if isinstance(node, DataNode):
        dataset_stats = data_access_manager.get_stats_for_data_node(node)
        return DataNodeMetadata(node, dataset_stats)

    if isinstance(node, TranscodedDataNode):
        dataset_stats = data_access_manager.get_stats_for_data_node(node)
        return TranscodedDataNodeMetadata(node, dataset_stats)

    return ParametersNodeMetadata(node)


def get_selected_pipeline_response(registered_pipeline_id: str):
    """API response for `/api/pipeline/pipeline_id`."""
    if not data_access_manager.registered_pipelines.has_pipeline(
        registered_pipeline_id
    ):
        return JSONResponse(status_code=404, content={"message": "Invalid pipeline ID"})

    modular_pipelines_tree = (
        data_access_manager.create_modular_pipelines_tree_for_registered_pipeline(
            registered_pipeline_id
        )
    )

    return GraphAPIResponse(
        nodes=data_access_manager.get_nodes_for_registered_pipeline(
            registered_pipeline_id
        ),
        edges=data_access_manager.get_edges_for_registered_pipeline(
            registered_pipeline_id
        ),
        tags=data_access_manager.tags.as_list(),
        layers=data_access_manager.get_sorted_layers_for_registered_pipeline(
            registered_pipeline_id
        ),
        pipelines=data_access_manager.registered_pipelines.as_list(),
        selected_pipeline=registered_pipeline_id,
        modular_pipelines=modular_pipelines_tree,
    )


def save_api_responses_to_fs(filepath: str):
    protocol, path = get_protocol_and_path(filepath)
    remote_fs = fsspec.filesystem(protocol)
    
    def encode_response(response):
        jsonable_response = jsonable_encoder(response)
        return EnhancedORJSONResponse.encode_to_human_readable(jsonable_response)

    def write_to_file(location, data):
        with remote_fs.open(location, "wb") as f:
            f.write(data)

    if protocol == "file":
        for loc in [path, f"{path}/api/nodes", f"{path}/api/pipelines"]:
            remote_fs.makedirs(loc, exist_ok=True)

    default_response = get_default_response()
    write_to_file(f"{path}/api/main", encode_response(default_response))

    for node in data_access_manager.nodes.get_node_ids():
        node_response = get_node_metadata_response(node)
        write_to_file(f"{path}/api/nodes/{node}", encode_response(node_response))

    for pipeline in data_access_manager.registered_pipelines.get_pipeline_ids():
        pipeline_response = get_selected_pipeline_response(pipeline)
        write_to_file(f"{path}/api/pipelines/{pipeline}", encode_response(pipeline_response))

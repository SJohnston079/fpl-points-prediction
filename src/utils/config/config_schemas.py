from pydantic import BaseModel, ConfigDict, AfterValidator, model_validator
from typing import Literal, Optional, Annotated
import jinja2
import re


class GitHubConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal['github']
    owner: str
    repo: str
    branch: Optional[str] = 'main'


class DataSourceMetaDataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: Optional[str] = None
    source: GitHubConfig # Should be a generic "data source" config, but for now we only support GitHub
    output_dir_name: str


def validate_jinja_syntax(value: str) -> str:
    try:
        jinja2.Environment().parse(value)
    except jinja2.exceptions.TemplateSyntaxError as e:
        raise ValueError(f"Invalid Jinja template syntax: {e}")
    return value


def validate_variable_name(name: str, regular_expression: str) -> str:

    if not re.fullmatch(regular_expression, name):
        raise ValueError(f"Invalid variable name: {name}. Must match the pattern: {regular_expression}")
    return name

class FplCoreInsightsIngestionConfig(BaseModel):
    #model_config = ConfigDict(extra="forbid")

    filenames: list[str]
    #temporal_granularity: Literal['gameweek', 'season']
    filepath_jinja: dict[str, Annotated[str, AfterValidator(validate_jinja_syntax)]] # expressed in jinja template format
    season_filepath_jinja_map: dict[str, str]
    structure: Optional[dict]

    @model_validator(mode="after")
    def check_structure_refs(self) -> "FplCoreInsightsIngestionConfig":
        referenced = set(self.season_filepath_jinja_map.values())
        defined = set(self.filepath_jinja.keys())

        missing = referenced - defined
        if missing:
            raise ValueError(
                f"season_filepath_jinja_map references undefined structures: {missing}"
            )

        return self


class DataIngestionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ingestion: FplCoreInsightsIngestionConfig # Should be a generic "data ingestion" config, but for now we only support FPL Core Insights
    #output_dir_name: str

    
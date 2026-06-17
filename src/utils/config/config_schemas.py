from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional



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
    source: GitHubConfig
    output_dir_name: str
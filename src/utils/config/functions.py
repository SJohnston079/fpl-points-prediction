from pathlib import Path
from pydantic import BaseModel
from typing import TypeVar, Type

from ruamel.yaml import YAML
yaml = YAML()
yaml.default_flow_style = False

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

def read_config(config_path: Path, config_class: Type[T]) -> T:
    """Load a YAML configuration file and validate it using a Pydantic model.

    The YAML file is parsed into a Python dictionary, which is then validated
    and coerced into the provided Pydantic model using `model_validate`. 

    :param config_path: Path to the YAML configuration file.
    :type config_path: Path
    :param config_class: Pydantic model class used for validation.
    :type config_class: type[BaseModel]
    :return: Instance of `config_class` containing validated configuration data.
    :rtype: BaseModel
    """
    with open(config_path, 'r') as config_file:
        config_raw = yaml.load(config_file)
    
    config = config_class.model_validate(config_raw)
    return config
from pathlib import Path, PurePosixPath
from pydantic import BaseModel
import zipfile
from typing import Optional, Union
import sys

from ruamel.yaml import YAML
yaml = YAML()
yaml.default_flow_style = False

src_root = Path(__file__).resolve().parent.parent
sys.path.append(str(src_root))
from utils.config.config_schemas import DataSourceMetaDataConfig

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def read_config(config_path: Path, config_class: type[BaseModel]) -> BaseModel:
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


def validate_output_location(output_path: Path):
    """Validates the output path. Must be of type Path, and must currently be empty

    :param output_path: _description_
    :type output_path: Path
    """

    assert isinstance(output_path, Path), f"{output_path}, is not of type '{Path}'"
    if output_path.exists():
        assert not any(output_path.iterdir()), f"Directory {output_path} is not empty"


def get_relative_path(zip_entry_path: str, archive_prefix: PurePosixPath) -> Optional[PurePosixPath]:
    """Returns the file path within the ZIP archive, relative to the specified prefix.

    :param zip_entry_path: An absolute file path.
    :type zip_entry_path: str
    :param archive_prefix: The path prefix from which relative file paths are calculated.
    :type archive_prefix: PurePosixPath
    :return: The relative path if the file is within the archive prefix, otherwise None.
    :rtype: Optional[PurePosixPath]
    """
    path = PurePosixPath (zip_entry_path)
    if path.is_relative_to(archive_prefix) and not zip_entry_path.endswith("/"):
        return path.relative_to(archive_prefix)


class BaseOutputManager:
    def __init__(self, output_path: Path):
        self.output_path = output_path

    def build_metadata(self):
        raise NotImplementedError("Subclasses must implement the build_metadata method.")
    
    def write_metadata(self):
        raise NotImplementedError("Subclasses must implement the write_metadata method.")

    def write_data(self):
        raise NotImplementedError("Subclasses must implement the write_data method.")
    
    def execute(self):
        raise NotImplementedError("Subclasses must implement the execute method.")
    

class ZipfileOutputManager(BaseOutputManager):
    def __init__(self, zip_file: zipfile.ZipFile, output_path: Path, archive_prefix: PurePosixPath, source_config: DataSourceMetaDataConfig, source_metadata: Optional[dict] = None):
        """_summary_

        :param zip_file: A zipfile to unzip and save to a specified location
        :type zip_file: zipfile.ZipFile
        :param output_path: The path to save the unzipped data to
        :type output_path: Path
        :param archive_prefix: A path prefix to filter files within the zip archive.
        :type archive_prefix: PurePosixPath
        :param source_config: The config file for the data source
        :type source_config: DataSourceMetaDataConfig
        :param source_metadata: Additional information about the source, that cannot/ is not provided in the config, defaults to None
        :type source_metadata: Optional[dict], optional
        """
        
        super().__init__(output_path)

        self.zip_file = zip_file
        self.archive_prefix = archive_prefix
        self.source_config = source_config
        self.source_metadata = source_metadata

    def build_metadata(self) -> dict:
        """Creates a dict, containing the metadata, relating to the zip data source

        :return: Dict containing the data source config, as 'source_config', and any other relevant information not found in the config, as 'source_metadata'
        :rtype: dict
        """

        metadata = {
            "source_config": self.source_config.model_dump(),
            "source_metadata":self.source_metadata
        }

        return metadata

    def write_yaml(self, metadata: dict, filename: str = "meta.yml"):
        """Writes a dictionary to a yaml file

        :param metadata: A dictionary containing metadata to be output
        :type metadata: dict
        :param filename: A filename to define the file by, defaults to "metadata.yml"
        :type filename: str, optional
        """
        if filename.endswith('.yaml'):
            filename = filename.replace('.yaml', '.yml')
        assert filename.endswith('.yml')
        yaml.dump(metadata, self.output_path / filename)

    def write_data(self):
        """Function to unzip the directory, and output to the specified output Path

        :param zip_file: A Zipfile object
        :type zip_file: zipfile.ZipFile
        :param output_dir_path: The directory where the files will be extracted.
        :type output_dir_path: Path
        :param archive_prefix: A path prefix to filter files within the zip archive.
        :type archive_prefix: Optional[Path]
        """
        file_paths = [(zip_entry_path, relative_path) for zip_entry_path in self.zip_file.namelist() if (relative_path := get_relative_path(zip_entry_path, self.archive_prefix))]
        log.info(f'Extracting {len(file_paths)} files from {self.archive_prefix}')

        for archive_file_path, relative_path in file_paths:
            file_output_path = self.output_path / relative_path
            file_output_path.parent.mkdir(parents=True, exist_ok=True)

            with self.zip_file.open(archive_file_path) as source, open(file_output_path, 'wb') as target:
                target.write(source.read())


    def execute(self):
        """Executes the Output Manager
            1) Build Metadata
            2) Write the Metadata to the specified directory (as meta.yml)
            3) Write the archive data to the specified directory (at the root of the archive_prefix)
        """

        metadata = self.build_metadata()
        self.write_yaml(metadata=metadata)
        self.write_data()
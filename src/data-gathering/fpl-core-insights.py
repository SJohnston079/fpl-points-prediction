import os
from pathlib import Path, PurePosixPath
from helper import download_from_github
import logging
import sys
import io
import zipfile
import requests
from typing import Optional, Union

src_root = Path(__file__).resolve().parent.parent
sys.path.append(str(src_root))
from utils.config.functions import read_config
from utils.config.types import DataSourceMetaDataConfig
from utils.constants import (
    SOURCES_CONFIG_DIR,
    SOURCE_METADATA_CONFIG_NAME,
    RAW_DATA_DIR_PATH
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def get_github_sha():
    return '1bfb53778a307e4b133085c01838cf01fc7a907b'


def get_relative_path(zip_entry_path: str, archive_prefix: Path) -> Union[Path, bool]:
    """Returns the file path within the ZIP archive, relative to the specified prefix.

    :param zip_entry_path: An absolute file path.
    :type zip_entry_path: str
    :param archive_prefix: The path prefix from which relative file paths are calculated.
    :type archive_prefix: Path
    :return: 
    :rtype: Union[Path, bool]
    """
    path = PurePosixPath (zip_entry_path)
    if path.is_relative_to(archive_prefix) and not zip_entry_path.endswith("/"):
        return path.relative_to(archive_prefix)
    return False


def get_github_url(owner: str, repo: str, sha: str) -> str:
    """Generate a Github URL

    :param owner: The github repository owner
    :type owner: str
    :param repo: The repository to extract from
    :type repo: str
    :param sha: The sha (secure hash algorithm) identifier for the commit
    :type sha: str
    :return: The constructed URL
    :rtype: str
    """
    return f"https://github.com/{owner}/{repo}/archive/{sha}.zip" 


def get_github_zip(url: str) -> zipfile.ZipFile:
    """Download a specific directory from a GitHub repository as a zip file

    :param url: The URL of the GitHub repository zip file.
    :type url: str
    :return: Returns a zipfile object to be parsed and saved
    :rtype: zipfile.ZipFile
    """
    response = requests.get(url)
    zip_file = zipfile.ZipFile(io.BytesIO(response.content), mode='r')
    return zip_file


def ingest_github_directory(config: DataSourceMetaDataConfig):
    """Ingest a directory from a GitHub repository based on the provided configuration.

    :param config: The configuration for the data source.
    :type config: DataSourceMetaDataConfig
    """

    sha = get_github_sha()
    log.info(f"Ingesting GitHub directory for {config.name} at sha {sha}")

    url = get_github_url(config.source.owner, config.source.repo, sha)
    log.info(f"Extracting directory from url: {url}")

    github_zip = get_github_zip(url)
    log.info("Github repository zipfile extracted")

    output_dir_path = PurePosixPath(RAW_DATA_DIR_PATH) / config.output_dir_name

    log.info(f"Unzipped repository and saved to {output_dir_path}")

    

if __name__ == "__main__":
    

    sources_config_path = Path(SOURCES_CONFIG_DIR)

    for dir in sources_config_path.iterdir():
        if not dir.is_dir():
            continue 

        metadata_config_path = dir / SOURCE_METADATA_CONFIG_NAME

        config = read_config(
            config_path=metadata_config_path,
            config_class=DataSourceMetaDataConfig
        )

        if config.source.type == 'github':
            ingest_github_directory(config)
        
        







    #ingest_fpl_core_insights()
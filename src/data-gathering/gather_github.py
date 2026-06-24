from pathlib import Path, PurePosixPath
from helper import download_from_github
import logging
import sys
import io
import zipfile
import requests
from typing import Optional, Union
from datetime import datetime, UTC
from dateutil import parser as dtparser
from zoneinfo import ZoneInfo

src_root = Path(__file__).resolve().parent.parent
sys.path.append(str(src_root))
from utils.config.functions import read_config, ZipfileOutputManager
from utils.config.config_schemas import DataSourceMetaDataConfig
from utils.constants import (
    SOURCES_CONFIG_DIR,
    SOURCE_METADATA_CONFIG_NAME,
    RAW_DATA_DIR_PATH
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def _check_response_status(response: requests.Response) -> None:
    """Validate an HTTP response, raising descriptive errors for non-2xx status codes.

    :param response: Response object from an HTTP request
    :type response: requests.Response
    :raises ValueError: For 4xx client errors
    :raises RuntimeError: For 429 rate limit or 5xx server errors
    """
    status_code = int(response.status_code)

    if status_code == 200:
        log.info("Successful API request")
    elif status_code == 400:
        raise ValueError(f"Bad Request: {response.json().get('message')}, for url {response.url}")
    elif status_code == 404:
        message = response.json().get('message') if response.content else 'No message'
        raise ValueError(f"Not Found: {message}, for url {response.url}")
    elif status_code == 429:
        raise RuntimeError("Rate Limited")
    elif 400 <= status_code < 500:
        raise ValueError(f"Client Error: {status_code}, for url {response.url}")
    elif status_code >= 500:
        raise RuntimeError(f"Server Error: {status_code}, for url {response.url}")
    else:
        response.raise_for_status()


def _parse_to_utc(date_str: str) -> datetime:
    """Parse a date string to utc datetime object

    :param date_str: A date string in any format recognised by dateutil.parser.parse (e.g. Human readable formats)
    :type date_str: str
    :return: A datetime object in UTC
    :rtype: datetime
    """
    print(date_str)
    dt = dtparser.parse(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC) 
    return dt


def get_commit_info(
    owner: str,
    repo: str,
    sha: Optional[str] = None,
    commit_datetime: Optional[datetime] = None,
) -> dict:
    """Function to get the sha identifier for a github repository,
    either for the most recent commit, or for a specific datetime.
    Also gathers commit metadata

    :param owner: The github repository owner
    :type owner: str
    :param repo: The repository to extract from
    :type repo: str
    :param sha: Commit SHA (secure hash algorithm) identifier to use directly. Defaults to None.
    :type sha: Optional[str], optional
    :param commit_datetime: Return the most recent commit SHA before this datetime. Ignored if sha is provided. Defaults to None.
    :type commit_datetime: Optional[datetime], optional
    :return: The sha (secure hash algorithm) identifier for the commit we are interested in
    :rtype: dict
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {"Accept": "application/vnd.github+json"}
    params = {}

    if sha:
        url += f"/{sha}"
    else:
        params["per_page"] = 1
        if commit_datetime:
            params['until'] = commit_datetime.isoformat()

    request_time = datetime.now(tz=UTC)
    response = requests.get(url, headers=headers, params=params, timeout=10)

    _check_response_status(response)

    # rate limit monitoring
    if 'x-ratelimit-limit' not in response.headers:
        log.debug("No rate limit headers present, skipping rate limit log")
    else:
        max_requests = response.headers.get('x-ratelimit-limit')
        remaining_requests = response.headers.get('x-ratelimit-remaining')
        total_used_requests = response.headers.get('x-ratelimit-used')
        print(response.headers.get('x-ratelimit-reset'))
        rate_limit_reset_time = datetime.fromtimestamp(int(response.headers.get('x-ratelimit-reset')), tz=UTC).astimezone(ZoneInfo("Pacific/Auckland"))
        rate_limit_resource = response.headers.get('x-ratelimit-resource')

        message = (
            f"GitHub rate limit ({rate_limit_resource}): "
            f"{remaining_requests}/{max_requests} requests remaining "
            f"({total_used_requests} used). "
            f"Resets at {rate_limit_reset_time.isoformat()}."
        )
        log.info(message)

    result = response.json() if sha else response.json()[0]

    return {
        'sha': result.get('sha'),
        'commit_datetime': _parse_to_utc(result['commit']['author'].get('date')).isoformat(),
        'request_datetime': request_time.isoformat(),
        'author': result['commit']['author'].get('name'),
        'message': result['commit'].get('message'),
    }


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


def gather_github_directory(config: DataSourceMetaDataConfig):
    """Ingest a directory from a GitHub repository based on the provided configuration.

    :param config: The configuration for the data source.
    :type config: DataSourceMetaDataConfig
    """
    commit_info = get_commit_info(
        owner = config.source.owner, 
        repo = config.source.repo,
        #sha = '1bfb53778a307e4b133085c01838cf01fc7a907b'
        #commit_datetime = datetime(2026, 6, 18, 22, 41, 54, tzinfo=UTC)
    )
    log.info(f"Commit information:\n{commit_info}")

    url = get_github_url(config.source.owner, config.source.repo, commit_info.get('sha'))
    log.info(f"Extracting directory from url: '{url}'")

    github_zip = get_github_zip(url)
    log.info("Github repository zipfile extracted")

    output_dir_path = PurePosixPath(RAW_DATA_DIR_PATH) / config.output_dir_name
    
    ZipfileOutputManager(
        zip_file=github_zip, 
        output_path=output_dir_path, 
        archive_prefix=PurePosixPath(f"{config.source.repo}-{commit_info.get('sha')}"), 
        source_config=config,
        source_metadata=commit_info
    ).execute()
    log.info(f"Unzipped repository and saved to {output_dir_path}")


if __name__ == "__main__":
    

    sources_config_path = Path(SOURCES_CONFIG_DIR)

    for dir in sources_config_path.iterdir():
        if not dir.is_dir():
            continue 

        metadata_config_path = dir / SOURCE_METADATA_CONFIG_NAME

        config = read_config(
            config_path=metadata_config_path,
            config_class=DataSourceMetaDataConfig,
        )

        if config.source.type == 'github':
            gather_github_directory(config)
        
        







    #ingest_fpl_core_insights()
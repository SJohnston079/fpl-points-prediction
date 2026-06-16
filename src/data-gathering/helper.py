import requests
import zipfile
import io
import logging
from typing import Optional
from pathlib import PurePosixPath 
import os

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def download_from_github(owner: str, repo: str, output_dir: str, input_dir: Optional[str] = None, branch: str = 'main', sha: Optional[str] = None):
    """Download a specific directory from a GitHub repository as a zip file and extract it to a specified location.

    Args:
        owner (str): The owner of the GitHub repository.
        repo (str): The name of the GitHub repository.
        output_dir (str): The directory to extract the downloaded files to.
        input_dir (Optional[str], optional): The specific directory within the repository to extract. Defaults to None. If None, the entire repository will be extracted.
        branch (str): The branch of the GitHub repository to download. Defaults to 'main'.
        sha (Optional[str], optional): The specific commit SHA to download. Defaults to None.
    """

    if sha:
        url = f"https://github.com/{owner}/{repo}/archive/{sha}.zip" # For specific commit
    else:
        url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip" # For most recent commit on a branch
    
    log.info(f'Downloading {url}')
    response = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(response.content), mode='r')
    log.info('Zip download complete')


    prefix = PurePosixPath(f"{repo}-{sha}") if sha else PurePosixPath(f"{repo}-{branch}")

    if input_dir:
        prefix = prefix / input_dir
 
    files = [(f, relative_path) for f in z.namelist() if (relative_path := get_relative_path(f, prefix))]
    log.info(f'Extracting {len(files)} files from {prefix}')

    
    for f, relative_path in files:
        # ensure the target directory exists
        os.makedirs(PurePosixPath(output_dir) / relative_path.parent, exist_ok=True)

        with z.open(f) as source, open(PurePosixPath(output_dir) / relative_path, 'wb') as target:
            target.write(source.read())

        

    z.close()


def get_relative_path(f, prefix):
    path = PurePosixPath (f)
    if path.is_relative_to(prefix) and not f.endswith("/"):
        return path.relative_to(prefix)
    return False
import os

import helper
import logging


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

owner = "olbauday"
repo = "FPL-Core-Insights"
branch = "main"
github_directory = 'data'
output_dir = 'data/00_raw/FPL-Core-Insights/'
#sha = 'aa0941a756948eb2681be212c51b6e9face0eb95' # For specific commit
sha = '1bfb53778a307e4b133085c01838cf01fc7a907b'

# Download zip into memory {sha}
url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip" # For most recent commit on a branch
#url = f"https://github.com/{owner}/{repo}/archive/{sha}.zip" For specific commit
helper.download_from_github(
    owner=owner,
    repo=repo,
    input_dir=github_directory,
    output_dir=output_dir,
    branch=branch,
    sha=sha
)
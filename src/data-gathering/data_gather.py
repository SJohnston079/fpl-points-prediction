from gather_github import gather_github_directory
import sys
from pathlib import Path

src_root = Path(__file__).resolve().parent.parent
sys.path.append(str(src_root))
from utils.config.functions import read_config
from utils.config.config_schemas import DataSourceMetaDataConfig
from utils.constants import SOURCES_CONFIG_DIR, SOURCE_METADATA_CONFIG_NAME

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
from pathlib import Path

# Global Project Working Directory
ROOT_DIR = 'FPL_POINTS-PREDICTION'

# CONFIG
SOURCE_METADATA_CONFIG_NAME = "meta.yml"
SOURCE_SCHEMA_CONFIG_NAME = "schema.yml"

CONFIG_ROOT = Path("configs")
SOURCES_CONFIG_DIR = CONFIG_ROOT / "sources"
FPL_CORE_INSIGHTS_CONFIG_DIR = SOURCES_CONFIG_DIR / "fpl_core_insights"



# DATA
RAW_DIR_NAME = "raw"


DATA_ROOT = Path("data")
RAW_DATA_DIR_PATH = DATA_ROOT / RAW_DIR_NAME
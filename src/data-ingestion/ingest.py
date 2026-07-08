import sys
from pathlib import Path, PosixPath
import pandas as pd

src_root = Path(__file__).resolve().parent.parent
sys.path.append(str(src_root))
from utils.config.functions import read_config
from utils.config.config_schemas import DataSourceMetaDataConfig
from utils.constants import SOURCE_METADATA_CONFIG_NAME, SOURCES_CONFIG_DIR, RAW_DATA_DIR_PATH




def ingest_fpl_core_insights():

    data_source = 'fpl-core-insights'
    season = '2025-2026'
    filename = 'players.csv'
    gameweek_info = 'By Gameweek'


    gameweek_dir = Path(RAW_DATA_DIR_PATH) / data_source / season / gameweek_info

    all_gw_dfs = []

    for gw_filepath in gameweek_dir.iterdir():
        print(f'Ingesting {gw_filepath}')
        df_gw_players = pd.read_csv(gw_filepath / filename)

        # adding in the gw column
        df_gw_players['gw'] = gw_filepath.stem
        all_gw_dfs.append(df_gw_players)

    df_players = pd.concat(all_gw_dfs, ignore_index=True)

    print(df_players.head())
    #print(df_players.groupby('player_code')['player_id'].nunique().max())


ingest_fpl_core_insights()
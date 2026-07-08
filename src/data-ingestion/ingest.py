import sys
from pathlib import Path, PosixPath
import pandas as pd
import jinja2

src_root = Path(__file__).resolve().parent.parent
sys.path.append(str(src_root))
from utils.config.functions import read_config
from utils.config.config_schemas import FplCoreInsightsIngestionConfig
from utils.constants import INGESTION_CONFIG_DIR, SOURCE_SCHEMA_CONFIG_NAME, RAW_DATA_DIR_PATH


def ingest_fpl_core_insights():

    data_source = 'fpl-core-insights'
    season = '2025-2026'
    filename = 'players'
    gameweek_info = 'By Gameweek'

    config = read_config(
        config_path= INGESTION_CONFIG_DIR / data_source / SOURCE_SCHEMA_CONFIG_NAME,
        config_class=FplCoreInsightsIngestionConfig,
    )

    template = jinja2.Template(config.filepath_jinja['structure_0'])
    rendered_path = template.render(season=season, filename=filename, temporal_granularity='season', gw=10)
    print(f'Rendered path: {rendered_path}')

    filepath = RAW_DATA_DIR_PATH / rendered_path

    # gameweek_dir = Path(RAW_DATA_DIR_PATH) / data_source / season / gameweek_info

    # all_gw_dfs = []

    # for gw_filepath in gameweek_dir.iterdir():
    #     print(f'Ingesting {gw_filepath}')
    #     df_gw_players = pd.read_csv(gw_filepath / filename)

    #     # adding in the gw column
    #     df_gw_players['gw'] = gw_filepath.stem
    #     all_gw_dfs.append(df_gw_players)

    # df_players = pd.concat(all_gw_dfs, ignore_index=True)

    # print(df_players.head())
    #print(df_players.groupby('player_code')['player_id'].nunique().max())


ingest_fpl_core_insights()


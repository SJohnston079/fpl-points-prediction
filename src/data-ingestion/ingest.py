import sys
from pathlib import Path, PosixPath
import pandas as pd
import jinja2
from typing import Literal, Optional

src_root = Path(__file__).resolve().parent.parent
sys.path.append(str(src_root))
from utils.config.functions import read_config
from utils.config.config_schemas import FplCoreInsightsIngestionConfig
from utils.constants import INGESTION_CONFIG_DIR, SOURCE_SCHEMA_CONFIG_NAME, RAW_DATA_DIR_PATH

TemporalGranularity = Literal["static", "season", "gameweek"]

class FilepathFactory:
    def __init__(self, path_base: Path, filepath_jinja: dict[str, str], season_filepath_jinja_map: dict[str, str]):
        """A factory to handle producing the correct filepath, given jinja structures

        :param path_base: The disk location at which the source's raw data is stored
        :type path_base: Path
        :param filepath_jinja: Jinja2 defining internal storage structures
        :type filepath_jinja: dict[str, str]
        :param season_filepath_jinja_map: A map to describe which seasons apply which jinja file path structures.
        :type season_filepath_jinja_map: dict[str, str]
        """

        self.path_base = path_base
        env = jinja2.Environment(undefined=jinja2.StrictUndefined)
        self.templates = {structure:env.from_string(filepath_jinja[structure]) for structure in filepath_jinja.keys()}
        self.season_map = season_filepath_jinja_map
        
    
    def get_filepath(self, season: str, temporal_granularity: TemporalGranularity, filename: str, gameweek: Optional[int] = None) -> Path:
        """Produces the correct filepath, using the correct schema, for the particular situation

        :param season: The season title (YYYY-YYYY)
        :type season: str
        :param temporal_granularity: The temporal granularity this input is stored at ("static", "season", "gameweek")
        :type temporal_granularity: TemporalGranularity
        :param filename: The name of the file, WITHOUT file extensions
        :type filename: str
        :param gameweek: The gameweek number
        :type gameweek: int
        :raises RuntimeError: Raises an error if the filepath jinja rendering fails
        :return: A path for the file, based on the season, temporal granularity, and filename
        :rtype: Path
        """

        assert season in self.season_map.keys(), f"Invalid season, must be of pattern YYYY-YYYY (one of {list(self.season_map.keys())})"
        assert (gameweek is not None) or (temporal_granularity != 'gameweek'), f"Argument 'gameweek' must be provided, when temporal_granularity = 'gameweek'"
    
        structure_label = self.season_map[season]
        template = self.templates[structure_label]

        try:
            path_str = template.render(
                season=season,
                temporal_granularity=temporal_granularity,
                gameweek=gameweek,
                filename=filename
            )
        except jinja2.exceptions.TemplateError as e:
            raise RuntimeError(f"Error while trying to parse filename: \n{e}")

        return self.path_base / path_str


def ingest_fpl_core_insights():

    data_source = 'fpl-core-insights'
    season = '2024-2025'
    filename = 'players'
    gameweek_info = 'By Gameweek'

    config = read_config(
        config_path= INGESTION_CONFIG_DIR / data_source / SOURCE_SCHEMA_CONFIG_NAME,
        config_class=FplCoreInsightsIngestionConfig,
    )

    # ensuring that an error is raised if any required variable is missing in the jinja template
    
    factory = FilepathFactory(
        path_base=RAW_DATA_DIR_PATH,
        filepath_jinja=config.filepath_jinja,
        season_filepath_jinja_map=config.season_filepath_jinja_map,
    )
    filepath = factory.get_filepath(season=season, temporal_granularity="season", filename=filename, gameweek=None)

    print(f'Filepath: {filepath}')

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


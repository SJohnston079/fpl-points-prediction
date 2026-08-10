import sys
from pathlib import Path, PosixPath
import pandas as pd
import jinja2
from typing import Literal, Optional
import duckdb

src_root = Path(__file__).resolve().parent.parent
sys.path.append(str(src_root))
from utils.config.functions import read_config
from utils.config.config_schemas import FplCoreInsightsIngestionConfig
from utils.constants import INGESTION_CONFIG_DIR, SOURCE_SCHEMA_CONFIG_NAME, RAW_DATA_DIR_PATH, INGESTION_DIR_PATH

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


def pandas_duckdb_load(df, cols_list, table):

    with duckdb.connect(INGESTION_DIR_PATH/'fpl_pipeline.duckdb') as con:

        cols_formated = ', '.join(cols_list)
        con.sql(f"""
        INSERT INTO {table} 
            BY NAME
            SELECT {cols_formated} FROM df
        """
        )


        con.sql(f'VIEW {table}')


def load_team(df):
    # currently is loaded to 3 different tables
    # 1. Team (HUB)
    # 2. Team_name_alias_fpl_core_insights
    # 3. Team_fpl_core_insights (later)

    df['source'] = 'fpl-core-insights'
    df['load_date'] = pd.t

    print(df)

def ingest_fpl_core_insights():

    data_source = 'fpl-core-insights'
    season = '2024-2025'
    current_gw = 38

    config = read_config(
        config_path= INGESTION_CONFIG_DIR / data_source / SOURCE_SCHEMA_CONFIG_NAME,
        config_class=FplCoreInsightsIngestionConfig,
    )


    # ensuring that an error is raised if any required variable is missing in the jinja template
    filepath_factory = FilepathFactory(
        path_base=RAW_DATA_DIR_PATH,
        filepath_jinja=config.filepath_jinja,
        season_filepath_jinja_map=config.season_filepath_jinja_map,
    )


    print(config.season_filepath_jinja_map)

    filename = config.filenames[0]
    granularity = 'season'
    
    for season in config.season_filepath_jinja_map.keys():

        

        if granularity == 'season':
            filepath = filepath_factory.get_filepath(
                season=season, 
                temporal_granularity=granularity, 
                filename=filename,
            )
            print(filepath)
            df = pd.read_csv(filepath)

            load_team(df=df)

            # (INGESTION_DIR_PATH / data_source / season).mkdir(parents=True, exist_ok=True)
            # df.to_csv(
            #     INGESTION_DIR_PATH / data_source / season / f"{filename}.csv",
            #     index=False
            # )

        elif granularity == 'gameweek':
            all_gw_dfs = []
            #for gw in range(1, current_gw + 1):
            # adding in the gw column
                #df_gw_players['gw'] = gw
                #all_gw_dfs.append(df_gw_players)
    
            #df_players = pd.concat(all_gw_dfs, ignore_index=True)
            pass


ingest_fpl_core_insights()


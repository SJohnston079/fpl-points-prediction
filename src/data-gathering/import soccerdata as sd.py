import pandas as pd
import soccerdata as sd


# ce = sd.ClubElo(no_store=True)

# data = ce.read_by_date(date='2026-08-04')
# print(data[data.index.str.contains('')])
# print(data)


sofascore = sd.Sofascore(leagues=['ENG-Premier League'], seasons=['24-25'])

print(sofascore.read_schedule())
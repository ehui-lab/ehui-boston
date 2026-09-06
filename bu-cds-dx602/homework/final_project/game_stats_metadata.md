# game_stats.csv

## 1. Overview
`game_stats_v2.csv` contains team-level box-score statistics for each NHL game in the dataset. Each game appears as two rows (typically one for home team and one for away team).

Source: Martin Ellis NHL game data, version 2.

## 2. File schema and column definitions

- `game_id` (string/int): unique game identifier (e.g., `2000020001`).
- `date_time_GMT` (string/datetime): game start timestamp in GMT/UTC, ISO 8601 format (e.g., `2000-10-04T23:00:00Z`).
- `home_team` (string): team name for home team as used in this dataset (e.g., `Colorado Avalanche`, `Dallas Stars`). 
- `away_team` (string): team name for away team as used in this dataset (e.g., `Colorado Avalanche`, `Dallas Stars`). 

- `home_won` (bool): result for home team in game (`TRUE` or `FALSE`).
- `home_settled_in` (string): game settlement type (`REG` = regulation time, `OT` = overtime, `SO` = shootout).
- `home_head_coach` (string): coach name for that team in that game.
- `home_goals` (int): goals scored by team.
- `home_shots` (int): shots on goal by team.
- `home_hits` (int or NA): physical hits (may be `NA` where missing).
- `home_pim` (int): penalty minutes.
- `home_powerPlayOpportunities` (int): power-play chances.
- `home_powerPlayGoals` (int): power-play goals.
- `home_faceOffWinPercentage` (string/float): faceoff win percentage.
- `home_giveaways` (int): turnovers given.
- `home_takeaways` (int): turnovers gained.
- `home_blocked` (int): blocked shots.

- `away_won` (bool): result for home team in game (`TRUE` or `FALSE`).
- `away_settled_in` (string): game settlement type (`REG` = regulation time, `OT` = overtime, `SO` = shootout).
- `away_head_coach` (string): coach name for that team in that game.
- `away_goals` (int): goals scored by team.
- `away_shots` (int): shots on goal by team.
- `away_hits` (int or NA): physical hits (may be `NA` where missing).
- `away_pim` (int): penalty minutes.
- `away_powerPlayOpportunities` (int): power-play chances.
- `away_powerPlayGoals` (int): power-play goals.
- `away_faceOffWinPercentage` (string/float): faceoff win percentage.
- `away_giveaways` (int): turnovers given.
- `away_takeaways` (int): turnovers gained.
- `away_blocked` (int): blocked shots.
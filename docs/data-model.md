# Data model

| Table | Key columns |
|---|---|
| `teams` | `id`, `name`, `acronym`, `image_url` |
| `matches` | `id`, `videogame`, `name`, `status`, `league_name`, `tournament_name`, `scheduled_at`, `begin_at`, `end_at`, `number_of_games`, `team1_id`, `team2_id`, `team1_score`, `team2_score`, `winner_id`, `updated_at` |

`status`: `not_started`, `running`, `finished`, `canceled`, `postponed`.

Planned: `games` (maps / rounds per match), `tournaments`, `standings`, `favorites`.

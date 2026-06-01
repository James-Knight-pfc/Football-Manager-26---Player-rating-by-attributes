# Football Manager Player Attribute Rating

## What this project does

Analyzes a Football Manager player export to provide position-based ratings, identify positioning mismatches, and recommend targeted training:

- Loads a Football Manager player export CSV file.
- Maps FM positions to generalized player groups (CB, FB, WB, CM, AM, Winger, ST).
- Calculates weighted position ratings based on role-specific attributes.
- Identifies players rated higher in different positions (tactical mismatches).
- Generates three detailed output sections:
  1. **Position Rankings** — Players ranked by role suitability.
  2. **Position Mismatches** — Players who excel in an alternate position.
  3. **Training Recommendations** — Personalized focus areas mapped to FM training regimes.

## Output Sections

### Position Rankings
For each position group, shows players ranked by their weighted position rating. Helps identify your best XI and squad depth.

### Position Mismatches
Highlights players whose attributes make them better suited to a different position than their current one. Useful for tactical flexibility or identifying squad redundancy.

### Training Recommendations
For players under 30, evaluates both:
- **Weighted attributes** (primary role requirements)
- **Secondary attributes** (complementary skills for tactical flexibility)

Each recommendation includes:
- Urgency flag: 🔴 **URGENT** (attribute < 9) or 📈 **FOCUS** (developmental)
- Status: ✅ **Strong** (well-developed) or needs training
- Training focus area (mapped to 16 FM training regimes)
- Specific attributes improved under that focus (e.g., "Quickness" trains Pace + Acceleration)

## Getting Started

1. Place your FM export file in the same directory.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the script:

```bash
# Using default filename (player_export.csv)
python attribute_rating.py

# Or specify a custom CSV file
python attribute_rating.py path/to/your/export.csv
```

## How It Works

### Position Classification
FM positions are mapped to standardized groups:
- `D (C)` → CB (Center Back)
- `D (R)`, `D (L)` → FB (Full Back)
- `WB (L)`, `WB (R)` → WB (Wing Back)
- `DM`, `M (C)` → CM (Central Midfielder)
- `AM (C)` → AM (Attacking Midfielder)
- `AM (R)`, `AM (L)`, `M (R)`, `M (L)` → Winger
- `ST (C)` → ST (Striker)

### Rating Calculation
Each player receives a position-specific weighted score:
- Attributes below 11 are penalized (encourages development of weak areas)
- Weights emphasize role-critical attributes (e.g., Pace for Wingers, Tackling for Defenders)
- Final rating is normalized across weighted attributes

### Position Compatibility
The system respects positional flexibility rules—players are only considered for compatible roles (e.g., CBs can play FB or CM, but not ST).

### Training Focus Mapping
16 FM training focuses are mapped to attribute improvements:
- **Quickness** → Pace, Acceleration
- **Defensive Positioning** → Marking, Positioning, Decisions
- **Ball Control** → First Touch, Dribbling, Technique
- ...and 13 others

## Files

- `attribute_rating.py` — Main analysis script with modular functions:
  - `load_data()` — Loads and validates CSV file
  - `classify_position()` — Maps FM positions to position groups
  - `calculate_rating()` — Computes weighted position ratings
  - `build_ratings()` — Builds player ratings table
  - `find_alternative_positions()` — Identifies positional mismatches
  - `print_*()` — Output formatting functions
  - `generate_report()` — Orchestrates the full analysis
- `requirements.txt` — Python dependencies (pandas, numpy)
- `README.md` — This file
- `.gitignore` — Exclude player export CSVs and artifacts

## Configuration & Customization

The following constants can be adjusted in `attribute_rating.py`:

- `RATING_THRESHOLD` — Minimum rating to qualify for squad lists (default: 12.5)
- `ALREADY_GOOD` — Attribute level considered sufficient (default: 14)
- `WEIGHTED_THRESHOLD` — Threshold for evaluating weighted attributes as "strong" (default: 14)
- `AGE_CUTOFF` — Exclude players above this age from training recommendations (default: 30)
- `position_weights` — Adjust role-specific attribute weights for different tactics
- `position_secondary_attrs` — Define complementary attributes per position
- `training_focus_attrs` — Map training focuses to attributes

## Requirements

The CSV export must include:
- Column: `Player` (player name)
- Column: `Best Pos` (FM position code)
- Column: `Age` (player age)
- All attribute columns (e.g., Pace, Marking, Tackling, etc.)
- Alternatively use the attached squad view Attributes.fmf by saving it in your fm views folder (create one if not present)

## How to Print Screen

Here is a link to the video that taught me how to print screen in fm 26, the video is by MustermannFM - [https://www.youtube.com/watch?v=NugiVa5xpIY]

## Notes

- Position weights reflect a **high-pressing gegenpress system** (high Pace demands, aggressive positioning). Adjust for other tactical philosophies.
- The script calculates squad averages dynamically for each run, allowing analysis of different squads without modification.
- Players under 30 receive training recommendations; older players are excluded as near their peak/decline.
- Misfits analysis only flags players where alternate positions exceed their natural position by a meaningful margin.
- Goalkeepers are ignored

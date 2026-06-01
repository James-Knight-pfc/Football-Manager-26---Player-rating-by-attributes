import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

DEFAULT_CSV = "player_export.csv"
RATING_THRESHOLD = 12.5
ALREADY_GOOD = 14
WEIGHTED_THRESHOLD = 14
AGE_CUTOFF = 30

position_weights: Dict[str, Dict[str, float]] = {
    'CB': {
        'Marking': 0.10, 'Tackling': 0.10, 'Heading': 0.08,
        'Positioning': 0.11, 'Concentration': 0.06, 'Anticipation': 0.07,
        'Pace': 0.14, 'Acceleration': 0.13, 'Jumping Reach': 0.09,
        'Strength': 0.08, 'Agility': 0.04
    },
    'FB': {
        'Tackling': 0.07, 'Marking': 0.06, 'Crossing': 0.08,
        'Positioning': 0.05, 'First Touch': 0.05,
        'Pace': 0.20, 'Acceleration': 0.17, 'Stamina': 0.13,
        'Agility': 0.06, 'Strength': 0.06, 'Jumping Reach': 0.07
    },
    'WB': {
    'Crossing': 0.09, 'Dribbling': 0.06, 'First Touch': 0.06,
    'Tackling': 0.06, 'Work Rate': 0.05, 'Positioning': 0.05,
    'Pace': 0.21, 'Acceleration': 0.18, 'Stamina': 0.15,
    'Agility': 0.09
    },
    'CM': {
        'Stamina': 0.09, 'Passing': 0.10, 'Tackling': 0.09,
        'Anticipation': 0.08, 'Work Rate': 0.12, 'Positioning': 0.07,
        'Vision': 0.07, 'Pace': 0.07, 'Acceleration': 0.06,
        'Agility': 0.06, 'First Touch': 0.06, 'Strength': 0.06,
        'Off The Ball': 0.07
    },
    'CM_att': {
        'Stamina': 0.09, 'Passing': 0.12, 'Vision': 0.09,
        'First Touch': 0.08, 'Off The Ball': 0.08, 'Work Rate': 0.11,
        'Pace': 0.08, 'Acceleration': 0.07, 'Agility': 0.08,
        'Anticipation': 0.08, 'Technique': 0.06
    },
    'CM_def': {
        'Tackling': 0.13, 'Marking': 0.10, 'Positioning': 0.10,
        'Anticipation': 0.09, 'Concentration': 0.08, 'Work Rate': 0.11,
        'Stamina': 0.09, 'Strength': 0.08, 'Pace': 0.08,
        'Acceleration': 0.07, 'Aggression': 0.07
    },
    'AM': {
        'Passing': 0.11, 'First Touch': 0.08, 'Vision': 0.09,
        'Dribbling': 0.07, 'Composure': 0.06, 'Technique': 0.07,
        'Off The Ball': 0.06, 'Work Rate': 0.04,
        'Pace': 0.13, 'Acceleration': 0.14, 'Agility': 0.08, 'Stamina': 0.07
    },
    'Winger': {
        'Dribbling': 0.07, 'Crossing': 0.06, 'First Touch': 0.05,
        'Technique': 0.04, 'Flair': 0.04, 'Work Rate': 0.04,
        'Pace': 0.22, 'Acceleration': 0.20, 'Stamina': 0.13,
        'Agility': 0.09, 'Balance': 0.06
    },
    'ST': {
        'Finishing': 0.13, 'Off The Ball': 0.08, 'Composure': 0.08,
        'First Touch': 0.06, 'Heading': 0.05, 'Anticipation': 0.06,
        'Work Rate': 0.05, 'Aggression': 0.04,
        'Pace': 0.18, 'Acceleration': 0.14, 'Strength': 0.09,
        'Jumping Reach': 0.04
    }
}

position_compatibility: Dict[str, List[str]] = {
    'CB': ['CB', 'FB', 'CM'],
    'FB': ['FB', 'CB', 'CM'],
    'CM': ['CM', 'CB', 'FB', 'AM'],
    'AM': ['AM', 'CM', 'Winger', 'ST'],
    'Winger': ['Winger', 'AM', 'ST'],
    'ST': ['ST', 'AM', 'Winger']
}


position_secondary_attrs: Dict[str, List[str]] = {
    'CB': ['Aggression', 'Bravery', 'Decisions', 'Composure', 'Work Rate', 'Stamina', 'Leadership'],
    'FB': ['Dribbling', 'Passing', 'Decisions', 'Work Rate', 'Stamina', 'Vision', 'Technique'],
    'DM': ['Decisions', 'Bravery', 'Leadership', 'Composure', 'Technique', 'Aggression', 'Vision'],
    'AM': ['Decisions', 'Leadership', 'Flair', 'Passing', 'Anticipation', 'Balance', 'Bravery'],
    'Winger': ['Decisions', 'Anticipation', 'Composure', 'Dribbling', 'Passing', 'Vision'],
    'ST': ['Dribbling', 'Technique', 'Decisions', 'Bravery', 'Flair', 'Balance', 'Vision']
}

training_focus_attrs: Dict[str, List[str]] = {
    'Free Kick Taking': ['Free Kick Taking', 'Technique'],
    'Corner Taking': ['Corners', 'Technique'],
    'Penalty Taking': ['Penalty Taking', 'Technique'],
    'Long Throws': ['Long Throws'],
    'Quickness': ['Pace', 'Acceleration'],
    'Agility and Balance': ['Agility', 'Balance'],
    'Strength': ['Strength', 'Jumping Reach'],
    'Endurance': ['Stamina', 'Work Rate'],
    'Defensive Positioning': ['Marking', 'Positioning', 'Decisions'],
    'Attacking Movement': ['Off The Ball', 'Anticipation', 'Decisions'],
    'Shooting': ['Finishing', 'Long Shots', 'Technique'],
    'Passing': ['Vision', 'Passing', 'Technique'],
    'Final Third': ['Composure', 'Decisions'],
    'Crossing': ['Crossing', 'Technique'],
    'Ball Control': ['First Touch', 'Dribbling', 'Technique'],
    'Aerial': ['Heading', 'Bravery']
}


def load_data(csv_file: str) -> pd.DataFrame:
    path = Path(csv_file)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path.resolve()}")
    return pd.read_csv(path)


def classify_position(pos: Optional[str]) -> Optional[str]:
    if not isinstance(pos, str):
        return None
    pos = pos.upper().strip()
    if pos == 'D (C)':
        return 'CB'
    if pos in ['D (R)', 'D (L)']:
        return 'FB'
    if pos in ['WB (L)', 'WB (R)']:
        return 'WB'
    if pos in ['DM', 'M (C)']:
        return 'CM'
    if pos == 'AM (C)':
        return 'AM'
    if pos in ['AM (R)', 'AM (L)', 'M (R)', 'M (L)']:
        return 'Winger'
    if pos == 'ST (C)':
        return 'ST'
    return None


def calculate_rating(row: pd.Series, weights: Dict[str, float]) -> Optional[float]:
    score = 0.0
    total_weight = 0.0
    for attr, weight in weights.items():
        if attr not in row.index or pd.isna(row[attr]):
            continue
        val = float(row[attr])
        score += val * weight
        if val < 11:
            score -= (11 - val) * weight
        total_weight += weight
    if total_weight == 0:
        return None
    return round(score / total_weight, 2)


def add_position_group(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Position Group'] = df['Best Pos'].apply(classify_position)
    return df


def build_ratings(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        pos_group = row.get('Position Group')
        if pos_group not in position_weights:
            continue
        rating = calculate_rating(row, position_weights[pos_group])
        record = {
            'Player': row['Player'],
            'Best Pos': row['Best Pos'],
            'Position Group': pos_group,
            'Age': row['Age'],
            'Rating': rating
        }
        # For CMs, also calculate attacking and defensive variants
        if pos_group == 'CM':
            record['Rating_Att'] = calculate_rating(row, position_weights['CM_att'])
            record['Rating_Def'] = calculate_rating(row, position_weights['CM_def'])
        rows.append(record)
    return pd.DataFrame(rows)


def find_alternative_positions(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        natural_group = row.get('Position Group')
        natural_rating = None
        if natural_group in position_weights:
            natural_rating = calculate_rating(row, position_weights[natural_group])
        best_alt_group = None
        best_alt_rating = 0.0
        for pos_group, weights in position_weights.items():
            # Skip if same natural position
            if pos_group == natural_group:
                continue
            # If player is already CM, skip CM_att/CM_def variants (to avoid lateral moves)
            if natural_group == 'CM' and pos_group in ['CM_att', 'CM_def']:
                continue
            rating = calculate_rating(row, weights)
            if rating is not None and rating > best_alt_rating:
                best_alt_rating = rating
                best_alt_group = pos_group
        if natural_rating is None:
            natural_rating = 0.0
        rows.append({
            'Player': row['Player'],
            'Best Pos': row['Best Pos'],
            'Age': row['Age'],
            'Natural Group': natural_group,
            'Natural Rating': natural_rating,
            'Better Alt Group': best_alt_group if best_alt_rating > natural_rating else None,
            'Better Alt Rating': round(best_alt_rating, 2) if best_alt_rating > natural_rating else None
        })
    return pd.DataFrame(rows)


def print_position_rankings(ratings_df: pd.DataFrame) -> None:
    groups = ['CB', 'FB', 'WB', 'CM', 'AM', 'Winger', 'ST']
    for group in groups:
        subset = ratings_df[ratings_df['Position Group'] == group].sort_values('Rating', ascending=False)
        if subset.empty:
            continue
        print(f"\n{'=' * 60}")
        print(f"  {group} RATINGS")
        print(f"{'=' * 60}")
        if group == 'CM':
            # Display CM with all three variants
            print(f"{'Player':<22} {'Best Pos':<10} {'Age':<4} {'Overall':<8} {'Attack':<8} {'Defense':<8}")
            print('-' * 60)
            for _, row in subset.iterrows():
                overall = f"{row['Rating']:.2f}" if pd.notna(row['Rating']) else '—'
                att = f"{row['Rating_Att']:.2f}" if pd.notna(row.get('Rating_Att')) else '—'
                defn = f"{row['Rating_Def']:.2f}" if pd.notna(row.get('Rating_Def')) else '—'
                print(f"{row['Player']:<22} {row['Best Pos']:<10} {int(row['Age']):<4} {overall:<8} {att:<8} {defn:<8}")
        else:
            print(subset[['Player', 'Best Pos', 'Age', 'Rating']].to_string(index=False))


def print_misfits(alt_df: pd.DataFrame) -> None:
    misfits = alt_df[alt_df['Better Alt Group'].notna()].sort_values('Better Alt Rating', ascending=False)
    if misfits.empty:
        return
    print('\n' + '=' * 60)
    print('  PLAYERS WHO RATE HIGHER IN A DIFFERENT POSITION')
    print('=' * 60)
    for _, row in misfits.iterrows():
        natural = f"{row['Natural Group']} ({row['Natural Rating']})" if row['Natural Group'] else 'Unclassified'
        print(
            f"{row['Player']:<22} {row['Best Pos']:<10} Age {int(row['Age'])}   "
            f"Natural: {natural:<18}  →  Better as {row['Better Alt Group']} ({row['Better Alt Rating']})"
        )


def get_training_recommendation(row: pd.Series, weights: Dict[str, float]) -> List[tuple]:
    """Evaluate weighted attributes and return priority-ranked recommendations."""
    recommendations = []
    for attr, weight in weights.items():
        if attr not in row.index or pd.isna(row[attr]) or attr not in TRAINABLE_ATTRS:
            continue
        val = float(row[attr])
        if val >= ALREADY_GOOD:
            continue
        # Higher penalty for critically low attributes (< 9)
        below_9_bonus = (9 - val) * weight * 2 if val < 9 else 0
        gap_to_threshold = (ALREADY_GOOD - val) * weight
        priority = below_9_bonus + gap_to_threshold
        recommendations.append((attr, val, weight, priority))
    recommendations.sort(key=lambda x: -x[3])
    return recommendations


def get_best_focus(attr_priorities: Dict[str, float]) -> tuple[Optional[str], List[str]]:
    """Map attribute priorities to the best training focus area.
    
    Returns:
        (best_focus_name, list_of_trained_attributes)
    """
    focus_scores: Dict[str, float] = {}
    for focus, attrs in training_focus_attrs.items():
        score = sum(attr_priorities.get(attr, 0) for attr in attrs)
        if score > 0:
            focus_scores[focus] = score
    
    if not focus_scores:
        return None, []
    
    best_focus = max(focus_scores.items(), key=lambda x: x[1])[0]
    return best_focus, []


TRAINABLE_ATTRS = {attr for attrs in training_focus_attrs.values() for attr in attrs}


def print_training_recommendations(df: pd.DataFrame) -> None:
    """Print detailed training recommendations with focus areas and urgency flags."""
    if 'Age' not in df.columns or 'Best Pos' not in df.columns:
        return
    print('\n' + '=' * 70)
    print('  INDIVIDUAL TRAINING FOCUS RECOMMENDATIONS')
    print('=' * 70)
    
    # Calculate squad averages for secondary attribute gaps
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    squad_averages = df[numeric_cols].mean()
    
    for _, row in df.sort_values('Age').iterrows():
        if row['Age'] >= AGE_CUTOFF:
            continue
        natural_group = classify_position(row['Best Pos'])
        if natural_group not in position_weights:
            continue
        
        weights = position_weights[natural_group]
        recs = get_training_recommendation(row, weights)
        
        # Check if all weighted attributes are already strong
        weighted_attrs_strong = all(
            row[attr] >= WEIGHTED_THRESHOLD
            for attr in weights.keys()
            if attr in row.index and pd.notna(row[attr])
        )
        
        if weighted_attrs_strong or not recs:
            # Focus on secondary attributes if weighted are strong
            secondary_attrs = position_secondary_attrs.get(natural_group, [])
            attr_priorities = {}
            for attr in secondary_attrs:
                if attr not in row.index or pd.isna(row[attr]):
                    continue
                if attr not in TRAINABLE_ATTRS:
                    continue
                if row[attr] >= ALREADY_GOOD:
                    continue
                gap = squad_averages.get(attr, 0) - row[attr]
                if gap > 0:
                    attr_priorities[attr] = gap
            
            best_focus, _ = get_best_focus(attr_priorities)
            if best_focus or attr_priorities:
                trained_str = ', '.join(
                    f"{attr} ({int(row[attr])})"
                    for attr in training_focus_attrs.get(best_focus, [])
                    if attr in attr_priorities and attr in row.index
                ) if best_focus else 'No obvious weakness'
                print(f"  {row['Player']:<22} [{natural_group:<7}]  ✅ Strong  "
                      f"{(best_focus or 'None'):<25} (trains: {trained_str})")
            else:
                print(f"  {row['Player']:<22} [{natural_group:<7}]  ✅ Strong  None")
        else:
            # Focus on weighted attributes that need training
            attr_priorities = {attr: priority for attr, val, w, priority in recs}
            best_focus, _ = get_best_focus(attr_priorities)
            
            # Check if top deficiency is critical (< 9)
            urgent = recs[0][1] < 9
            flag = '🔴 URGENT' if urgent else '📈 FOCUS '
            
            # Get trained attributes for this focus
            trained_list = []
            if best_focus:
                for attr in training_focus_attrs.get(best_focus, []):
                    if attr in row.index and pd.notna(row[attr]):
                        trained_list.append(f"{attr} ({int(row[attr])})")
            
            trained_str = ', '.join(trained_list) if trained_list else recs[0][0]
            print(f"  {row['Player']:<22} [{natural_group:<7}]  "
                  f"{flag}  {(best_focus or 'None'):<25} (trains: {trained_str})")


def generate_report(csv_path: str) -> None:
    df = load_data(csv_path)
    df = add_position_group(df)
    ratings_df = build_ratings(df)
    if ratings_df.empty:
        print('No players could be rated. Check the CSV headers and position mapping.')
        return
    alt_df = find_alternative_positions(df)

    print_position_rankings(ratings_df)
    print_misfits(alt_df)
    print_training_recommendations(df)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Attribute rating analysis for Football Manager exports.')
    parser.add_argument('csv_file', nargs='?', default=DEFAULT_CSV, help='Path to the Football Manager player export CSV file')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        generate_report(args.csv_file)
    except Exception as exc:
        print(f'ERROR: {exc}')


if __name__ == '__main__':
    main()

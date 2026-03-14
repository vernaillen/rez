#!/usr/bin/env python3
"""
Query Garmin Connect data.
Usage: garmin_query.py <command> [date]

Commands:
  sleep [date]     - Get sleep data (default: today)
  steps [date]     - Get steps data (default: today)
  heart [date]     - Get heart rate data (default: today)
  stress [date]    - Get stress data (default: today)
  body             - Get body composition
  activities [n]   - Get last n activities (default: 5)

Date format: YYYY-MM-DD
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add parent dir for potential imports
sys.path.insert(0, os.path.expanduser('~/git/health/garmin_mcp'))

def get_garmin():
    from garminconnect import Garmin
    email = os.environ.get('GARMIN_EMAIL')
    password = os.environ.get('GARMIN_PASSWORD')
    if not email or not password:
        raise ValueError("GARMIN_EMAIL and GARMIN_PASSWORD environment variables required")
    g = Garmin(email, password)
    g.login()
    return g

def format_sleep(data):
    dto = data.get('dailySleepDTO', {})
    scores = dto.get('sleepScores', {})
    overall = scores.get('overall', {})
    
    sleep_seconds = dto.get('sleepTimeSeconds') or 0
    result = {
        'sleepScore': overall.get('value'),
        'quality': overall.get('qualifierKey'),
        'duration': {
            'total': round(sleep_seconds / 3600, 1),
            'quality': scores.get('totalDuration', {}).get('qualifierKey')
        },
        'stages': {
            'deep': f"{scores.get('deepPercentage', {}).get('value') or 0}% ({scores.get('deepPercentage', {}).get('qualifierKey', 'N/A')})",
            'light': f"{scores.get('lightPercentage', {}).get('value') or 0}% ({scores.get('lightPercentage', {}).get('qualifierKey', 'N/A')})",
            'rem': f"{scores.get('remPercentage', {}).get('value') or 0}% ({scores.get('remPercentage', {}).get('qualifierKey', 'N/A')})",
        },
        'restfulness': scores.get('restlessness', {}).get('qualifierKey'),
        'stress': scores.get('stress', {}).get('qualifierKey'),
    }
    return result

def format_steps(data):
    return {
        'steps': data.get('totalSteps', 0),
        'goal': data.get('dailyStepGoal', 0),
        'distance_km': round(data.get('totalDistanceMeters', 0) / 1000, 2),
        'calories': data.get('totalKilocalories', 0)
    }

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1].lower()
    date_arg = sys.argv[2] if len(sys.argv) > 2 else datetime.now().strftime('%Y-%m-%d')
    
    try:
        g = get_garmin()
        
        if cmd == 'sleep':
            data = g.get_sleep_data(date_arg)
            print(json.dumps(format_sleep(data), indent=2))
        
        elif cmd == 'steps':
            data = g.get_steps_data(date_arg)
            print(json.dumps(format_steps(data), indent=2))
        
        elif cmd == 'heart':
            data = g.get_heart_rates(date_arg)
            print(json.dumps({
                'resting': data.get('restingHeartRate'),
                'min': data.get('minHeartRate'),
                'max': data.get('maxHeartRate'),
            }, indent=2))
        
        elif cmd == 'stress':
            data = g.get_stress_data(date_arg)
            print(json.dumps({
                'overall': data.get('overallStressLevel'),
                'rest': data.get('restStressLevel'),
                'low': data.get('lowStressDuration'),
                'medium': data.get('mediumStressDuration'),
                'high': data.get('highStressDuration'),
            }, indent=2))
        
        elif cmd == 'body':
            data = g.get_body_composition(date_arg)
            print(json.dumps({
                'weight_kg': data.get('weight', 0) / 1000,
                'bmi': data.get('bmi'),
                'body_fat': data.get('bodyFat'),
                'muscle_mass': data.get('muscleMass'),
            }, indent=2))
        
        elif cmd == 'activities':
            limit = int(date_arg) if date_arg.isdigit() else 5
            data = g.get_activities(0, limit)
            activities = [{
                'name': a.get('activityName'),
                'type': a.get('activityType', {}).get('typeKey'),
                'date': a.get('startTimeLocal'),
                'duration_min': round(a.get('duration', 0) / 60, 1),
                'distance_km': round(a.get('distance', 0) / 1000, 2),
                'calories': a.get('calories'),
            } for a in data]
            print(json.dumps(activities, indent=2))
        
        else:
            print(f"Unknown command: {cmd}")
            print(__doc__)
            sys.exit(1)
            
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()

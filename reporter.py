"""
Reporting tool for analyzing tracked activities.
Generates reports from the activity database.
"""
import sys
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Any
import csv

import database


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def get_date_range(period: str) -> tuple:
    """Get date range for period (today, yesterday, week, month)."""
    now = datetime.now()
    
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "yesterday":
        start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(hour=23, minute=59, second=59)
    elif period == "week":
        start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "month":
        start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:
        start = None
        end = None
    
    return (start.isoformat() if start else None, end.isoformat() if end else None)


def report_by_category(start_date: str = None, end_date: str = None):
    """Report time spent by category."""
    activities = database.get_activities(start_date, end_date)
    
    category_time = defaultdict(int)
    total_time = 0
    
    for activity in activities:
        duration = activity['duration_seconds']
        category = activity['category_name'] or "Uncategorized"
        category_time[category] += duration
        total_time += duration
    
    print("\n" + "=" * 60)
    print("TIME BY CATEGORY")
    print("=" * 60)
    
    if total_time == 0:
        print("No activities found in the specified period.")
        return
    
    # Sort by time spent (descending)
    sorted_categories = sorted(category_time.items(), key=lambda x: x[1], reverse=True)
    
    for category, duration in sorted_categories:
        percentage = (duration / total_time) * 100
        print(f"{category:30s} {format_duration(duration):>15s} ({percentage:5.1f}%)")
    
    print("-" * 60)
    print(f"{'TOTAL':30s} {format_duration(total_time):>15s} (100.0%)")
    print()


def report_by_application(start_date: str = None, end_date: str = None, limit: int = 20):
    """Report time spent by application."""
    activities = database.get_activities(start_date, end_date)
    
    app_time = defaultdict(int)
    total_time = 0
    
    for activity in activities:
        duration = activity['duration_seconds']
        app = activity['process_name']
        app_time[app] += duration
        total_time += duration
    
    print("\n" + "=" * 60)
    print("TIME BY APPLICATION")
    print("=" * 60)
    
    if total_time == 0:
        print("No activities found in the specified period.")
        return
    
    # Sort by time spent (descending)
    sorted_apps = sorted(app_time.items(), key=lambda x: x[1], reverse=True)
    
    for i, (app, duration) in enumerate(sorted_apps[:limit]):
        percentage = (duration / total_time) * 100
        print(f"{app:30s} {format_duration(duration):>15s} ({percentage:5.1f}%)")
    
    if len(sorted_apps) > limit:
        print(f"\n... and {len(sorted_apps) - limit} more applications")
    
    print("-" * 60)
    print(f"{'TOTAL':30s} {format_duration(total_time):>15s} (100.0%)")
    print()


def report_by_chrome_profile(start_date: str = None, end_date: str = None):
    """Report time spent by Chrome profile."""
    activities = database.get_activities(start_date, end_date)
    
    profile_time = defaultdict(int)
    total_time = 0
    
    for activity in activities:
        if activity['chrome_profile']:
            duration = activity['duration_seconds']
            profile = activity['chrome_profile']
            profile_time[profile] += duration
            total_time += duration
    
    print("\n" + "=" * 60)
    print("TIME BY CHROME PROFILE")
    print("=" * 60)
    
    if total_time == 0:
        print("No Chrome activities found in the specified period.")
        return
    
    # Sort by time spent (descending)
    sorted_profiles = sorted(profile_time.items(), key=lambda x: x[1], reverse=True)
    
    for profile, duration in sorted_profiles:
        percentage = (duration / total_time) * 100
        print(f"{profile:30s} {format_duration(duration):>15s} ({percentage:5.1f}%)")
    
    print("-" * 60)
    print(f"{'TOTAL':30s} {format_duration(total_time):>15s} (100.0%)")
    print()


def export_to_csv(start_date: str = None, end_date: str = None, output_file: str = "activities.csv"):
    """Export activities to CSV file."""
    activities = database.get_activities(start_date, end_date)
    
    if not activities:
        print("No activities found to export.")
        return
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'duration_seconds', 'process_name', 'window_title', 
                     'url', 'chrome_profile', 'category_name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for activity in activities:
            writer.writerow({
                'timestamp': activity['timestamp'],
                'duration_seconds': activity['duration_seconds'],
                'process_name': activity['process_name'],
                'window_title': activity['window_title'],
                'url': activity['url'] or '',
                'chrome_profile': activity['chrome_profile'] or '',
                'category_name': activity['category_name'] or 'Uncategorized'
            })
    
    print(f"\nExported {len(activities)} activities to {output_file}")


def daily_summary(start_date: str = None, end_date: str = None):
    """Show daily summary."""
    activities = database.get_activities(start_date, end_date)
    
    daily_time = defaultdict(int)
    
    for activity in activities:
        # Extract date from timestamp
        date = activity['timestamp'].split('T')[0]
        daily_time[date] += activity['duration_seconds']
    
    print("\n" + "=" * 60)
    print("DAILY SUMMARY")
    print("=" * 60)
    
    if not daily_time:
        print("No activities found in the specified period.")
        return
    
    # Sort by date
    for date in sorted(daily_time.keys(), reverse=True):
        duration = daily_time[date]
        print(f"{date:15s} {format_duration(duration):>15s}")
    
    print()


def main():
    """Main entry point for reporter."""
    parser = argparse.ArgumentParser(description="Activity Tracker Reporter")
    parser.add_argument('--period', choices=['today', 'yesterday', 'week', 'month', 'all'],
                       default='today', help='Time period for report')
    parser.add_argument('--start', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date (YYYY-MM-DD)')
    parser.add_argument('--category', action='store_true', help='Report by category')
    parser.add_argument('--app', action='store_true', help='Report by application')
    parser.add_argument('--profile', action='store_true', help='Report by Chrome profile')
    parser.add_argument('--daily', action='store_true', help='Daily summary')
    parser.add_argument('--export', metavar='FILE', help='Export to CSV file')
    parser.add_argument('--limit', type=int, default=20, help='Limit for application report')
    
    args = parser.parse_args()
    
    # Determine date range
    if args.start or args.end:
        start_date = args.start
        end_date = args.end
    elif args.period == 'all':
        start_date = None
        end_date = None
    else:
        start_date, end_date = get_date_range(args.period)
    
    # Show period info
    if start_date or end_date:
        print(f"\nReport Period: {start_date or 'Beginning'} to {end_date or 'Now'}")
    else:
        print("\nReport Period: All Time")
    
    # Generate reports
    if args.category:
        report_by_category(start_date, end_date)
    
    if args.app:
        report_by_application(start_date, end_date, args.limit)
    
    if args.profile:
        report_by_chrome_profile(start_date, end_date)
    
    if args.daily:
        daily_summary(start_date, end_date)
    
    if args.export:
        export_to_csv(start_date, end_date, args.export)
    
    # Default: show all reports if none specified
    if not any([args.category, args.app, args.profile, args.daily, args.export]):
        report_by_category(start_date, end_date)
        report_by_application(start_date, end_date, args.limit)
        daily_summary(start_date, end_date)


if __name__ == "__main__":
    main()

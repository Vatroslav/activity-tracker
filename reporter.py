"""
Activity Reporter - CLI tool for generating activity reports.
"""

import sys
import argparse
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tabulate import tabulate
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
    """Get start and end date for a period."""
    now = datetime.now()
    
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "yesterday":
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif period == "week":
        # Start of current week (Monday)
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:
        start = None
        end = None
    
    return (start.isoformat() if start else None, end.isoformat() if end else None)


def report_by_category(start_date: str = None, end_date: str = None, output_format: str = "table"):
    """Generate a report of time spent by category."""
    results = database.get_activity_summary_by_category(start_date, end_date)
    
    if not results:
        print("No activity data found.")
        return
    
    # Prepare data for display
    table_data = []
    
    # Calculate total first
    total_seconds = sum(row['total_seconds'] for row in results)
    
    for row in results:
        category_name = row['category_name'] if row['category_name'] else "Uncategorized"
        duration = row['total_seconds']
        count = row['activity_count']
        
        # Calculate percentage - handle zero case
        if total_seconds > 0:
            percentage = f"{(duration / total_seconds) * 100:.1f}%"
        else:
            percentage = "0.0%"
        
        table_data.append([
            category_name,
            format_duration(duration),
            count,
            percentage
        ])
    
    # Add total row
    table_data.append([
        "TOTAL",
        format_duration(total_seconds),
        sum(r['activity_count'] for r in results),
        "100.0%" if total_seconds > 0 else "0.0%"
    ])
    
    if output_format == "csv":
        # Output as CSV
        writer = csv.writer(sys.stdout)
        writer.writerow(["Category", "Duration", "Activity Count", "Percentage"])
        for row in table_data:
            writer.writerow(row)
    else:
        # Output as table
        headers = ["Category", "Duration", "Count", "Percentage"]
        print("\nActivity Summary by Category")
        print("=" * 80)
        print(tabulate(table_data, headers=headers, tablefmt="grid"))


def report_by_process(start_date: str = None, end_date: str = None, output_format: str = "table", limit: int = 20):
    """Generate a report of time spent by process."""
    results = database.get_activity_summary_by_process(start_date, end_date)
    
    if not results:
        print("No activity data found.")
        return
    
    # Limit results
    results = results[:limit]
    
    # Prepare data for display
    table_data = []
    
    # Calculate total first
    total_seconds = sum(r['total_seconds'] for r in results)
    
    for row in results:
        process_name = row['process_name']
        duration = row['total_seconds']
        count = row['activity_count']
        
        # Calculate percentage - handle zero case
        if total_seconds > 0:
            percentage = f"{(duration / total_seconds) * 100:.1f}%"
        else:
            percentage = "0.0%"
        
        table_data.append([
            process_name,
            format_duration(duration),
            count,
            percentage
        ])
    
    # Add total row
    table_data.append([
        "TOTAL (shown)",
        format_duration(total_seconds),
        sum(r['activity_count'] for r in results),
        "100.0%" if total_seconds > 0 else "0.0%"
    ])
    
    if output_format == "csv":
        # Output as CSV
        writer = csv.writer(sys.stdout)
        writer.writerow(["Process", "Duration", "Activity Count", "Percentage"])
        for row in table_data:
            writer.writerow(row)
    else:
        # Output as table
        headers = ["Process", "Duration", "Count", "Percentage"]
        print("\nActivity Summary by Process")
        print("=" * 80)
        print(tabulate(table_data, headers=headers, tablefmt="grid"))


def report_by_chrome_profile(start_date: str = None, end_date: str = None, output_format: str = "table"):
    """Generate a report of time spent by Chrome profile."""
    results = database.get_activity_summary_by_chrome_profile(start_date, end_date)
    
    if not results:
        print("No Chrome activity data found.")
        return
    
    # Prepare data for display
    table_data = []
    
    # Calculate total first
    total_seconds = sum(row['total_seconds'] for row in results)
    
    for row in results:
        profile_name = row['chrome_profile']
        duration = row['total_seconds']
        count = row['activity_count']
        
        # Calculate percentage - handle zero case
        if total_seconds > 0:
            percentage = f"{(duration / total_seconds) * 100:.1f}%"
        else:
            percentage = "0.0%"
        
        table_data.append([
            profile_name,
            format_duration(duration),
            count,
            percentage
        ])
    
    # Add total row
    table_data.append([
        "TOTAL",
        format_duration(total_seconds),
        sum(r['activity_count'] for r in results),
        "100.0%" if total_seconds > 0 else "0.0%"
    ])
    
    if output_format == "csv":
        # Output as CSV
        writer = csv.writer(sys.stdout)
        writer.writerow(["Chrome Profile", "Duration", "Activity Count", "Percentage"])
        for row in table_data:
            writer.writerow(row)
    else:
        # Output as table
        headers = ["Chrome Profile", "Duration", "Count", "Percentage"]
        print("\nActivity Summary by Chrome Profile")
        print("=" * 80)
        print(tabulate(table_data, headers=headers, tablefmt="grid"))


def list_activities(start_date: str = None, end_date: str = None, limit: int = 50):
    """List recent activities."""
    logs = database.get_activity_logs(start_date, end_date)
    
    if not logs:
        print("No activity data found.")
        return
    
    # Limit results
    logs = logs[:limit]
    
    # Prepare data for display
    table_data = []
    
    for log in logs:
        timestamp = datetime.fromisoformat(log['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        duration = format_duration(log['duration_seconds'])
        process = log['process_name']
        title = log['window_title'][:50] + "..." if len(log['window_title']) > 50 else log['window_title']
        url = (log['url'][:40] + "...") if log['url'] and len(log['url']) > 40 else (log['url'] or "N/A")
        
        table_data.append([
            timestamp,
            duration,
            process,
            title,
            url
        ])
    
    headers = ["Timestamp", "Duration", "Process", "Window Title", "URL"]
    print("\nRecent Activities")
    print("=" * 150)
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def main():
    """Main entry point for the reporter CLI."""
    parser = argparse.ArgumentParser(description="Activity Tracker Reporter")
    
    parser.add_argument(
        "report_type",
        choices=["category", "process", "chrome", "list"],
        help="Type of report to generate"
    )
    
    parser.add_argument(
        "-p", "--period",
        choices=["today", "yesterday", "week", "month", "all"],
        default="today",
        help="Time period for the report (default: today)"
    )
    
    parser.add_argument(
        "-s", "--start-date",
        help="Start date in ISO format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
    )
    
    parser.add_argument(
        "-e", "--end-date",
        help="End date in ISO format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
    )
    
    parser.add_argument(
        "-f", "--format",
        choices=["table", "csv"],
        default="table",
        help="Output format (default: table)"
    )
    
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=20,
        help="Limit number of results (default: 20)"
    )
    
    args = parser.parse_args()
    
    # Initialize database (in case it doesn't exist)
    database.initialize_database()
    
    # Determine date range
    if args.start_date or args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    elif args.period == "all":
        start_date = None
        end_date = None
    else:
        start_date, end_date = get_date_range(args.period)
    
    # Display date range
    if start_date or end_date:
        print(f"\nDate Range: {start_date or 'beginning'} to {end_date or 'now'}")
    else:
        print("\nDate Range: All time")
    
    # Generate report
    if args.report_type == "category":
        report_by_category(start_date, end_date, args.format)
    elif args.report_type == "process":
        report_by_process(start_date, end_date, args.format, args.limit)
    elif args.report_type == "chrome":
        report_by_chrome_profile(start_date, end_date, args.format)
    elif args.report_type == "list":
        list_activities(start_date, end_date, args.limit)


if __name__ == "__main__":
    main()

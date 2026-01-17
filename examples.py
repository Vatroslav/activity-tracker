"""
Quick start guide and examples for Activity Tracker.
This script demonstrates common usage patterns.
"""

def example_add_custom_category():
    """Example: Add a custom category with rules."""
    import database
    
    # Initialize database
    database.initialize_database()
    
    # Add a custom category
    gaming_id = database.add_category(
        name="Gaming",
        color="#FF1744",
        description="Video games and entertainment"
    )
    
    # Add rules for this category
    database.add_category_rule(
        pattern=r"steam",
        match_field="process_name",
        category_id=gaming_id,
        priority=10
    )
    
    database.add_category_rule(
        pattern=r"(game|gaming)",
        match_field="window_title",
        category_id=gaming_id,
        priority=8
    )
    
    print(f"✓ Added Gaming category (ID: {gaming_id}) with 2 rules")


def example_list_categories():
    """Example: List all categories and their rules."""
    import database
    
    database.initialize_database()
    
    categories = database.get_all_categories()
    rules = database.get_all_category_rules()
    
    print("\n=== CATEGORIES ===")
    for cat in categories:
        print(f"\n{cat['name']} (ID: {cat['id']})")
        print(f"  Color: {cat['color']}")
        print(f"  Description: {cat['description']}")
        
        # Find rules for this category
        cat_rules = [r for r in rules if r['category_id'] == cat['id']]
        if cat_rules:
            print(f"  Rules:")
            for rule in cat_rules:
                print(f"    - {rule['match_field']}: {rule['pattern']} (priority: {rule['priority']})")


def example_query_activities():
    """Example: Query activities with custom filters."""
    import database
    from datetime import datetime, timedelta
    
    database.initialize_database()
    
    # Get activities from the last 7 days
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    activities = database.get_activity_logs(start_date=week_ago)
    
    print(f"\n=== ACTIVITIES (last 7 days) ===")
    print(f"Total activities: {len(activities)}")
    
    if activities:
        print(f"\nMost recent:")
        for activity in activities[:5]:
            print(f"  {activity['timestamp']}: {activity['process_name']} ({activity['duration_seconds']}s)")


def example_generate_reports():
    """Example: Generate various reports programmatically."""
    import database
    from datetime import datetime, timedelta
    
    database.initialize_database()
    
    # Get today's date range
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    print("\n=== TODAY'S SUMMARY ===")
    
    # Category summary
    cat_summary = database.get_activity_summary_by_category(
        start_date=today.isoformat()
    )
    
    print("\nBy Category:")
    for row in cat_summary:
        cat_name = row['category_name'] or "Uncategorized"
        hours = row['total_seconds'] / 3600
        print(f"  {cat_name}: {hours:.2f} hours")
    
    # Process summary
    proc_summary = database.get_activity_summary_by_process(
        start_date=today.isoformat()
    )
    
    print("\nBy Process:")
    for row in proc_summary[:5]:  # Top 5
        hours = row['total_seconds'] / 3600
        print(f"  {row['process_name']}: {hours:.2f} hours")


if __name__ == "__main__":
    print("Activity Tracker - Quick Start Examples")
    print("=" * 50)
    
    print("\n1. List existing categories and rules:")
    example_list_categories()
    
    print("\n2. Query recent activities:")
    example_query_activities()
    
    print("\n3. Generate reports:")
    example_generate_reports()
    
    print("\n" + "=" * 50)
    print("\nTo add a custom category, uncomment and run:")
    print("  example_add_custom_category()")

"""
Example script for adding categories and rules to the Activity Tracker.

Run this script to add some sample categories and rules to get started.
You can modify this file to add your own categories and rules.
"""

import database


def setup_sample_categories():
    """Set up sample categories and rules."""
    
    # Initialize database
    database.initialize_database()
    
    print("Setting up sample categories and rules...\n")
    
    # Add categories
    print("Adding categories...")
    
    work_id = database.add_category(
        "Work",
        "#0078D4",
        "Work-related activities"
    )
    print(f"  ✓ Added category: Work (ID: {work_id})")
    
    dev_id = database.add_category(
        "Development",
        "#4CAF50",
        "Software development"
    )
    print(f"  ✓ Added category: Development (ID: {dev_id})")
    
    social_id = database.add_category(
        "Social Media",
        "#FF6B6B",
        "Social media and entertainment"
    )
    print(f"  ✓ Added category: Social Media (ID: {social_id})")
    
    learning_id = database.add_category(
        "Learning",
        "#9C27B0",
        "Educational content and courses"
    )
    print(f"  ✓ Added category: Learning (ID: {learning_id})")
    
    communication_id = database.add_category(
        "Communication",
        "#FF9800",
        "Email, chat, and meetings"
    )
    print(f"  ✓ Added category: Communication (ID: {communication_id})")
    
    # Add category rules
    print("\nAdding category rules...")
    
    # Development rules (high priority)
    database.add_category_rule(r"github\.com", "url", dev_id, priority=15)
    print("  ✓ Added rule: github.com → Development")
    
    database.add_category_rule(r"stackoverflow\.com", "url", dev_id, priority=15)
    print("  ✓ Added rule: stackoverflow.com → Development")
    
    database.add_category_rule(r"Visual Studio Code", "window_title", dev_id, priority=15)
    print("  ✓ Added rule: VS Code → Development")
    
    database.add_category_rule(r"PyCharm", "window_title", dev_id, priority=15)
    print("  ✓ Added rule: PyCharm → Development")
    
    # Social media rules (medium priority)
    database.add_category_rule(r"facebook\.com", "url", social_id, priority=10)
    print("  ✓ Added rule: facebook.com → Social Media")
    
    database.add_category_rule(r"twitter\.com|x\.com", "url", social_id, priority=10)
    print("  ✓ Added rule: twitter.com/x.com → Social Media")
    
    database.add_category_rule(r"instagram\.com", "url", social_id, priority=10)
    print("  ✓ Added rule: instagram.com → Social Media")
    
    database.add_category_rule(r"reddit\.com", "url", social_id, priority=10)
    print("  ✓ Added rule: reddit.com → Social Media")
    
    database.add_category_rule(r"youtube\.com", "url", social_id, priority=10)
    print("  ✓ Added rule: youtube.com → Social Media")
    
    # Learning rules (medium priority)
    database.add_category_rule(r"udemy\.com", "url", learning_id, priority=12)
    print("  ✓ Added rule: udemy.com → Learning")
    
    database.add_category_rule(r"coursera\.org", "url", learning_id, priority=12)
    print("  ✓ Added rule: coursera.org → Learning")
    
    database.add_category_rule(r"pluralsight\.com", "url", learning_id, priority=12)
    print("  ✓ Added rule: pluralsight.com → Learning")
    
    database.add_category_rule(r"docs\.python\.org", "url", learning_id, priority=12)
    print("  ✓ Added rule: Python docs → Learning")
    
    # Communication rules (medium priority)
    database.add_category_rule(r"outlook|mail", "window_title", communication_id, priority=10)
    print("  ✓ Added rule: Email clients → Communication")
    
    database.add_category_rule(r"slack\.com", "url", communication_id, priority=10)
    print("  ✓ Added rule: slack.com → Communication")
    
    database.add_category_rule(r"teams\.microsoft\.com", "url", communication_id, priority=10)
    print("  ✓ Added rule: Microsoft Teams → Communication")
    
    database.add_category_rule(r"zoom", "window_title", communication_id, priority=10)
    print("  ✓ Added rule: Zoom → Communication")
    
    # Work rules (low priority - catches general work apps)
    database.add_category_rule(r"EXCEL\.EXE", "process_name", work_id, priority=5)
    print("  ✓ Added rule: Excel → Work")
    
    database.add_category_rule(r"WINWORD\.EXE", "process_name", work_id, priority=5)
    print("  ✓ Added rule: Word → Work")
    
    database.add_category_rule(r"POWERPNT\.EXE", "process_name", work_id, priority=5)
    print("  ✓ Added rule: PowerPoint → Work")
    
    print("\n✅ Sample categories and rules added successfully!")
    print("\nYou can now start the tracker with: python tracker.py")
    print("Generate reports with: python reporter.py category -p today")


def list_all_categories():
    """List all existing categories and rules."""
    print("\n" + "="*80)
    print("EXISTING CATEGORIES")
    print("="*80)
    
    categories = database.get_all_categories()
    
    if not categories:
        print("No categories found.")
        return
    
    for cat in categories:
        print(f"\nCategory ID: {cat['id']}")
        print(f"  Name: {cat['name']}")
        print(f"  Color: {cat['color']}")
        print(f"  Description: {cat['description']}")
    
    print("\n" + "="*80)
    print("EXISTING RULES")
    print("="*80)
    
    rules = database.get_all_category_rules()
    
    if not rules:
        print("No rules found.")
        return
    
    for rule in rules:
        # Get category name
        cat = next((c for c in categories if c['id'] == rule['category_id']), None)
        cat_name = cat['name'] if cat else "Unknown"
        
        print(f"\nRule ID: {rule['id']}")
        print(f"  Pattern: {rule['pattern']}")
        print(f"  Match Field: {rule['match_field']}")
        print(f"  Category: {cat_name}")
        print(f"  Priority: {rule['priority']}")


def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        database.initialize_database()
        list_all_categories()
    else:
        setup_sample_categories()
        list_all_categories()


if __name__ == "__main__":
    main()

"""
Example script to set up categories and rules for the activity tracker.
Run this after installing the tracker to create initial categories.
"""
import database

def setup_categories():
    """Setup example categories and rules."""
    
    # Initialize database
    database.initialize_database()
    print("Database initialized")
    
    # Create categories
    print("\nCreating categories...")
    
    work_id = database.add_category(
        "Work",
        "#4CAF50",
        "Work-related activities"
    )
    print(f"  ✓ Work category created (ID: {work_id})")
    
    entertainment_id = database.add_category(
        "Entertainment",
        "#FF5722",
        "Entertainment and social media"
    )
    print(f"  ✓ Entertainment category created (ID: {entertainment_id})")
    
    communication_id = database.add_category(
        "Communication",
        "#2196F3",
        "Email and messaging"
    )
    print(f"  ✓ Communication category created (ID: {communication_id})")
    
    learning_id = database.add_category(
        "Learning",
        "#9C27B0",
        "Educational content and courses"
    )
    print(f"  ✓ Learning category created (ID: {learning_id})")
    
    # Create rules for Work category
    print("\nCreating rules for Work category...")
    
    database.add_category_rule(
        r"github\.com",
        "url",
        work_id,
        priority=10
    )
    print("  ✓ GitHub URLs → Work")
    
    database.add_category_rule(
        r"stackoverflow\.com",
        "url",
        work_id,
        priority=10
    )
    print("  ✓ Stack Overflow URLs → Work")
    
    database.add_category_rule(
        r"code\.exe",
        "process_name",
        work_id,
        priority=8
    )
    print("  ✓ VS Code → Work")
    
    database.add_category_rule(
        r"pycharm.*\.exe",
        "process_name",
        work_id,
        priority=8
    )
    print("  ✓ PyCharm → Work")
    
    # Create rules for Entertainment category
    print("\nCreating rules for Entertainment category...")
    
    database.add_category_rule(
        r"youtube\.com",
        "url",
        entertainment_id,
        priority=10
    )
    print("  ✓ YouTube URLs → Entertainment")
    
    database.add_category_rule(
        r"netflix\.com",
        "url",
        entertainment_id,
        priority=10
    )
    print("  ✓ Netflix URLs → Entertainment")
    
    database.add_category_rule(
        r"reddit\.com",
        "url",
        entertainment_id,
        priority=8
    )
    print("  ✓ Reddit URLs → Entertainment")
    
    database.add_category_rule(
        r"twitter\.com|x\.com",
        "url",
        entertainment_id,
        priority=8
    )
    print("  ✓ Twitter/X URLs → Entertainment")
    
    # Create rules for Communication category
    print("\nCreating rules for Communication category...")
    
    database.add_category_rule(
        r"mail\.google\.com|outlook\.live\.com",
        "url",
        communication_id,
        priority=10
    )
    print("  ✓ Email URLs → Communication")
    
    database.add_category_rule(
        r"slack\.exe",
        "process_name",
        communication_id,
        priority=10
    )
    print("  ✓ Slack → Communication")
    
    database.add_category_rule(
        r"teams\.exe",
        "process_name",
        communication_id,
        priority=10
    )
    print("  ✓ Microsoft Teams → Communication")
    
    # Create rules for Learning category
    print("\nCreating rules for Learning category...")
    
    database.add_category_rule(
        r"udemy\.com|coursera\.org|edx\.org",
        "url",
        learning_id,
        priority=10
    )
    print("  ✓ Online course URLs → Learning")
    
    database.add_category_rule(
        r"docs\.python\.org|docs\.microsoft\.com|developer\.mozilla\.org",
        "url",
        learning_id,
        priority=9
    )
    print("  ✓ Documentation URLs → Learning")
    
    print("\n" + "=" * 60)
    print("✓ Setup complete!")
    print("=" * 60)
    print("\nCategories created:")
    for cat in database.get_categories():
        print(f"  - {cat['name']} ({cat['color']})")
    
    print(f"\nTotal rules created: {len(database.get_all_category_rules())}")
    print("\nYou can now start the tracker with: python tracker.py")


if __name__ == "__main__":
    setup_categories()

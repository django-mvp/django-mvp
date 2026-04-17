"""
Context processor for Demo App navbar widgets.

Provides sample notification data for demonstration purposes.
"""


def navbar_widgets(request):
    """
    Provide sample navbar widget data for all Demo App pages.

    This ensures navbar widgets have demo data even when views don't
    explicitly provide it.
    """
    # Sample notifications for demo purposes
    notifications = [
        {"text": "Welcome to Django MVP!", "time": "Just now"},
        {"text": "Check out the navbar widgets demo", "time": "2 mins ago"},
        {"text": "All tests passing ✓", "time": "5 mins ago"},
    ]

    # Sample messages for demo purposes
    messages = [
        {
            "sender_name": "Alice Johnson",
            "sender_avatar": "https://i.pravatar.cc/150?img=1",
            "message": "Hey! Just wanted to check if you're coming to the meeting tomorrow. Let me know!",
            "timestamp": "2 mins ago",
            "link": "#",
        },
        {
            "sender_name": "Bob Smith",
            "message": "Thanks for your help with the project yesterday. Really appreciated!",
            "timestamp": "1 hour ago",
            "link": "#",
        },
        {
            "sender_name": "Carol Williams",
            "sender_avatar": "https://i.pravatar.cc/150?img=5",
            "message": "Quick question: Do you have the latest design files? I need them for the presentation.",
            "timestamp": "3 hours ago",
            "link": "#",
        },
    ]

    # User avatar and member_since for user widget
    user_avatar = None
    user_member_since = None

    # Only access request.user if it exists (may not be available in tests)
    if hasattr(request, "user") and request.user.is_authenticated:
        # Try to get user avatar from profile (if exists)
        if hasattr(request.user, "profile") and hasattr(request.user.profile, "avatar"):
            user_avatar = (
                request.user.profile.avatar.url if request.user.profile.avatar else None
            )

        # Calculate member_since from date_joined
        if hasattr(request.user, "date_joined"):
            user_member_since = (
                f"Member since {request.user.date_joined.strftime('%b %Y')}"
            )

    return {
        "notifications_count": len(notifications),
        "notifications": notifications,
        "messages_count": len(messages),
        "messages": messages,
        "user_avatar": user_avatar,
        "user_member_since": user_member_since,
    }

"""Example menu configuration showing all django-mvp menu features.

This file demonstrates how to use the AppMenu system to create comprehensive
navigation menus with all available features:

- Single menu items with icons
- Hierarchical menu groups and sections
- Badge support for notifications
- Active state detection
- URL resolution (view names and direct URLs)
- Multi-level nesting
- Menu sections with headers
"""

from flex_menu import MenuItem

from mvp.menus import AppMenu, MenuGroup

AppMenu.extend(
    [
        # Home
        MenuItem(
            name="home",
            view_name="home",
            extra_context={
                "label": "Home",
                "icon": "home",
            },
        ),
        # Layout Demo
        MenuItem(
            name="layout_demo",
            view_name="layout_demo",
            extra_context={
                "label": "Layout Demo",
                "icon": "box-seam",
            },
        ),
        # Navbar Widgets
        MenuItem(
            name="navbar_widgets_demo",
            view_name="navbar_widgets_demo",
            extra_context={
                "label": "Navbar Widgets",
                "icon": "grid",
                "badge": "MVP",
                "badge_classes": "text-bg-primary",
            },
        ),
        MenuItem(
            name="page_layout_demo",
            view_name="page_layout_demo",
            extra_context={
                "label": "Inner Layout",
                "icon": "sidebar",
            },
        ),
        # List View Demos
        MenuGroup(
            name="list_views",
            extra_context={
                "label": "List Views",
                "icon": "list",
            },
            children=[
                MenuItem(
                    name="list_view_full_demo",
                    view_name="list_view_demo",
                    extra_context={
                        "label": "Full Demo",
                        "icon": "list",
                        "badge": "All Features",
                        "badge_classes": "text-bg-primary",
                    },
                ),
                MenuItem(
                    name="basic_list_demo",
                    view_name="basic_list_demo",
                    extra_context={
                        "label": "Basic ListView",
                        "icon": "list",
                    },
                ),
                MenuItem(
                    name="minimal_list_demo",
                    view_name="minimal_list_demo",
                    extra_context={
                        "label": "Minimal",
                        "icon": "list",
                    },
                ),
            ],
        ),
        # Form View Demos
        MenuGroup(
            name="mvp_forms",
            extra_context={
                "label": "Form Views",
                "icon": "form",
            },
            children=[
                MenuItem(
                    name="contact_form",
                    view_name="contact_form",
                    extra_context={
                        "label": "Contact Form",
                        "icon": "book",  # Using available Bootstrap icon
                        "badge": "NEW",
                        "badge_classes": "text-bg-success",
                    },
                ),
                MenuItem(
                    name="product_create",
                    view_name="product_create",
                    extra_context={
                        "label": "Create Product",
                        "icon": "add",
                        "badge": "NEW",
                        "badge_classes": "text-bg-info",
                    },
                ),
                MenuItem(
                    name="explicit_renderer_demo",
                    view_name="explicit_renderer_demo",
                    extra_context={
                        "label": "Explicit Renderer",
                        "icon": "code-slash",
                        "badge": "NEW",
                        "badge_classes": "text-bg-warning",
                    },
                ),
                # Note: Edit Product would need dynamic pk - linking to products list instead
                # MenuItem for editing will be added dynamically from product list view
            ],
        ),
        # 3rd party integration demos - shows how to link to external apps or features
        MenuGroup(
            name="integrations_section",
            extra_context={"label": "INTEGRATIONS", "component_type": "menu.group"},
            children=[
                MenuItem(
                    name="datatables_demo",
                    view_name="datatables_demo",
                    extra_context={
                        "label": "DataTables Demo",
                        "icon": "table",
                    },
                )
            ],
        ),
        # Extra resources with external links to github and documentation
        MenuGroup(
            name="resources_section",
            extra_context={"label": "Resources"},
            children=[
                MenuItem(
                    name="external_link",
                    url="https://github.com/SamuelJennings/django-mvp",
                    extra_context={
                        "label": "GitHub Repository",
                        "icon": "github",
                    },
                ),
                MenuItem(
                    name="documentation",
                    url="https://samueljennings.github.io/django-cotton-bs5/",
                    extra_context={
                        "label": "Documentation",
                        "icon": "book",
                    },
                ),
            ],
        ),
    ]
)

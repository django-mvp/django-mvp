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

from mvp.menus import AppMenu, MenuCollapse, MenuGroup

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
        MenuCollapse(
            name="crud_views",
            extra_context={
                "label": "App Layout",
                "icon": "layout",
            },
            children=[
                # Layout Demo
                MenuItem(
                    name="layout_demo",
                    view_name="layout_demo",
                    extra_context={
                        "label": "Configuration",
                        "icon": "settings",
                    },
                ),
                # Navbar Widgets
                MenuItem(
                    name="navbar_widgets_demo",
                    view_name="navbar_widgets_demo",
                    extra_context={
                        "label": "Navbar",
                        "icon": "grid",
                    },
                ),
                MenuItem(
                    name="app_sidebar",
                    view_name="navbar_widgets_demo",
                    extra_context={
                        "label": "Sidebar",
                        "icon": "sidebar-left",
                    },
                ),
            ],
        ),
        # MenuItem(
        #     name="page_layout_demo",
        #     view_name="page_layout_demo",
        #     extra_context={
        #         "label": "Inner Layout",
        #         "icon": "sidebar",
        #     },
        # ),
        MenuItem(
            name="scss_variables_demo",
            view_name="scss_variables_demo",
            extra_context={
                "label": "Theme Customization",
                "icon": "code-slash",
            },
        ),
        # List View Demos
        MenuGroup(
            name="crud_views",
            extra_context={
                "label": "CRUD Views",
            },
            children=[
                MenuItem(
                    name="product-list",
                    view_name="product-list",
                    extra_context={
                        "label": "Product List",
                        "icon": "list",
                    },
                ),
                MenuItem(
                    name="datatables_demo",
                    view_name="datatables_demo",
                    extra_context={
                        "label": "Product Table",
                        "icon": "table",
                        "badge": "add-on",
                        "badge_classes": "text-bg-info",
                    },
                ),
                MenuItem(
                    name="product_create",
                    view_name="product-create",
                    extra_context={
                        "label": "Create Product",
                        "icon": "add",
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
                    name="htmx_demo",
                    view_name="htmx_demo",
                    extra_context={
                        "label": "HTMX Form Demo",
                        "icon": "form",
                    },
                ),
            ],
        ),
        # 3rd party integration demos - shows how to link to external apps or features
        # MenuGroup(
        #     name="integrations_section",
        #     extra_context={"label": "INTEGRATIONS", "component_type": "menu.group"},
        #     children=[
        #     ],
        # ),
        # Extra resources with external links to github and documentation
        MenuGroup(
            name="pages",
            extra_context={"label": "Pages"},
            children=[
                MenuCollapse(
                    name="error_previews",
                    extra_context={
                        "label": "Error Pages",
                        "icon": "exclamation-circle",
                    },
                    children=[
                        MenuItem(
                            name="error-preview-400",
                            view_name="error-preview-400",
                            extra_context={
                                "label": "400 Bad Request",
                                "icon": "exclamation-circle",
                            },
                        ),
                        MenuItem(
                            name="error-preview-403",
                            view_name="error-preview-403",
                            extra_context={
                                "label": "403 Forbidden",
                                "icon": "shield-x",
                            },
                        ),
                        MenuItem(
                            name="error-preview-404",
                            view_name="error-preview-404",
                            extra_context={
                                "label": "404 Not Found",
                                "icon": "search",
                            },
                        ),
                        MenuItem(
                            name="error-preview-500",
                            view_name="error-preview-500",
                            extra_context={
                                "label": "500 Server Error",
                                "icon": "bug",
                            },
                        ),
                    ],
                )
            ],
        ),
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

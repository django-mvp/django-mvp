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

from django.urls import reverse_lazy
from flex_menu import MenuItem

from demo.component_docs import COMPONENTS
from mvp.menus import AppMenu, MenuCollapse, MenuGroup

AppMenu.extend(
    [
        MenuItem(
            name="home",
            view_name="home",
            extra_context={
                "label": "Home",
                "icon": "home",
            },
        ),
        MenuItem(
            name="layout",
            view_name="layout",
            extra_context={
                "label": "Layout",
                "icon": "layout",
            },
        ),
        MenuItem(
            name="customization",
            view_name="customization",
            extra_context={
                "label": "Theme Customization",
                "icon": "gears",
            },
        ),
        MenuCollapse(
            name="custom-components",
            extra_context={
                "label": "Components",
                "icon": "code-slash",
            },
            children=[
                MenuItem(
                    name="components-overview",
                    view_name="custom-components",
                    extra_context={
                        "label": "Overview",
                        "icon": "grid",
                    },
                ),
                *[
                    MenuItem(
                        name=f"component-{component.slug}",
                        url=reverse_lazy(
                            "component-doc", kwargs={"slug": component.slug}
                        ),
                        extra_context={
                            "label": component.label,
                            "icon": component.icon,
                        },
                    )
                    for component in COMPONENTS
                ],
            ],
        ),
        MenuGroup(
            name="pages",
            extra_context={"label": "Demo Pages"},
            children=[
                MenuItem(
                    name="product-list",
                    view_name="product-list",
                    extra_context={
                        "label": "List Page",
                        "icon": "list",
                    },
                ),
                MenuCollapse(
                    name="errors",
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
                ),
            ],
        ),
        MenuGroup(
            name="integrations",
            extra_context={
                "label": "Integrations",
            },
            children=[
                MenuItem(
                    name="django-tables-2",
                    view_name="djangotables2",
                    extra_context={
                        "label": "Django Tables 2",
                        "icon": "table",
                    },
                ),
            ],
        ),
        MenuGroup(
            name="resources",
            extra_context={"label": "Resources"},
            children=[
                MenuItem(
                    name="external_link",
                    url="https://github.com/django-mvp/django-mvp",
                    extra_context={
                        "label": "GitHub Repository",
                        "icon": "github",
                    },
                ),
                MenuItem(
                    name="documentation",
                    url="https://github.com/django-mvp/django-mvp",
                    extra_context={
                        "label": "Documentation",
                        "icon": "book",
                    },
                ),
            ],
        ),
    ]
)

1. MVP App

- A set of related cotton components that allow users to set up the AdminLTE4 style app shell using nothing but django-cotton components and template overrides, without any custom Python code.
- Must provide the following main components:
  - <c-app>: Main layout component that wraps header, sidebar, and content area
  - <c-app.header>: Top navigation bar with branding, sidebar toggle and custom widgets
  - <c-app.sidebar>: Collapsible side navigation with support for nested and grouped menus.
  - <c-app.main>: Main area for rendering page content
  - <c-app.footer>: Optional footer for additional information or actions.

1. MVP Page

- A set of related cotton components that allow users to set up a configurable MVP page using nothing but django-cotton components.
- Must provide the following main components:
  - <c-page>: Main page layout component that wraps header and content area
  - <c-mvp-toolbar>: Page header with title, description and action buttons
  - <c-page.content>: Main area for rendering page content.
  - <c-page.footer>: Optional page footer for additional information or actions.

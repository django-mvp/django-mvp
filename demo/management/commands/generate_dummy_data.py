"""Management command to generate dummy data for examples."""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from demo.models import Article, Category, Product, Task


class Command(BaseCommand):
    """Generate dummy data for demonstrating list and detail views."""

    help = "Generate dummy data for examples"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before generating new data",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            Product.objects.all().delete()
            Article.objects.all().delete()
            Task.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ Data cleared"))

        self.stdout.write("Generating dummy data...")

        # Create categories
        categories = self.create_categories()
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(categories)} categories"))

        # Create products
        products = self.create_products(categories)
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(products)} products"))

        # Create articles
        articles = self.create_articles(categories)
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(articles)} articles"))

        # Create tasks
        tasks = self.create_tasks(categories)
        self.stdout.write(self.style.SUCCESS(f"✓ Created {len(tasks)} tasks"))

        self.stdout.write(
            self.style.SUCCESS("\n✓ All dummy data generated successfully!")
        )

    def create_categories(self):
        """Create category instances."""
        category_data = [
            {
                "name": "Electronics",
                "icon": "cpu",
                "color": "primary",
                "description": "Electronic devices and gadgets",
            },
            {
                "name": "Clothing",
                "icon": "shirt",
                "color": "success",
                "description": "Fashion and apparel",
            },
            {
                "name": "Books",
                "icon": "book",
                "color": "info",
                "description": "Books and publications",
            },
            {
                "name": "Home & Garden",
                "icon": "home",
                "color": "warning",
                "description": "Home improvement and gardening",
            },
            {
                "name": "Sports",
                "icon": "bicycle",
                "color": "danger",
                "description": "Sports equipment and gear",
            },
            {
                "name": "Technology",
                "icon": "laptop",
                "color": "secondary",
                "description": "Tech news and reviews",
            },
            {
                "name": "Health",
                "icon": "heart",
                "color": "pink",
                "description": "Health and wellness",
            },
            {
                "name": "Business",
                "icon": "briefcase",
                "color": "dark",
                "description": "Business and finance",
            },
        ]

        categories = []
        for data in category_data:
            category, _created = Category.objects.get_or_create(
                slug=slugify(data["name"]),
                defaults={
                    "name": data["name"],
                    "icon": data["icon"],
                    "color": data["color"],
                    "description": data["description"],
                    "is_active": True,
                },
            )
            categories.append(category)

        return categories

    def create_products(self, categories):
        """Create product instances."""
        product_names = [
            "Wireless Headphones",
            "Smart Watch",
            "Laptop Stand",
            "Mechanical Keyboard",
            "USB-C Hub",
            "Portable Charger",
            "Bluetooth Speaker",
            "Webcam HD",
            "Ergonomic Mouse",
            "LED Desk Lamp",
            "Phone Case",
            "Screen Protector",
            "Cable Organizer",
            "Laptop Bag",
            "Wireless Earbuds",
            "Gaming Controller",
            "External SSD",
            "Monitor Arm",
            "Docking Station",
            "Microphone",
            "T-Shirt Classic",
            "Jeans Slim Fit",
            "Sneakers Running",
            "Hoodie Premium",
            "Jacket Winter",
            "Backpack Travel",
            "Hat Baseball",
            "Socks Cotton",
            "Programming Guide",
            "Design Patterns",
            "Clean Code",
            "Data Science Handbook",
        ]

        products = []
        for i, name in enumerate(product_names):
            category = random.choice(
                categories[:5]
            )  # Use first 5 categories for products
            product, _created = Product.objects.get_or_create(
                slug=slugify(f"{name}-{i}"),
                defaults={
                    "name": name,
                    "category": category,
                    "description": f"This is a detailed description of {name}. "
                    f"It features high quality materials and excellent craftsmanship. "
                    f"Perfect for daily use and comes with a warranty.",
                    "short_description": f"High-quality {name} with premium features",
                    "price": Decimal(random.uniform(9.99, 299.99)).quantize(
                        Decimal("0.01")
                    ),
                    "stock": random.randint(0, 100),
                    "rating": Decimal(random.uniform(3.5, 5.0)).quantize(
                        Decimal("0.01")
                    ),
                    "status": random.choice(
                        ["draft", "published", "published", "published"]
                    ),  # More published
                    "priority": random.choice(["low", "medium", "high", "critical"]),
                    "is_featured": random.choice(
                        [True, False, False, False]
                    ),  # 25% featured
                    "is_available": random.choice(
                        [True, True, True, False]
                    ),  # 75% available
                    "release_date": timezone.now().date()
                    - timedelta(days=random.randint(0, 365)),
                    "tags": ", ".join(
                        random.sample(
                            ["new", "sale", "popular", "trending", "premium"],
                            k=random.randint(1, 3),
                        )
                    ),
                    "sku": f"SKU-{1000 + i}",
                    "barcode": f"978{random.randint(1000000000, 9999999999)}",
                },
            )
            products.append(product)

        return products

    def create_articles(self, categories):
        """Create article instances."""
        article_titles = [
            "Getting Started with Django",
            "10 Tips for Better Code",
            "Understanding CSS Grid",
            "Python Best Practices",
            "JavaScript ES6 Features",
            "Building Responsive Layouts",
            "Introduction to Machine Learning",
            "Web Accessibility Guide",
            "Database Optimization",
            "API Design Principles",
            "Modern Frontend Tools",
            "Testing Your Code",
            "Cloud Computing Basics",
            "Security Best Practices",
            "Performance Optimization",
            "Version Control with Git",
            "DevOps Fundamentals",
            "Microservices Architecture",
            "Container Technology",
            "Continuous Integration",
        ]

        authors = [
            "John Doe",
            "Jane Smith",
            "Alex Johnson",
            "Emily Davis",
            "Michael Brown",
            "Sarah Wilson",
        ]

        articles = []
        for _i, title in enumerate(article_titles):
            category = random.choice(
                categories[5:]
            )  # Use last 3 categories for articles
            article, _created = Article.objects.get_or_create(
                slug=slugify(title),
                defaults={
                    "title": title,
                    "author": random.choice(authors),
                    "category": category,
                    "excerpt": f"A comprehensive guide to {title.lower()}. "
                    f"Learn everything you need to know to get started.",
                    "content": f"# {title}\n\n"
                    f"This is the full content of the article about {title.lower()}. "
                    f"It contains detailed information, examples, and best practices.\n\n"
                    f"## Key Points\n\n"
                    f"- Point one about {title.lower()}\n"
                    f"- Important consideration\n"
                    f"- Best practices to follow\n\n"
                    f"## Conclusion\n\n"
                    f"Following these guidelines will help you master {title.lower()}.",
                    "status": random.choice(
                        ["draft", "review", "published", "published"]
                    ),
                    "views": random.randint(0, 10000),
                    "read_time": random.randint(3, 15),
                    "published_at": (
                        timezone.now() - timedelta(days=random.randint(1, 180))
                        if random.random() > 0.3
                        else None
                    ),
                    "tags": ", ".join(
                        random.sample(
                            ["tutorial", "guide", "tips", "advanced", "beginner"],
                            k=random.randint(1, 3),
                        )
                    ),
                },
            )
            articles.append(article)

        return articles

    def create_tasks(self, categories):
        """Create task instances."""
        task_titles = [
            "Fix navigation menu bug",
            "Update documentation",
            "Add user authentication",
            "Optimize database queries",
            "Design new landing page",
            "Implement search feature",
            "Write unit tests",
            "Deploy to production",
            "Review pull requests",
            "Update dependencies",
            "Refactor API endpoints",
            "Add error handling",
            "Improve accessibility",
            "Set up CI/CD pipeline",
            "Create user dashboard",
            "Fix mobile responsiveness",
            "Add email notifications",
            "Implement caching",
            "Security audit",
            "Performance testing",
            "Update UI components",
            "Add pagination",
            "Implement filters",
            "Create admin panel",
            "Fix form validation",
        ]

        assignees = [
            "Alice Cooper",
            "Bob Martin",
            "Carol White",
            "David Lee",
            "Eve Anderson",
            "Frank Thomas",
        ]

        tasks = []
        for _i, title in enumerate(task_titles):
            category = random.choice(categories) if random.random() > 0.5 else None
            task, _created = Task.objects.get_or_create(
                title=title,
                defaults={
                    "description": f"Detailed description for task: {title}. "
                    f"This needs to be completed according to specifications.",
                    "status": random.choice(["todo", "in_progress", "review", "done"]),
                    "priority": random.choice(["low", "medium", "high", "urgent"]),
                    "assignee": (
                        random.choice(assignees) if random.random() > 0.3 else ""
                    ),
                    "category": category,
                    "due_date": timezone.now().date()
                    + timedelta(days=random.randint(-7, 30)),
                    "completed_at": (
                        timezone.now() - timedelta(days=random.randint(1, 30))
                        if random.random() > 0.6
                        else None
                    ),
                    "estimated_hours": Decimal(random.uniform(1, 40)).quantize(
                        Decimal("0.25")
                    ),
                    "actual_hours": (
                        Decimal(random.uniform(1, 40)).quantize(Decimal("0.25"))
                        if random.random() > 0.5
                        else None
                    ),
                },
            )
            tasks.append(task)

        return tasks

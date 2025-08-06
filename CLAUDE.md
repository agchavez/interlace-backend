# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django REST API backend for a logistics tracker system. The application manages orders, inventory, tracking, maintenance data, and document handling with Celery for background tasks and WebSocket support for real-time notifications.

## Development Commands

### Running the Application
```bash
# Run development server
python manage.py runserver

# Run with Docker Compose (includes PostgreSQL, Redis, Celery)
docker-compose up

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Celery Commands
```bash
# Run Celery worker
celery -A config worker -l info

# Run Celery beat scheduler
celery -A config beat
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Load initial data (if available)
python manage.py load_data
```

### Management Commands
```bash
# Create users programmatically
python manage.py create_user

# Update users
python manage.py update_user

# Update tracker data
python manage.py update_tracker

# Create scheduled tasks
python manage.py create_task
```

## Architecture

### Django Apps Structure
- **apps/authentication/**: JWT-based authentication system
- **apps/user/**: User management with distributor center relationships and WebSocket notifications
- **apps/maintenance/**: Core maintenance data (drivers, products, trailers, operators, countries, periods)
- **apps/tracker/**: Main tracking functionality with T2 tracking support
- **apps/order/**: Order management with history tracking
- **apps/inventory/**: Inventory management with Celery tasks
- **apps/report/**: Reporting and dashboard functionality  
- **apps/document/**: Document and image handling with Azure Blob Storage
- **apps/imported/**: Import/export functionality for claims data

### Key Technologies
- **Django 4.2** with Django REST Framework
- **PostgreSQL** database
- **Redis** for Celery broker and WebSocket channel layer
- **Celery** with django-celery-beat for scheduled tasks
- **Django Channels** for WebSocket support
- **Azure Blob Storage** for media files
- **JWT Authentication** with SimpleJWT

### Database Models
- Custom user model extends AbstractUser (apps/user/models/user.py)
- BaseModel provides common fields (created_at, updated_at, etc.)
- Main entities: TrackerModel, OrderModel, InventoryModel, ProductModel
- Relationship hierarchy: Users → Distributor Centers → Orders/Trackers

### API Structure
- All apps use ViewSets with DRF routers
- URLs consolidated in config/urls.py with /api/ prefix
- JWT authentication required for most endpoints
- Custom exception handling in utils/error_handler.py

### Background Tasks
- Celery configured with Redis broker
- Database scheduler for periodic tasks
- Task definitions in individual app tasks.py files
- Management commands for creating scheduled tasks

### File Storage
- Azure Blob Storage configured for media files
- Local storage available for development
- Document processing utilities in apps/document/utils/

### Environment Configuration
- Uses python-decouple for environment variables
- Database, email, Redis, and Azure settings configurable via .env
- DEBUG mode toggleable via environment

## Testing and Quality

No specific test framework configuration was found in the codebase. Standard Django testing with `python manage.py test` should be used.

## Time Zone and Localization

- Time zone: America/Tegucigalpa
- Language: Spanish (Honduras) - es-HN
- USE_TZ = True for timezone-aware datetime handling
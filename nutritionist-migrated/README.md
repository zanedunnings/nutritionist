# Nutritionist App (Migrated)

This is the migrated version of the Nutritionist app, now using the web-app-template structure.

## Project Structure

```
nutritionist-migrated/
├── app.py              # Main FastAPI application
├── config.py           # Configuration settings
├── dependencies.py     # Common dependencies
├── requirements.txt    # Python dependencies
├── .env.example        # Example environment variables
├── data/              # Database files
├── models/            # SQLAlchemy models
│   ├── user.py        # User model
│   ├── waitlist.py    # Waitlist model
│   └── meal_plan.py   # Meal plan models
├── routes/            # API routes
│   ├── auth.py        # Authentication routes
│   ├── meal_plan.py   # Meal plan routes
│   └── main.py        # Main application routes
├── services/          # Business logic
│   └── meal_plan_service.py  # Meal plan service
├── static/            # Static files
└── templates/         # Jinja2 templates
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your environment variables:
   ```bash
   cp .env.example .env
   ```

4. Create the data directory:
   ```bash
   mkdir -p data
   ```

5. Run the application:
   ```bash
   uvicorn app:app --reload
   ```

## Migration Notes

- The app has been migrated to use SQLAlchemy ORM instead of raw SQLite
- Authentication is now handled through JWT tokens
- The database structure has been updated to use the template's schema
- All routes have been organized into separate modules
- Business logic has been moved to services
- Configuration is now handled through environment variables

## API Endpoints

- `/api/weekly` - Get the weekly meal plan
- `/api/today` - Get today's meal plan
- `/api/chat` - Chat with the meal plan assistant
- `/api/generate` - Generate a new meal plan
- `/auth/*` - Authentication endpoints
- `/app/*` - Main application routes

## Development

To start development:

1. Make sure you have all dependencies installed
2. Set up your environment variables
3. Run the development server:
   ```bash
   uvicorn app:app --reload
   ```

The server will automatically reload when you make changes to the code. 
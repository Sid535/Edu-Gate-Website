from website import create_app
from website.database import db
from website.models import Course

app = create_app()
app.app_context().push()

# Test database connection
courses = Course.query.all()
print(f"Found {len(courses)} courses:")
for course in courses:
    print(f"ID: {course.id}, Name: {course.name}")
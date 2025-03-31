import os
import json
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")
TOKEN_FILE = os.getenv("TOKEN_FILE")

SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.students.readonly"
]

def get_credentials():
    """Authenticate and return Google API credentials."""
    creds = None

    # Load token if available
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as token:
            creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)

    # If no valid credentials, initiate OAuth flow
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save credentials to JSON
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds

def list_classrooms(service):
    """Fetch and display available Google Classroom courses."""
    results = service.courses().list().execute()
    courses = results.get("courses", [])

    if not courses:
        print("No classrooms found.")
        return None

    print("\nAvailable Classrooms:")
    for i, course in enumerate(courses):
        print(f"{i + 1}. {course['name']} (ID: {course['id']})")

    return courses

def get_students(service, course_id):
    """Retrieve students from the specified classroom."""
    try:
        results = service.courses().students().list(courseId=course_id).execute()
        students = results.get("students", [])
        return students
    except Exception as e:
        print(f"Error fetching students for course {course_id}: {e}")
        return []

def get_assignments(service, course_id):
    """Retrieve assignments for a given classroom."""
    try:
        results = service.courses().courseWork().list(courseId=course_id).execute()
        assignments = results.get("courseWork", [])
        return assignments
    except Exception as e:
        print(f"Error fetching assignments for course {course_id}: {e}")
        return []

def main():
    creds = get_credentials()
    service = build("classroom", "v1", credentials=creds)

    classrooms = list_classrooms(service)
    if not classrooms:
        return

    # Let user choose a classroom
    choice = int(input("\nEnter the classroom number to access: ")) - 1
    if 0 <= choice < len(classrooms):
        selected_course = classrooms[choice]
        course_id = selected_course["id"]
        print(f"\nFetching data for classroom: {selected_course['name']}")

        students = get_students(service, course_id)
        assignments = get_assignments(service, course_id)

        if students:
            print("\nStudents in the classroom:")
            for student in students:
                print(f"- {student['profile']['name']['fullName']} ({student['profile']['emailAddress']})")

        if assignments:
            print("\nAssignments in the classroom:")
            for assignment in assignments:
                print(f"- {assignment['title']} (Due: {assignment.get('dueDate', 'N/A')})")

    else:
        print("Invalid selection.")

if __name__ == "__main__":
    main()

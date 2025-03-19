import os
import json
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")
TOKEN_FILE = os.getenv("TOKEN_FILE")

if not CREDENTIALS_FILE or not TOKEN_FILE:
    raise ValueError("Missing CREDENTIALS_FILE or TOKEN_FILE in .env file")

# Google Classroom API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.rosters.readonly"
]

def get_credentials():
    
    creds = None

    # Load token file if it exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials to token file
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def list_students_and_assignments():
    
    creds = get_credentials()
    service = build("classroom", "v1", credentials=creds)

    # Fetch all courses
    courses = service.courses().list().execute().get("courses", [])

    for course in courses:
        course_id = course["id"]
        course_name = course["name"]

        # Fetch students
        students_response = service.courses().students().list(courseId=course_id).execute()
        students = students_response.get("students", [])
        
        # Create a dictionary to store student names by their ID
        student_dict = {s["userId"]: s["profile"]["name"]["fullName"] for s in students}

        # Fetch assignments
        assignments_response = service.courses().courseWork().list(courseId=course_id).execute()
        assignments = assignments_response.get("courseWork", [])

        # Fetch all student submissions per course
        submissions_response = service.courses().courseWork().studentSubmissions().list(
            courseId=course_id, courseWorkId="-"
        ).execute()
        submissions = submissions_response.get("studentSubmissions", [])

        # Store student assignment stats in dictionary
        student_assignments = {student_dict[s["userId"]]: {"total": 0, "turned_in": 0} for s in students}

        # Process submissions and count assignments turned in
        for submission in submissions:
            student_id = submission["userId"]
            state = submission.get("state", "NEW")  # Default to NEW if state is missing

            if student_id in student_dict:
                student_assignments[student_dict[student_id]]["total"] += 1
                if state == "TURNED_IN":
                    student_assignments[student_dict[student_id]]["turned_in"] += 1

        # Prints the details of students and their assignments
        print(f"\nCourse: {course_name}")
        for student, stats in student_assignments.items():
            print(f"  {student}: {stats['turned_in']}/{stats['total']} assignments turned in")

if __name__ == "__main__":
    list_students_and_assignments()

import os
import csv
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Get file paths from .env
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE")
TOKEN_FILE = os.getenv("TOKEN_FILE")

# Updated Google Classroom API scopes
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.students.readonly",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
    "https://www.googleapis.com/auth/classroom.topics.readonly",
    "https://www.googleapis.com/auth/classroom.profile.emails"
]

def get_credentials():
    
    creds = None

    # Load existing credentials if available
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refresh or create new credentials if necessary
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future use
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds

def fetch_classrooms(service):
    
    try:
        results = service.courses().list().execute()
        courses = results.get("courses", [])
        
        if not courses:
            print("No classrooms found.")
            return []
        
        return [(course["id"], course["name"]) for course in courses]

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def get_students(service, classroom_id):
    
    try:
        students = service.courses().students().list(courseId=classroom_id).execute()
        student_list = students.get("students", [])

        if not student_list:
            print("No students found in this classroom.")
            return []

        return [(student["profile"]["name"]["fullName"], student["profile"].get("emailAddress", "N/A")) for student in student_list]

    except HttpError as error:
        print(f"An error occurred while fetching students: {error}")
        return []

def get_assignment_submissions(service, classroom_id):
    """Fetches the number of assignments turned in per student."""
    try:
        coursework = service.courses().courseWork().list(courseId=classroom_id).execute()
        assignments = coursework.get("courseWork", [])

        if not assignments:
            print("No assignments found for this classroom.")
            return {}

        turned_in_count = {}

        for assignment in assignments:
            submission_results = service.courses().courseWork().studentSubmissions().list(
                courseId=classroom_id, courseWorkId=assignment["id"]
            ).execute()
            submissions = submission_results.get("studentSubmissions", [])

            for submission in submissions:
                student_id = submission["userId"]
                if submission.get("state") == "TURNED_IN":
                    turned_in_count[student_id] = turned_in_count.get(student_id, 0) + 1

        return turned_in_count

    except HttpError as error:
        print(f"An error occurred while fetching assignments: {error}")
        return {}

def save_to_csv(data, filename):
    
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Student Name", "Email ID", "Assignments Turned In"])
        writer.writerows(data)

def main():
    
    creds = get_credentials()
    service = build("classroom", "v1", credentials=creds)

    # Fetch classrooms
    classrooms = fetch_classrooms(service)

    if not classrooms:
        print("No classrooms available.")
        return

    # Display available classrooms
    print("\nAvailable Classrooms:")
    for idx, (_, name) in enumerate(classrooms, 1):
        print(f"{idx}. {name}")

    # User selects a classroom
    choice = int(input("\nEnter the number of the classroom you want to check: ")) - 1
    if choice < 0 or choice >= len(classrooms):
        print("Invalid choice.")
        return

    classroom_id, classroom_name = classrooms[choice]
    
    # Fetch students
    students = get_students(service, classroom_id)
    if not students:
        return

    # Fetch assignment submissions
    submissions = get_assignment_submissions(service, classroom_id)

    # Match students with their turned-in count
    student_data = [(name, email, submissions.get(email, 0)) for name, email in students]

    # Display the data
    print("\nStudent Details:")
    for name, email, count in student_data:
        print(f"Name: {name}, Email: {email}, Assignments Turned In: {count}")

    # Save to CSV file
    save_choice = input("\nDo you want to save the data to a CSV file? (y/n): ").strip().lower()
    if save_choice == 'y':
        filename = f"{classroom_name}_students.csv"
        save_to_csv(student_data, filename)
        print(f"Data saved to {filename}")

if __name__ == "__main__":
    main()

"""
University Course Registration and Timetable Conflict System
Development Program: CourseRegistration.py
"""

from typing import Dict, List, Set


class Course:
    def __init__(self, code: str, title: str, credits: int, capacity: int, 
                 prerequisites: List[str], schedule: List[tuple]):
        """
        schedule: List of tuples -> [("Mon", 9, 11), ("Wed", 9, 11)]
        Time is represented in 24-hour format (e.g., 9 to 11).
        """
        self.code = code
        self.title = title
        self.credits = credits
        self.capacity = capacity
        self.prerequisites = prerequisites
        self.schedule = schedule
        self.enrolled_students: Set[str] = set()

    def is_full(self) -> bool:
        return len(self.enrolled_students) >= self.capacity


class Student:
    def __init__(self, student_id: str, program: str, semester: int, max_credits: int, completed_courses: List[str]):
        self.student_id = student_id
        self.program = program
        self.semester = semester
        self.max_credits = max_credits
        self.completed_courses = set(completed_courses)
        self.registered_courses: List[Course] = []

    def total_credits(self) -> int:
        return sum(course.credits for course in self.registered_courses)


class RegistrationSystem:
    def __init__(self):
        self.courses: Dict[str, Course] = {}

    def add_course(self, course: Course):
        self.courses[course.code] = course

    @staticmethod
    def _has_time_conflict(sched1: List[tuple], sched2: List[tuple]) -> bool:
        for day1, start1, end1 in sched1:
            for day2, start2, end2 in sched2:
                if day1 == day2:
                    # Check if time intervals overlap
                    if max(start1, start2) < min(end1, end2):
                        return True
        return False

    def register_courses(self, student: Student, course_codes: List[str]) -> Dict[str, str]:
        results = {}

        for code in course_codes:
            # 1. Existential Check
            if code not in self.courses:
                results[code] = "FAILED: Course does not exist."
                continue

            course = self.courses[code]

            # 2. Duplicate Registration Check
            if course in student.registered_courses:
                results[code] = "FAILED: Already registered for this course."
                continue

            # 3. Capacity Check
            if course.is_full():
                results[code] = "FAILED: Course capacity reached."
                continue

            # 4. Prerequisite Verification
            missing_prereqs = [p for p in course.prerequisites if p not in student.completed_courses]
            if missing_prereqs:
                results[code] = f"FAILED: Missing prerequisites ({', '.join(missing_prereqs)})."
                continue

            # 5. Maximum Credit Limit Check
            if student.total_credits() + course.credits > student.max_credits:
                results[code] = f"FAILED: Exceeds credit limit (Max: {student.max_credits})."
                continue

            # 6. Timetable Conflict Check
            conflict_found = False
            for reg_course in student.registered_courses:
                if self._has_time_conflict(course.schedule, reg_course.schedule):
                    results[code] = f"FAILED: Timetable clash with {reg_course.code}."
                    conflict_found = True
                    break
            if conflict_found:
                continue

            # Successful Registration
            student.registered_courses.append(course)
            course.enrolled_students.add(student.student_id)
            results[code] = "SUCCESS: Registration successful."

        return results


# ==========================================
# TEST IMPLEMENTATION
# ==========================================
if __name__ == "__main__":
    system = RegistrationSystem()

    # Add sample courses (Code, Title, Credits, Capacity, Prerequisites, Schedule)
    system.add_course(Course("PROG101", "Programming", 4, 30, [], [("Mon", 8, 10)]))
    system.add_course(Course("DS101", "Data Structures", 4, 30, ["PROG101"], [("Tue", 10, 12)]))
    system.add_course(Course("STAT101", "Statistics", 3, 30, [], [("Wed", 14, 16)]))
    system.add_course(Course("NET101", "Networking", 3, 30, [], [("Thu", 11, 13)]))

    # Target Courses from Example
    system.add_course(Course("DBMS", "Database Systems", 4, 2, ["PROG101"], [("Mon", 10, 12)]))
    system.add_course(Course("AI", "Artificial Intelligence", 4, 30, ["DS101"], [("Mon", 10, 12)])) # Clashes with DBMS
    system.add_course(Course("ML", "Machine Learning", 3, 30, ["STAT101"], [("Fri", 9, 11)]))
    system.add_course(Course("Cloud", "Cloud Computing", 3, 30, ["NET101"], [("Fri", 14, 16)]))

    # Initialize Student
    student_1 = Student(
        student_id="ST1001",
        program="Computer Science",
        semester=4,
        max_credits=10,
        completed_courses=["PROG101", "STAT101", "NET101"]  # Missing DS101
    )

    # List of desired courses to register
    desired_courses = ["DBMS", "AI", "ML", "Cloud", "DBMS"]

    # Process Registration
    registration_log = system.register_courses(student_1, desired_courses)

    # Output Results
    print(f"--- Student Registration Log ({student_1.student_id}) ---")
    for course_code, status in registration_log.items():
        print(f"Course {course_code}: {status}")

    print("\n--- Summary ---")
    print(f"Registered Courses: {[c.code for c in student_1.registered_courses]}")
    print(f"Total Registered Credits: {student_1.total_credits()} / {student_1.max_credits}")

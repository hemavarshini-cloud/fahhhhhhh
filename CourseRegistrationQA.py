"""
Course Registration System - Unit & Integration Test Suite
Executes test cases covering all edge cases, edge conditions, and constraint checks.
"""

from CourseRegistration import Course, Student, RegistrationSystem


def run_comprehensive_tests():
    # Setup baseline registration system
    system = RegistrationSystem()

    # Base Prerequisites & Reference Courses
    system.add_course(Course("PROG101", "Programming", 4, 30, [], [("Mon", 8, 10)]))
    system.add_course(Course("DS101", "Data Structures", 4, 30, ["PROG101"], [("Tue", 10, 12)]))
    system.add_course(Course("STAT101", "Statistics", 3, 30, [], [("Wed", 14, 16)]))
    system.add_course(Course("NET101", "Networking", 3, 30, [], [("Thu", 11, 13)]))

    # Core Test Courses
    system.add_course(Course("DBMS", "Database Systems", 4, 30, ["PROG101"], [("Mon", 10, 12)]))
    system.add_course(Course("AI", "Artificial Intelligence", 4, 30, ["DS101"], [("Mon", 10, 12)]))  # Clashes with DBMS
    system.add_course(Course("ML", "Machine Learning", 3, 30, ["STAT101"], [("Fri", 9, 11)]))
    system.add_course(Course("Cloud", "Cloud Computing", 3, 30, ["NET101"], [("Fri", 14, 16)]))
    system.add_course(Course("FULL101", "Full Capacity Seminar", 3, 1, [], [("Sat", 10, 12)]))  # Cap: 1

    print("==================================================")
    print("      COURSE REGISTRATION SYSTEM TEST SUITE       ")
    print("==================================================\n")

    # 1. Valid Registration
    s1 = Student("S001", "CS", 3, max_credits=15, completed_courses=["PROG101", "STAT101"])
    res1 = system.register_courses(s1, ["DBMS", "ML"])
    print("[TEST 1] Valid Registration")
    print(f"DBMS: {res1['DBMS']} | ML: {res1['ML']}")
    print(f"Total Credits: {s1.total_credits()}\n")

    # 2. Missing Prerequisite
    s2 = Student("S002", "CS", 3, max_credits=15, completed_courses=["PROG101"])  # Lacks DS101
    res2 = system.register_courses(s2, ["AI"])
    print("[TEST 2] Missing Prerequisite")
    print(f"AI: {res2['AI']}\n")

    # 3. Credit-Limit Violation
    s3 = Student("S003", "CS", 3, max_credits=6, completed_courses=["PROG101", "STAT101"])
    res3 = system.register_courses(s3, ["DBMS", "ML"])  # 4 + 3 = 7 credits (> 6)
    print("[TEST 3] Credit-Limit Violation")
    print(f"DBMS: {res3['DBMS']} | ML: {res3['ML']}")
    print(f"Total Credits: {s3.total_credits()}\n")

    # 4. Timetable Conflict
    s4 = Student("S004", "CS", 3, max_credits=15, completed_courses=["PROG101", "DS101"])
    res4 = system.register_courses(s4, ["DBMS", "AI"])  # Mon 10-12 overlap
    print("[TEST 4] Timetable Conflict")
    print(f"DBMS: {res4['DBMS']} | AI: {res4['AI']}\n")

    # 5. Full Course Capacity
    s_other = Student("S000", "CS", 1, max_credits=10, completed_courses=[])
    system.register_courses(s_other, ["FULL101"])  # Fills up capacity (1/1)
    
    s5 = Student("S005", "CS", 2, max_credits=15, completed_courses=[])
    res5 = system.register_courses(s5, ["FULL101"])
    print("[TEST 5] Full Course Capacity")
    print(f"FULL101: {res5['FULL101']}\n")

    # 6. Duplicate Registration
    s6 = Student("S006", "CS", 3, max_credits=15, completed_courses=["PROG101"])
    res6 = system.register_courses(s6, ["DBMS", "DBMS"])
    print("[TEST 6] Duplicate Registration")
    print(f"DBMS Attempt 1 & 2: {res6['DBMS']}\n")

    # 7. Invalid Course
    s7 = Student("S007", "CS", 1, max_credits=15, completed_courses=[])
    res7 = system.register_courses(s7, ["UNKNOWN999"])
    print("[TEST 7] Invalid Course")
    print(f"UNKNOWN999: {res7['UNKNOWN999']}\n")

    # 8. Boundary Credit Values (Exact max limit match vs. +1 over limit)
    s8 = Student("S008", "CS", 3, max_credits=7, completed_courses=["PROG101", "STAT101"])
    res8 = system.register_courses(s8, ["DBMS", "ML"])  # 4 + 3 = 7 (Exactly Max)
    print("[TEST 8] Boundary Credit Values")
    print(f"DBMS (4 cr): {res8['DBMS']}")
    print(f"ML (3 cr - Boundary hit exact 7/7): {res8['ML']}")
    print(f"Total Credits: {s8.total_credits()} / {s8.max_credits}\n")


if __name__ == "__main__":
    run_comprehensive_tests()

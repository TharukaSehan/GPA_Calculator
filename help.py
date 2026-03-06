#!/usr/bin/env python3
"""Simple GPA calculator CLI.

Prompts user to select a semester and enter course information
(subject, credits, and grade), then computes the GPA for that semester.
"""

from typing import Dict

# grade to point mapping
GRADE_POINTS: Dict[str, float] = {
    "A+": 4.0,
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "F": 0.0,
}


def prompt_course() -> tuple[str, int, str]:
    """Ask the user for a single course entry.

    Returns a tuple of (subject, credits, grade).
    """
    subject = input("Enter subject name (or press Enter to finish): ").strip()
    if not subject:
        return "", 0, ""

    while True:
        credits_str = input("  Credits: ").strip()
        if credits_str.isdigit():
            credits = int(credits_str)
            break
        print("    Please enter a valid integer for credits.")

    while True:
        grade = input("  Grade (A+, A, A-, ... F): ").upper().strip()
        if grade in GRADE_POINTS:
            break
        print("    Invalid grade; try again.")

    return subject, credits, grade


def calculate_gpa(courses: list[tuple[str, int, str]]) -> float:
    """Compute GPA from a list of courses.

    Each course is (subject, credits, grade).
    """
    total_points = 0.0
    total_credits = 0
    for _, credits, grade in courses:
        points = GRADE_POINTS.get(grade, 0.0)
        total_points += points * credits
        total_credits += credits
    return total_points / total_credits if total_credits > 0 else 0.0


def main() -> None:
    print("Welcome to the simple GPA calculator!")
    semester = input("Select semester (e.g. Fall 2025): ").strip()
    print(f"-- Entering courses for {semester} --")

    courses: list[tuple[str, int, str]] = []
    while True:
        subj, creds, grd = prompt_course()
        if not subj:
            break
        courses.append((subj, creds, grd))

    if not courses:
        print("No courses entered. Goodbye.")
        return

    gpa = calculate_gpa(courses)
    print(f"GPA for {semester}: {gpa:.2f}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""SUSL Faculty of Computing GPA web app with accounts.

Features:
- Student registration and login
- First-login degree selection (CIS/SE/DS)
- Handbook-based semester auto-fill for subject codes (CIS/SE)
- Persistent per-user progress saved on the server
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import uuid
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


GRADE_POINTS = {
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
    "E": 0.0,
}


PROGRAMS = {
    "CIS": {
        "name": "Computing and Information Systems",
        "from_handbook": True,
        "fgpa_weights": [0.2, 0.2, 0.3, 0.3],
        "semesters": {
            1: [
                {"code": "IS1101", "title": "Fundamentals of Information Systems", "credits": 2},
                {"code": "IS1102", "title": "Structured Programming Techniques", "credits": 2},
                {"code": "IS1103", "title": "Structured Programming Practicum", "credits": 1},
                {"code": "IS1104", "title": "Theories of Information Systems", "credits": 2},
                {"code": "IS1105", "title": "Computer System Organization", "credits": 2},
                {"code": "IS1106", "title": "Foundations of Web Technologies", "credits": 2},
                {"code": "IS1107", "title": "Personal Productivity with Information Technology", "credits": 1},
                {"code": "IS1108", "title": "Fundamentals of Mathematics", "credits": 2},
                {"code": "IS1109", "title": "Statistics and Probability Theory", "credits": 2},
                {"code": "IS1110", "title": "Communication Skills I", "credits": 2, "non_gpa": True},
                {"code": "IS1111", "title": "Academic Integrity", "credits": 1, "non_gpa": True},
                {"code": "IS-EGP-1101", "title": "General English I", "credits": 2, "non_gpa": True},
            ],
            2: [
                {"code": "IS2101", "title": "Object Oriented Programming", "credits": 2},
                {"code": "IS2102", "title": "Object Oriented Programming Practicum", "credits": 1},
                {"code": "IS2103", "title": "Emerging IS Technologies", "credits": 1},
                {"code": "IS2104", "title": "Database Systems", "credits": 2},
                {"code": "IS2105", "title": "Database Management Systems Practicum", "credits": 1},
                {"code": "IS2106", "title": "System Analysis and Design", "credits": 1},
                {"code": "IS2107", "title": "Social and Professional Issues", "credits": 1},
                {"code": "IS2108", "title": "Human Computer Interaction", "credits": 2},
                {"code": "IS2109", "title": "Information Assurance and Security", "credits": 2},
                {"code": "IS2110", "title": "Software Project Initiation and Planning", "credits": 1},
                {"code": "IS2111", "title": "Advanced Mathematics", "credits": 2},
                {"code": "IS2112", "title": "Communication Skills II", "credits": 2, "non_gpa": True},
                {"code": "IS-EGP-1201", "title": "General English II", "credits": 2, "non_gpa": True},
            ],
            3: [
                {"code": "IS3101", "title": "Object Oriented Analysis and Design", "credits": 2},
                {"code": "IS3102", "title": "Data Structures and Algorithms", "credits": 2},
                {"code": "IS3103", "title": "IT Governance", "credits": 2},
                {"code": "IS3104", "title": "Software Engineering", "credits": 2},
                {"code": "IS3105", "title": "IS Risk Management", "credits": 2},
                {"code": "IS3106", "title": "IS Sustainability", "credits": 1},
                {"code": "IS3107", "title": "Management Information Systems", "credits": 2},
                {"code": "IS3108", "title": "E-Business", "credits": 1},
                {"code": "IS3109", "title": "Digital Innovation", "credits": 2},
                {"code": "IS-EAP-2101", "title": "Academic English I", "credits": 2, "non_gpa": True},
            ],
            4: [
                {"code": "IS4101", "title": "IT Auditing", "credits": 2},
                {"code": "IS4102", "title": "Web Application Development", "credits": 2},
                {"code": "IS4103", "title": "Operating Systems", "credits": 2},
                {"code": "IS4104", "title": "System Administration and Maintenance", "credits": 2},
                {"code": "IS4105", "title": "IT Procurement Management", "credits": 1},
                {"code": "IS4106", "title": "Software Architecture", "credits": 2},
                {"code": "IS4107", "title": "Professionalism and Ethics in Computing", "credits": 1},
                {"code": "IS4108", "title": "IS Strategies", "credits": 1},
                {"code": "IS4109", "title": "Agile Software Development", "credits": 2},
                {"code": "IS4110", "title": "Capstone Project", "credits": 2},
                {"code": "IS-EAP-2201", "title": "Academic English II", "credits": 2, "non_gpa": True},
            ],
            5: [
                {"code": "IS5101", "title": "Entrepreneurship and Innovation", "credits": 1},
                {"code": "IS5102", "title": "Enterprise Architecture", "credits": 1},
                {"code": "IS5103", "title": "High Performance Computing", "credits": 2},
                {"code": "IS5104", "title": "Software Process Management", "credits": 1},
                {"code": "IS5105", "title": "Business Process Management", "credits": 2},
                {"code": "IS5106", "title": "UI/UX Practicum", "credits": 1},
                {"code": "IS5107", "title": "Project Management Practicum", "credits": 1},
                {"code": "IS5108", "title": "Business Intelligence", "credits": 2},
                {"code": "IS5109", "title": "IS Project for Community", "credits": 1},
                {"code": "IS5110", "title": "Advanced Database Systems", "credits": 2},
                {"code": "IS5111", "title": "Data Communication and Networks", "credits": 2},
                {"code": "IS5112", "title": "Design Patterns and Anti-patterns", "credits": 2},
                {"code": "IS5113", "title": "Software Quality Assurance", "credits": 2},
                {"code": "IS5114", "title": "Data Mining and Analytics", "credits": 2},
                {"code": "IS-EBP-3101", "title": "Business English", "credits": 2, "non_gpa": True},
            ],
            6: [
                {"code": "IS6101", "title": "Industrial Training", "credits": 6},
            ],
            7: [
                {"code": "IS7101", "title": "Research Methodologies", "credits": 2},
                {"code": "IS7102", "title": "Information System Law", "credits": 2},
                {"code": "IS7103", "title": "Business Process Simulation", "credits": 2},
                {"code": "IS7104", "title": "Enterprise Modelling Ontologies", "credits": 2},
                {"code": "IS7105", "title": "Organizational Behavior and Management", "credits": 2},
                {"code": "IS7106", "title": "Cloud Computing", "credits": 2},
                {"code": "IS7107", "title": "Mobile Application Development", "credits": 2},
                {"code": "IS7108", "title": "Web Service Technologies", "credits": 2},
                {"code": "IS7109", "title": "Geographical Information Systems", "credits": 2},
                {"code": "IS7110", "title": "Statistical Distribution and Inferences", "credits": 2},
                {"code": "IS7111", "title": "Advanced Programming Practicum", "credits": 2},
                {"code": "IS7112", "title": "Machine Learning", "credits": 2},
            ],
            8: [
                {"code": "IS8101", "title": "Research Project in IS", "credits": 8},
                {"code": "IS8102", "title": "Business/IT Alignment", "credits": 2},
                {"code": "IS8103", "title": "Human Resource Management", "credits": 2},
                {"code": "IS8104", "title": "Scientific Communication", "credits": 2},
                {"code": "IS8105", "title": "IS Economics", "credits": 2},
                {"code": "IS8106", "title": "Computer System Security", "credits": 2},
                {"code": "IS8107", "title": "Supply Chain Management", "credits": 2},
                {"code": "IS8108", "title": "Advanced Computer Networks", "credits": 2},
            ],
        },
    },
    "SE": {
        "name": "Software Engineering",
        "from_handbook": True,
        "fgpa_weights": [0.2, 0.2, 0.3, 0.3],
        "semesters": {
            1: [
                {"code": "SE1101", "title": "Computer Organization", "credits": 2},
                {"code": "SE1102", "title": "Programming Fundamentals", "credits": 2},
                {"code": "SE1103", "title": "Requirements Fundamentals", "credits": 2},
                {"code": "SE1104", "title": "Software Process Concepts", "credits": 2},
                {"code": "SE1105", "title": "Social and Professional Issues", "credits": 2},
                {"code": "SE1106", "title": "Fundamentals of Mathematics", "credits": 2},
                {"code": "SE1107", "title": "Fundamentals of Statistics", "credits": 2},
                {"code": "SE1108", "title": "Communication Skills I", "credits": 2, "non_gpa": True},
                {"code": "SE1109", "title": "Academic Integrity", "credits": 1, "non_gpa": True},
                {"code": "SE-EGP-1101", "title": "General English I", "credits": 2, "non_gpa": True},
            ],
            2: [
                {"code": "SE2101", "title": "Algorithms, Data Structures, and Complexity", "credits": 2},
                {"code": "SE2102", "title": "Database Management Systems", "credits": 2},
                {"code": "SE2103", "title": "Operating Systems Basics", "credits": 2},
                {"code": "SE2104", "title": "Object Oriented Programming", "credits": 2},
                {"code": "SE2105", "title": "Requirement Specification and Documentation", "credits": 2},
                {"code": "SE2106", "title": "Software Process Implementation", "credits": 2},
                {"code": "SE2107", "title": "Analysis Fundamentals", "credits": 2},
                {"code": "SE2108", "title": "Advanced Mathematics", "credits": 2},
                {"code": "SE2109", "title": "Communication Skills II", "credits": 2, "non_gpa": True},
                {"code": "SE-EGP-1201", "title": "General English II", "credits": 2, "non_gpa": True},
            ],
            3: [
                {"code": "SE3101", "title": "Network Protocols", "credits": 2},
                {"code": "SE3102", "title": "Formal Methods", "credits": 2},
                {"code": "SE3103", "title": "Object Oriented Analysis and Design", "credits": 2},
                {"code": "SE3104", "title": "Requirements Validation", "credits": 2},
                {"code": "SE3105", "title": "Software Design Concepts", "credits": 2},
                {"code": "SE3106", "title": "Web Systems and Technologies", "credits": 2},
                {"code": "SE3107", "title": "Software Engineering Foundations", "credits": 2},
                {"code": "SE-EAP-2101", "title": "Academic English I", "credits": 2, "non_gpa": True},
            ],
            4: [
                {"code": "SE4101", "title": "Security Fundamentals", "credits": 2},
                {"code": "SE4102", "title": "Software Verification and Validation", "credits": 2},
                {"code": "SE4103", "title": "Software Configuration Management", "credits": 2},
                {"code": "SE4104", "title": "Software Project Management", "credits": 2},
                {"code": "SE4105", "title": "Human Computer Interaction Design", "credits": 2},
                {"code": "SE4106", "title": "Projects in Web Systems and Technologies", "credits": 3},
                {"code": "SE4107", "title": "Industrial Inspection", "credits": 1},
                {"code": "SE4108", "title": "Risk Management", "credits": 2},
                {"code": "SE4109", "title": "Communication Skills", "credits": 2, "non_gpa": True},
                {"code": "SE4110", "title": "Management Information Systems", "credits": 2},
                {"code": "SE-EAP-2201", "title": "Academic English II", "credits": 2, "non_gpa": True},
            ],
            5: [
                {"code": "SE5101", "title": "Computer and Network Security", "credits": 2},
                {"code": "SE5102", "title": "Software Testing", "credits": 2},
                {"code": "SE5103", "title": "Product Assurance", "credits": 2},
                {"code": "SE5104", "title": "Mini Project", "credits": 3},
                {"code": "SE5105", "title": "Evolution Processes and Activities", "credits": 1},
                {"code": "SE-EBP-3101", "title": "Business English", "credits": 2, "non_gpa": True},
                {"code": "SE5106", "title": "IT Auditing", "credits": 2, "elective": True},
                {"code": "SE5107", "title": "Human Resource Management", "credits": 2, "elective": True},
                {"code": "SE5108", "title": "Geographic Information Systems", "credits": 2, "elective": True},
                {"code": "SE5109", "title": "Logistic System and Transportation Management", "credits": 2, "elective": True},
                {"code": "SE5110", "title": "Business Intelligence", "credits": 2, "elective": True},
            ],
            6: [
                {"code": "SE6101", "title": "Community Project", "credits": 3},
                {"code": "SE6102", "title": "Cloud Computing", "credits": 2},
                {"code": "SE6103", "title": "Parallel and Distributed Systems", "credits": 2},
                {"code": "SE6104", "title": "Advanced Database Management Systems", "credits": 2},
                {"code": "SE6105", "title": "Software Architecture", "credits": 2},
                {"code": "SE6106", "title": "Software Design Patterns", "credits": 2},
                {"code": "SE6107", "title": "Software Design Evaluation", "credits": 2},
                {"code": "SE6108", "title": "Current Topics in Software Engineering", "credits": 1},
                {"code": "SE6109", "title": "Enterprise Modeling Ontologies", "credits": 2, "elective": True},
                {"code": "SE6110", "title": "Software Engineering Economics", "credits": 2, "elective": True},
                {"code": "SE6111", "title": "Social Computing", "credits": 2, "elective": True},
                {"code": "SE6112", "title": "Semantic Web", "credits": 2, "elective": True},
                {"code": "SE6113", "title": "Robotics", "credits": 2, "elective": True},
            ],
            7: [
                {"code": "SE7101", "title": "Industrial Training", "credits": 6},
            ],
            8: [
                {"code": "SE8101", "title": "Research Project", "credits": 8},
                {"code": "SE8102", "title": "Research Methods", "credits": 2},
                {"code": "SE8103", "title": "Service Oriented Architecture", "credits": 2},
                {"code": "SE8104", "title": "Problem Analysis and Reporting", "credits": 2},
                {"code": "SE8105", "title": "Machine Learning", "credits": 2},
                {"code": "SE8106", "title": "Mobile Computing", "credits": 2},
                {"code": "SE8107", "title": "Refactoring", "credits": 2},
                {"code": "SE8108", "title": "Game Designing and Development", "credits": 2, "elective": True},
                {"code": "SE8109", "title": "Data Mining", "credits": 2, "elective": True},
                {"code": "SE8110", "title": "Big Data Analytics", "credits": 2, "elective": True},
                {"code": "SE8111", "title": "Artificial Intelligence", "credits": 2, "elective": True},
            ],
        },
    },
    "DS": {
        "name": "Data Science",
        "from_handbook": False,
        "fgpa_weights": [0.2, 0.2, 0.3, 0.3],
        "semesters": {1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: []},
    },
}


USERS_PATH = Path(__file__).with_name("student_accounts.json")
ADMIN_PATH = Path(__file__).with_name("admin_accounts.json")
USERS_LOCK = threading.Lock()
SESSIONS: dict[str, str] = {}  # token -> username (student)
ADMIN_SESSIONS: dict[str, str] = {}  # token -> admin_username


def load_users() -> dict[str, Any]:
    if not USERS_PATH.exists():
        return {}
    try:
        return json.loads(USERS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_users(users: dict[str, Any]) -> None:
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return digest.hex()


def create_user_record(password: str) -> dict[str, Any]:
    salt_hex = secrets.token_hex(16)
    return {
        "salt": salt_hex,
        "password_hash": hash_password(password, salt_hex),
        "program": None,
        "state": None,
    }


def verify_password(password: str, user: dict[str, Any]) -> bool:
    expected = user.get("password_hash", "")
    actual = hash_password(password, user.get("salt", ""))
    return hmac.compare_digest(expected, actual)


def load_admins() -> dict[str, Any]:
    if not ADMIN_PATH.exists():
        # Initialize with default admin if file doesn't exist
        default = {
            "admin": create_user_record("admin123")
        }
        ADMIN_PATH.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    try:
        return json.loads(ADMIN_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_admins(admins: dict[str, Any]) -> None:
    ADMIN_PATH.write_text(json.dumps(admins, indent=2), encoding="utf-8")


def new_token(username: str) -> str:
    token = uuid.uuid4().hex
    SESSIONS[token] = username
    return token


def new_admin_token(admin_username: str) -> str:
    token = uuid.uuid4().hex
    ADMIN_SESSIONS[token] = admin_username
    return token


def default_semester_rows(program_key: str, semester_number: int) -> list[dict[str, Any]]:
    courses = PROGRAMS[program_key]["semesters"].get(semester_number, [])
    if not courses:
        return [
            {"id": uuid.uuid4().hex, "course": "", "grade": "--", "credits": 3, "nonGpa": False}
            for _ in range(3)
        ]
    rows = []
    for course in courses:
        rows.append(
            {
                "id": uuid.uuid4().hex,
                "course": f"{course['code']} - {course['title']}",
                "grade": "--",
                "credits": int(course.get("credits", 0)),
                "nonGpa": bool(course.get("non_gpa", False)),
            }
        )
    return rows


def build_default_state(program_key: str) -> dict[str, Any]:
    return {
        "program": program_key,
        "weights": PROGRAMS[program_key].get("fgpa_weights", [0.2, 0.2, 0.3, 0.3]),
        "semesters": [
            {
                "id": uuid.uuid4().hex,
                "number": 1,
                "collapsed": False,
                "rows": default_semester_rows(program_key, 1),
            }
        ],
    }


def read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any] | None:
    try:
        length = int(handler.headers.get("Content-Length", "0"))
    except ValueError:
        return None
    if length <= 0:
        return None
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


class GPAHandler(BaseHTTPRequestHandler):
    def _auth_admin_username(self) -> str | None:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth.removeprefix("Bearer ").strip()
        return ADMIN_SESSIONS.get(token)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self) -> None:
        html = build_html().encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(html)

    def _auth_username(self) -> str | None:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth.removeprefix("Bearer ").strip()
        return SESSIONS.get(token)

    def do_GET(self) -> None:  # noqa: N802
      if self.path in {"/", "/index.html"}:
        self._send_html()
        return

      if self.path == "/admin":
        html = build_admin_html().encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(html)
        return

      if self.path == "/admin/login.html":
        html = build_admin_login_html().encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(html)
        return

      if self.path == "/api/me":
        username = self._auth_username()
        if not username:
          self._send_json(401, {"ok": False, "message": "Unauthorized"})
          return
        with USERS_LOCK:
          users = load_users()
          user = users.get(username)
        if not user:
          self._send_json(404, {"ok": False, "message": "User not found"})
          return
        self._send_json(
          200,
          {
            "ok": True,
            "username": username,
            "program": user.get("program"),
            "state": user.get("state"),
            "full_name": user.get("full_name", ""),
            "student_id": user.get("student_id", ""),
          },
        )
        return

      if self.path == "/api/admin/stats":
        admin = self._auth_admin_username()
        if not admin:
          self._send_json(401, {"ok": False, "message": "Unauthorized"})
          return
        with USERS_LOCK:
          users = load_users()
        total = len(users)
        with_program = sum(1 for u in users.values() if u.get("program"))
        self._send_json(200, {"ok": True, "total_students": total, "with_program": with_program})
        return

      if self.path == "/api/admin/students":
        admin = self._auth_admin_username()
        if not admin:
          self._send_json(401, {"ok": False, "message": "Unauthorized"})
          return
        with USERS_LOCK:
          users = load_users()
        students = []
        for username, user in users.items():
          students.append({
            "username": username,
            "program": user.get("program") or "Not Selected",
            "full_name": user.get("full_name", "-"),
            "student_id": user.get("student_id", "-"),
            "has_progress": bool(user.get("state")),
          })
        self._send_json(200, {"ok": True, "students": sorted(students, key=lambda x: x["username"])})
        return

      if self.path == "/api/admin/logout":
        auth = self.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
        if token and token in ADMIN_SESSIONS:
          del ADMIN_SESSIONS[token]
        self._send_json(200, {"ok": True})
        return

      self.send_error(404, "Not found")

    def do_POST(self) -> None:  # noqa: N802
      if self.path == "/api/admin-login":
        body = read_json_body(self) or {}
        username = str(body.get("username", "")).strip().lower()
        password = str(body.get("password", ""))
        with USERS_LOCK:
          admins = load_admins()
          admin = admins.get(username)
        if not admin or not verify_password(password, admin):
          self._send_json(401, {"ok": False, "message": "Invalid admin credentials."})
          return
        token = new_admin_token(username)
        self._send_json(200, {"ok": True, "token": token, "admin_username": username})
        return

      if self.path == "/api/register":
        body = read_json_body(self) or {}
        username = str(body.get("username", "")).strip().lower()
        password = str(body.get("password", ""))
        if len(username) < 3 or len(password) < 6:
          self._send_json(400, {"ok": False, "message": "Username must be at least 3 chars and password at least 6 chars."})
          return
        with USERS_LOCK:
          users = load_users()
          if username in users:
            self._send_json(409, {"ok": False, "message": "Account already exists."})
            return
          users[username] = create_user_record(password)
          users[username]["full_name"] = str(body.get("full_name", "")).strip()
          users[username]["student_id"] = str(body.get("student_id", "")).strip()
          save_users(users)
        token = new_token(username)
        self._send_json(200, {"ok": True, "token": token, "username": username, "program": None, "state": None, "full_name": users[username].get("full_name", ""), "student_id": users[username].get("student_id", "")})
        return

      if self.path == "/api/login":
        body = read_json_body(self) or {}
        username = str(body.get("username", "")).strip().lower()
        password = str(body.get("password", ""))
        with USERS_LOCK:
          users = load_users()
          user = users.get(username)
        if not user or not verify_password(password, user):
          self._send_json(401, {"ok": False, "message": "Invalid username or password."})
          return
        token = new_token(username)
        self._send_json(200, {"ok": True, "token": token, "username": username, "program": user.get("program"), "state": user.get("state"), "full_name": user.get("full_name", ""), "student_id": user.get("student_id", "")})
        return

      if self.path == "/api/set-program":
        username = self._auth_username()
        if not username:
          self._send_json(401, {"ok": False, "message": "Unauthorized"})
          return
        body = read_json_body(self) or {}
        program = str(body.get("program", "")).strip().upper()
        if program not in PROGRAMS:
          self._send_json(400, {"ok": False, "message": "Unknown program."})
          return
        with USERS_LOCK:
          users = load_users()
          user = users.get(username)
          if not user:
            self._send_json(404, {"ok": False, "message": "User not found"})
            return
          user["program"] = program
          if user.get("state") is None:
            user["state"] = build_default_state(program)
          else:
            user["state"]["program"] = program
          users[username] = user
          save_users(users)
        self._send_json(200, {"ok": True, "program": program, "state": users[username]["state"]})
        return

      if self.path == "/api/save-progress":
        username = self._auth_username()
        if not username:
          self._send_json(401, {"ok": False, "message": "Unauthorized"})
          return
        body = read_json_body(self) or {}
        state = body.get("state")
        if not isinstance(state, dict):
          self._send_json(400, {"ok": False, "message": "Invalid state payload."})
          return
        with USERS_LOCK:
          users = load_users()
          user = users.get(username)
          if not user:
            self._send_json(404, {"ok": False, "message": "User not found"})
            return
          user["state"] = state
          if isinstance(state.get("program"), str):
            user["program"] = state["program"]
          users[username] = user
          save_users(users)
        self._send_json(200, {"ok": True})
        return

      if self.path == "/api/logout":
        auth = self.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
        if token and token in SESSIONS:
          del SESSIONS[token]
        self._send_json(200, {"ok": True})
        return

      admin_username = self._auth_admin_username()
      if not admin_username:
        self._send_json(401, {"ok": False, "message": "Unauthorized"})
        return

      if self.path == "/api/admin/change-password":
        body = read_json_body(self) or {}
        current_password = str(body.get("current_password", ""))
        new_password = str(body.get("new_password", ""))
        if len(new_password) < 6:
          self._send_json(400, {"ok": False, "message": "New password must be at least 6 characters."})
          return
        with USERS_LOCK:
          admins = load_admins()
          admin = admins.get(admin_username)
          if not admin or not verify_password(current_password, admin):
            self._send_json(401, {"ok": False, "message": "Current password is incorrect."})
            return
          admins[admin_username] = create_user_record(new_password)
          save_admins(admins)
        self._send_json(200, {"ok": True})
        return

      if self.path == "/api/admin/rename-student":
        body = read_json_body(self) or {}
        old_username = str(body.get("old_username", "")).strip().lower()
        new_username = str(body.get("new_username", "")).strip().lower()
        if len(old_username) < 3 or len(new_username) < 3:
          self._send_json(400, {"ok": False, "message": "Both usernames must be at least 3 characters."})
          return
        if old_username == new_username:
          self._send_json(400, {"ok": False, "message": "New username must be different."})
          return
        with USERS_LOCK:
          users = load_users()
          if old_username not in users:
            self._send_json(404, {"ok": False, "message": "Student not found."})
            return
          if new_username in users:
            self._send_json(409, {"ok": False, "message": "Username already exists."})
            return
          users[new_username] = users.pop(old_username)
          save_users(users)
          for token, session_username in list(SESSIONS.items()):
            if session_username == old_username:
              SESSIONS[token] = new_username
        self._send_json(200, {"ok": True, "username": new_username})
        return

      if self.path == "/api/admin/logout":
        auth = self.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
        if token and token in ADMIN_SESSIONS:
          del ADMIN_SESSIONS[token]
        self._send_json(200, {"ok": True})
        return

      self.send_error(404, "Not found")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SUSL GPA Calculator</title>
  <style>
    :root { --bg:#f3f6fb; --panel:#fff; --ink:#17233b; --muted:#66768f; --line:#d8dfeb; --accent:#1e59e6; }
    *{box-sizing:border-box} body{margin:0;font-family:'Trebuchet MS','Segoe UI',sans-serif;background:linear-gradient(180deg,#f8fbff,#edf2fb);color:var(--ink)}
    .top{height:12px;background:#302840}
    .wrap{max-width:1480px;margin:0 auto;padding:18px}
    .title{display:flex;justify-content:space-between;align-items:end;gap:12px;margin-bottom:12px}
    .title h1{margin:0;font-size:2.3rem;letter-spacing:-.04em}
    .title .user{display:flex;gap:8px;align-items:center}
    .chip{border:1px solid var(--line);padding:8px 12px;border-radius:999px;background:#fff;color:#35507f;font-weight:700}
    .btn{border:0;border-radius:12px;padding:10px 14px;font:inherit;font-weight:800;cursor:pointer}
    .btn.primary{background:linear-gradient(135deg,#2f64ec,#1749d3);color:#fff}
    .btn.ghost{background:#fff;border:1px solid var(--line);color:#27406b}
    .layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px}
    .panel{background:var(--panel);border:1px solid var(--line);border-radius:20px;box-shadow:0 14px 28px rgba(18,40,86,.08)}
    .semester{overflow:hidden}
    .semester .head{display:flex;justify-content:space-between;align-items:center;background:#eef4ff;padding:16px 18px;border-bottom:1px solid var(--line)}
    .semester .head strong{font-size:1.3rem}
    .semester .body{padding:14px}
    .table-head,.row{display:grid;grid-template-columns:minmax(0,1fr) 120px 100px auto;gap:10px;align-items:center}
    .table-head{padding:12px;font-size:.73rem;text-transform:uppercase;letter-spacing:.12em;color:#415170;background:#f6f8fd;border-bottom:1px solid var(--line)}
    .row{padding:8px;border-bottom:1px solid #e9eef7}
    .field{width:100%;min-height:48px;border:1px solid #cfd8e6;border-radius:12px;padding:0 12px;font:inherit;background:#fff}
    .meta{font-size:.82rem;color:var(--muted);margin-top:6px}
    .badge{display:inline-block;padding:3px 8px;border-radius:999px;background:#edf3ff;color:#224a95;font-size:.74rem;font-weight:700;margin-left:6px}
    .actions{display:grid;grid-template-columns:minmax(0,1fr) 140px 120px;gap:10px;margin-top:12px}
    .side{padding:14px}
    .metric{padding:12px;border:1px solid var(--line);border-radius:14px;background:#f7faff;margin-bottom:10px}
    .metric small{display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.11em;font-size:.7rem;font-weight:800}
    .metric strong{display:block;font-size:1.9rem;letter-spacing:-.03em}
    .status.good{color:#0f6f50}.status.warn{color:#9a4d00}.status.bad{color:#b42318}
    .rules{font-size:.92rem;color:#394b67;line-height:1.55}
    .hidden{display:none !important}

    .overlay{position:fixed;inset:0;background:rgba(13,19,35,.48);display:grid;place-items:center;padding:12px;z-index:10}
    .auth-card{width:min(560px,100%);padding:18px}
    .tabs{display:flex;gap:8px;margin-bottom:10px}
    .tabs button{flex:1}
    .auth-form{display:grid;gap:10px}
    .message{min-height:20px;font-size:.9rem;color:#b42318}

    .program-picker{width:min(720px,100%);padding:18px}
    .program-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:12px}
    .pbtn{border:1px solid var(--line);border-radius:14px;padding:14px;background:#fff;cursor:pointer;text-align:left}
    .pbtn strong{display:block}
    .pbtn span{display:block;color:var(--muted);font-size:.86rem;margin-top:6px}

    @media(max-width:1120px){.layout{grid-template-columns:1fr}} @media(max-width:780px){.actions{grid-template-columns:1fr}.table-head{display:none}.row{grid-template-columns:1fr 1fr}}
  </style>
</head>
<body>
  <div class="top"></div>

  <div id="auth-overlay" class="overlay">
    <div class="panel auth-card">
      <h2 style="margin:0 0 10px">Student Account</h2>
      <div class="tabs">
        <button class="btn primary" id="tab-login">Login</button>
        <button class="btn ghost" id="tab-register">Create Account</button>
      </div>
      <form id="auth-form" class="auth-form">
        <input class="field" id="username" placeholder="Username" required />
        <input class="field" id="full_name" placeholder="Full Name (optional)" style="display:none" />
        <input class="field" id="student_id" placeholder="Student ID (optional)" style="display:none" />
        <input class="field" id="password" type="password" placeholder="Password (min 6 chars)" required />
        <button class="btn primary" id="auth-submit" type="submit">Login</button>
      </form>
      <div class="message" id="auth-message"></div>
    </div>
  </div>

  <div id="program-overlay" class="overlay hidden">
    <div class="panel program-picker">
      <h2 style="margin:0">Choose Your Degree Program</h2>
      <p style="margin:8px 0 0;color:#5c6e89">Select once on first login. You can still change later in Settings.</p>
      <div class="program-grid">
        <button class="pbtn" data-program="CIS"><strong>CIS</strong><span>Computing and Information Systems (handbook auto-fill)</span></button>
        <button class="pbtn" data-program="SE"><strong>SE</strong><span>Software Engineering (handbook auto-fill)</span></button>
        <button class="pbtn" data-program="DS"><strong>DS</strong><span>Data Science (manual fill, DS codes not in provided PDF)</span></button>
      </div>
      <div class="message" id="program-message"></div>
    </div>
  </div>

  <div class="wrap hidden" id="app-root">
    <div class="title">
      <div>
        <h1>Faculty of Computing GPA Calculator</h1>
        <div style="color:#667690">Sabaragamuwa University of Sri Lanka</div>
      </div>
      <div class="user">
        <div class="chip" id="whoami">Not logged in</div>
        <button class="btn ghost" id="logout-btn">Logout</button>
      </div>
    </div>

    <div class="layout">
      <div>
        <div id="semesters"></div>
        <div class="actions">
          <button class="btn primary" id="save-progress">Save Progress</button>
          <button class="btn primary" id="add-semester">+ Add Semester</button>
          <button class="btn ghost" id="change-program">Settings</button>
          <button class="btn ghost" id="reset">Reset</button>
        </div>
      </div>

      <div class="panel side">
        <div class="metric"><small>Semester GPA</small><strong id="m-sem">0.00</strong><span id="n-sem"></span></div>
        <div class="metric"><small>Overall GPA</small><strong id="m-overall">0.00</strong><span id="n-overall"></span></div>
        <div class="metric"><small>Final GPA</small><strong id="m-fgpa">0.00</strong><span id="n-fgpa"></span></div>
        <div class="metric"><small>Status</small><strong id="m-status" class="status warn">In Progress</strong><span id="n-status"></span></div>
        <div class="rules">
          Grade scale follows handbook (A+ to E). GPA uses credited GPA courses. Non-GPA English/Communication courses are tracked but excluded from GPA.
        </div>
      </div>
    </div>
  </div>

  <template id="semester-template">
    <section class="panel semester">
      <div class="head">
        <div><strong class="sem-title">Semester 1</strong><div class="sem-sub" style="color:#667690;font-size:.9rem"></div></div>
        <button class="btn ghost sem-toggle">Collapse</button>
      </div>
      <div class="body">
        <div class="table-head"><div>Course / Subject Code</div><div>Grade</div><div>Credits</div><div></div></div>
        <div class="rows"></div>
        <button class="btn ghost add-row" style="margin-top:10px">+ Add Class</button>
      </div>
    </section>
  </template>

  <template id="row-template">
    <div class="row">
      <div>
        <input class="field course" placeholder="e.g., IS1101 - Fundamentals of Information Systems" />
        <div class="meta note"></div>
      </div>
      <select class="field grade"></select>
      <select class="field credits"></select>
      <button class="btn ghost remove">Remove</button>
    </div>
  </template>

  <script>
    const PROGRAMS = __PROGRAMS__;
    const GRADE_POINTS = __GRADE_POINTS__;
    const GRADE_ORDER = ['--','A+','A','A-','B+','B','B-','C+','C','C-','D+','D','E'];
    const CREDIT_CHOICES = [1,2,3,4,6,8];

    let authMode = 'login';
    let token = '';
    let profile = { full_name: '', student_id: '' };
    let username = '';
    let state = null;
    let saveTimer = null;

    const authOverlay = document.getElementById('auth-overlay');
    const programOverlay = document.getElementById('program-overlay');
    const appRoot = document.getElementById('app-root');
    const semestersHost = document.getElementById('semesters');

    function uid(){ return crypto.randomUUID(); }

    function api(path, method='GET', body=null){
      const headers = {};
      if (body){ headers['Content-Type'] = 'application/json'; }
      if (token){ headers['Authorization'] = 'Bearer ' + token; }
      return fetch(path, { method, headers, body: body ? JSON.stringify(body) : undefined }).then(r => r.json());
    }

    function setAuthMode(mode){
      authMode = mode;
      document.getElementById('tab-login').className = 'btn ' + (mode === 'login' ? 'primary' : 'ghost');
      document.getElementById('tab-register').className = 'btn ' + (mode === 'register' ? 'primary' : 'ghost');
      document.getElementById('auth-submit').textContent = mode === 'login' ? 'Login' : 'Create Account';
      document.getElementById('auth-message').textContent = '';
      document.getElementById('full_name').style.display = mode === 'register' ? '' : 'none';
      document.getElementById('student_id').style.display = mode === 'register' ? '' : 'none';
    }

    function semesterRowsFor(program, number){
      const courses = PROGRAMS[program]?.semesters?.[number] || [];
      if (!courses.length){
        return Array.from({length:3}, () => ({ id: uid(), course:'', grade:'--', credits:3, nonGpa:false }));
      }
      return courses.map(c => ({
        id: uid(),
        course: `${c.code} - ${c.title}`,
        grade: '--',
        credits: Number(c.credits || 0),
        nonGpa: Boolean(c.non_gpa),
      }));
    }

    function createState(program){
      return {
        program,
        weights: [...(PROGRAMS[program].fgpa_weights || [0.2,0.2,0.3,0.3])],
        semesters: [{ id: uid(), number: 1, collapsed: false, rows: semesterRowsFor(program, 1) }],
      };
    }

    function gradeOptions(selected){
      return GRADE_ORDER.map(g => `<option value="${g}" ${g===selected?'selected':''}>${g}</option>`).join('');
    }

    function creditOptions(selected){
      return CREDIT_CHOICES.map(c => `<option value="${c}" ${c===Number(selected)?'selected':''}>${c}</option>`).join('');
    }

    function score(grade){ return GRADE_POINTS[grade] ?? 0; }

    function computeSemester(sem){
      let points = 0, credits = 0;
      for (const row of sem.rows){
        if (row.grade === '--' || !row.credits) continue;
        if (!row.nonGpa){
          points += score(row.grade) * Number(row.credits);
          credits += Number(row.credits);
        }
      }
      return { points, credits, gpa: credits ? points/credits : 0 };
    }

    function computeMetrics(){
      if (!state || !state.semesters.length){ return; }
      const last = state.semesters[state.semesters.length-1];
      const lastM = computeSemester(last);
      let totalPoints = 0, totalCredits = 0;
      for (const sem of state.semesters){
        const m = computeSemester(sem);
        totalPoints += m.points;
        totalCredits += m.credits;
      }
      const overall = totalCredits ? totalPoints/totalCredits : 0;

      const year = [{p:0,c:0},{p:0,c:0},{p:0,c:0},{p:0,c:0}];
      for (const sem of state.semesters){
        const y = Math.max(0, Math.min(3, Math.floor((sem.number-1)/2)));
        const m = computeSemester(sem);
        year[y].p += m.points;
        year[y].c += m.credits;
      }
      const w = state.weights || [0.2,0.2,0.3,0.3];
      let ws = 0, wt = 0;
      for (let i=0;i<4;i++){
        if (year[i].c > 0){
          ws += (year[i].p / year[i].c) * Number(w[i] || 0);
          wt += Number(w[i] || 0);
        }
      }
      const fgpa = wt ? ws / wt : 0;

      document.getElementById('m-sem').textContent = lastM.gpa.toFixed(2);
      document.getElementById('n-sem').textContent = `${lastM.credits} GPA credits in semester ${last.number}`;
      document.getElementById('m-overall').textContent = overall.toFixed(2);
      document.getElementById('n-overall').textContent = `${totalCredits} GPA credits total`;
      document.getElementById('m-fgpa').textContent = fgpa.toFixed(2);
      document.getElementById('n-fgpa').textContent = 'Weighted by 0.2, 0.2, 0.3, 0.3';

      let bad = false;
      for (const sem of state.semesters){
        for (const row of sem.rows){
          if (row.grade === '--') continue;
          if (!row.nonGpa && score(row.grade) < score('D')) bad = true;
          if (row.nonGpa && score(row.grade) < score('D+')) bad = true;
        }
      }

      const s = document.getElementById('m-status');
      const sn = document.getElementById('n-status');
      if (bad){ s.textContent = 'Needs Improvement'; s.className = 'status bad'; sn.textContent = 'One or more entered courses are below handbook minimums.'; }
      else if (fgpa >= 2 && fgpa > 0){ s.textContent = 'On Track'; s.className = 'status good'; sn.textContent = 'Current records satisfy FGPA minimum threshold.'; }
      else { s.textContent = 'In Progress'; s.className = 'status warn'; sn.textContent = 'Enter results to evaluate completion status.'; }
    }

    function inferNonGpa(course, existing){
      if (existing) return true;
      return /communication skills|general english|academic english|business english/i.test(course || '');
    }

    function render(){
      semestersHost.innerHTML = '';
      const tplSem = document.getElementById('semester-template');
      const tplRow = document.getElementById('row-template');
      const handbook = PROGRAMS[state.program]?.from_handbook;

      state.semesters.forEach((sem) => {
        const semNode = tplSem.content.firstElementChild.cloneNode(true);
        semNode.querySelector('.sem-title').textContent = `Semester ${sem.number}`;
        semNode.querySelector('.sem-sub').textContent = handbook ? 'Subject codes auto-filled from handbook catalog' : 'Manual entry (DS code table not in provided PDF)';

        const body = semNode.querySelector('.body');
        const rowsHost = semNode.querySelector('.rows');
        const toggleBtn = semNode.querySelector('.sem-toggle');
        if (sem.collapsed){ body.classList.add('hidden'); toggleBtn.textContent = 'Expand'; }
        toggleBtn.addEventListener('click', () => { sem.collapsed = !sem.collapsed; render(); queueSave(); });

        sem.rows.forEach((row) => {
          const rowNode = tplRow.content.firstElementChild.cloneNode(true);
          const course = rowNode.querySelector('.course');
          const grade = rowNode.querySelector('.grade');
          const credits = rowNode.querySelector('.credits');
          const note = rowNode.querySelector('.note');

          course.value = row.course || '';
          grade.innerHTML = gradeOptions(row.grade || '--');
          credits.innerHTML = creditOptions(Number(row.credits || 3));

          const nonGpa = inferNonGpa(row.course, row.nonGpa);
          row.nonGpa = nonGpa;
          note.textContent = nonGpa ? 'Non-GPA course' : 'GPA course';
          if (nonGpa){ note.innerHTML += '<span class="badge">non-GPA</span>'; }

          course.addEventListener('input', () => { row.course = course.value; row.nonGpa = inferNonGpa(row.course, row.nonGpa); render(); queueSave(); });
          grade.addEventListener('change', () => { row.grade = grade.value; computeMetrics(); queueSave(); });
          credits.addEventListener('change', () => { row.credits = Number(credits.value || 0); computeMetrics(); queueSave(); });
          rowNode.querySelector('.remove').addEventListener('click', () => {
            sem.rows = sem.rows.filter(r => r.id !== row.id);
            render(); queueSave();
          });
          rowsHost.appendChild(rowNode);
        });

        semNode.querySelector('.add-row').addEventListener('click', () => {
          sem.rows.push({ id: uid(), course: '', grade: '--', credits: 3, nonGpa: false });
          render(); queueSave();
        });

        semestersHost.appendChild(semNode);
      });

      computeMetrics();
      document.getElementById('whoami').textContent = `${username} · ${state.program}`;
    }

    function queueSave(){
      clearTimeout(saveTimer);
      saveTimer = setTimeout(async () => {
        if (!token || !state) return;
        await api('/api/save-progress', 'POST', { state });
      }, 350);
    }

    async function afterLogin(payload){
      token = payload.token;
      username = payload.username;
      profile.full_name = payload.full_name || '';
      profile.student_id = payload.student_id || '';
      let loadedState = payload.state;
      let program = payload.program;

      authOverlay.classList.add('hidden');

      if (!program){
        programOverlay.classList.remove('hidden');
        appRoot.classList.add('hidden');
        return;
      }

      programOverlay.classList.add('hidden');
      appRoot.classList.remove('hidden');
      if (!loadedState || typeof loadedState !== 'object'){
        loadedState = createState(program);
      }
      state = loadedState;
      if (!state.program) state.program = program;
      render();
      await api('/api/save-progress','POST',{state});
    }

    document.getElementById('tab-login').addEventListener('click', () => setAuthMode('login'));
    document.getElementById('tab-register').addEventListener('click', () => setAuthMode('register'));
    setAuthMode('login');

    document.getElementById('auth-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const u = document.getElementById('username').value.trim().toLowerCase();
      const p = document.getElementById('password').value;
      const endpoint = authMode === 'login' ? '/api/login' : '/api/register';
      const body = { username: u, password: p };
      if (authMode === 'register'){
        body.full_name = document.getElementById('full_name').value.trim();
        body.student_id = document.getElementById('student_id').value.trim();
      }
      const result = await api(endpoint, 'POST', body);
      if (!result.ok){ document.getElementById('auth-message').textContent = result.message || 'Authentication failed.'; return; }
      await afterLogin(result);
    });

    for (const btn of document.querySelectorAll('[data-program]')){
      btn.addEventListener('click', async () => {
        const program = btn.dataset.program;
        const res = await api('/api/set-program', 'POST', { program });
        if (!res.ok){ document.getElementById('program-message').textContent = res.message || 'Cannot set degree program.'; return; }
        state = res.state || createState(program);
        state.program = program;
        programOverlay.classList.add('hidden');
        appRoot.classList.remove('hidden');
        render();
        await api('/api/save-progress','POST',{state});
      });
    }

    document.getElementById('add-semester').addEventListener('click', () => {
      const next = state.semesters.length + 1;
      if (next > 8) return;
      state.semesters.push({ id: uid(), number: next, collapsed: false, rows: semesterRowsFor(state.program, next) });
      render(); queueSave();
    });

    document.getElementById('save-progress').addEventListener('click', async () => {
      if (!token || !state) return;
      await api('/api/save-progress', 'POST', { state });
      const n = document.getElementById('n-status');
      const old = n.textContent;
      n.textContent = 'Progress saved.';
      setTimeout(() => { n.textContent = old; }, 1800);
    });

    document.getElementById('change-program').addEventListener('click', () => {
      programOverlay.classList.remove('hidden');
      appRoot.classList.add('hidden');
    });

    document.getElementById('reset').addEventListener('click', async () => {
      state = createState(state.program);
      render();
      await api('/api/save-progress','POST',{state});
    });

    document.getElementById('logout-btn').addEventListener('click', async () => {
      await api('/api/logout', 'POST', {});
      token = '';
      username = '';
      state = null;
      appRoot.classList.add('hidden');
      programOverlay.classList.add('hidden');
      authOverlay.classList.remove('hidden');
      document.getElementById('auth-message').textContent = '';
      document.getElementById('password').value = '';
    });
  </script>
</body>
</html>
"""


def build_html() -> str:
    return (
        HTML.replace("__PROGRAMS__", json.dumps(PROGRAMS, ensure_ascii=True))
        .replace("__GRADE_POINTS__", json.dumps(GRADE_POINTS, ensure_ascii=True))
    )


def build_admin_login_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Admin Login - SUSL GPA Calculator</title>
  <style>
    :root { --bg:#f3f6fb; --panel:#fff; --ink:#17233b; --muted:#66768f; --line:#d8dfeb; --accent:#1e59e6; }
    *{box-sizing:border-box} body{margin:0;font-family:'Trebuchet MS','Segoe UI',sans-serif;background:linear-gradient(180deg,#f8fbff,#edf2fb);color:var(--ink)}
    .container{display:grid;place-items:center;min-height:100vh;padding:12px}
    .panel{background:var(--panel);border:1px solid var(--line);border-radius:20px;box-shadow:0 14px 28px rgba(18,40,86,.08);padding:32px;width:min(480px,100%)}
    .panel h1{margin:0 0 20px;font-size:1.8rem}
    .form{display:grid;gap:12px}
    .field{width:100%;min-height:48px;border:1px solid #cfd8e6;border-radius:12px;padding:0 12px;font:inherit;background:#fff}
    .btn{border:0;border-radius:12px;padding:12px 20px;font:inherit;font-weight:800;cursor:pointer;width:100%}
    .btn.primary{background:linear-gradient(135deg,#2f64ec,#1749d3);color:#fff}
    .message{min-height:20px;font-size:.9rem;color:#b42318;margin-top:12px}
    .footer{margin-top:20px;text-align:center;font-size:.85rem;color:var(--muted)}
  </style>
</head>
<body>
  <div class="container">
    <div class="panel">
      <h1>Admin Login</h1>
      <form class="form" id="admin-form">
        <input class="field" id="admin-username" placeholder="Admin Username" required />
        <input class="field" id="admin-password" type="password" placeholder="Password" required />
        <button class="btn primary" type="submit">Login</button>
        <div class="message" id="admin-message"></div>
      </form>
      <div class="footer">
        <p style="margin:12px 0 0">Default credentials: admin / admin123</p>
        <a href="/" style="color:var(--accent);text-decoration:none">← Back to Student Portal</a>
      </div>
    </div>
  </div>

  <script>
    document.getElementById('admin-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('admin-username').value.trim().toLowerCase();
      const password = document.getElementById('admin-password').value;
      const msg = document.getElementById('admin-message');
      msg.textContent = '';

      const resp = await fetch('/api/admin-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      }).then(r => r.json());

      if (!resp.ok) {
        msg.textContent = resp.message || 'Login failed';
        return;
      }
      localStorage.setItem('admin_token', resp.token);
      localStorage.setItem('admin_username', resp.admin_username);
      window.location.href = '/admin';
    });
  </script>
</body>
</html>
"""


def build_admin_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Admin Dashboard - SUSL GPA Calculator</title>
  <style>
    :root { --bg:#f3f6fb; --panel:#fff; --ink:#17233b; --muted:#66768f; --line:#d8dfeb; --accent:#1e59e6; }
    *{box-sizing:border-box} body{margin:0;font-family:'Trebuchet MS','Segoe UI',sans-serif;background:linear-gradient(180deg,#f8fbff,#edf2fb);color:var(--ink)}
    .top{height:12px;background:#302840}
    .wrap{max-width:1280px;margin:0 auto;padding:18px}
    .header{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:20px;flex-wrap:wrap}
    .header h1{margin:0;font-size:2rem}
    .header .admin-info{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
    .chip{border:1px solid var(--line);padding:8px 12px;border-radius:999px;background:#fff;color:#35507f;font-weight:700}
    .btn{border:0;border-radius:12px;padding:10px 14px;font:inherit;font-weight:800;cursor:pointer}
    .btn.primary{background:linear-gradient(135deg,#2f64ec,#1749d3);color:#fff}
    .btn.ghost{background:#fff;border:1px solid var(--line);color:#27406b}
    .btn.danger{background:#c83c3c;color:#fff}
    .panel{background:var(--panel);border:1px solid var(--line);border-radius:20px;box-shadow:0 14px 28px rgba(18,40,86,.08)}
    .stats-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:18px}
    .stat-card{padding:20px}
    .stat-card .label{font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);font-weight:700}
    .stat-card .value{font-size:2.4rem;font-weight:900;margin-top:8px}
    .content-grid{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;align-items:start}
    .students-section{padding:20px}
    .students-section h2{margin:0 0 14px;font-size:1.3rem}
    .students-toolbar{display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin-bottom:12px}
    .search{flex:1;min-width:220px;min-height:46px;border:1px solid #cfd8e6;border-radius:12px;padding:0 12px;font:inherit;background:#fff}
    .students-table{width:100%;border-collapse:collapse}
    .students-table thead{background:#f6f8fd;border-bottom:1px solid var(--line)}
    .students-table th{padding:12px;text-align:left;font-size:.75rem;text-transform:uppercase;letter-spacing:.12em;color:#415170;font-weight:700}
    .students-table td{padding:12px;border-bottom:1px solid #e9eef7;vertical-align:top}
    .students-table tr:hover{background:#f9fbff}
    .status-badge{display:inline-block;padding:4px 8px;border-radius:999px;font-size:.75rem;font-weight:700}
    .status-badge.active{background:#c7f0d8;color:#0f6f50}
    .status-badge.inactive{background:#f0e0d8;color:#8b5a00}
    .row-actions{display:flex;gap:8px;flex-wrap:wrap}
    .mini{border:1px solid var(--line);background:#fff;border-radius:10px;padding:7px 10px;font:inherit;font-weight:700;cursor:pointer;color:#27406b}
    .mini.danger{border-color:#edb4b4;color:#b42318}
    .side-stack{display:grid;gap:16px}
    .side-card{padding:18px}
    .side-card h3{margin:0 0 12px;font-size:1.05rem}
    .form-grid{display:grid;gap:10px}
    .field{width:100%;min-height:46px;border:1px solid #cfd8e6;border-radius:12px;padding:0 12px;font:inherit;background:#fff}
    .message{min-height:20px;font-size:.9rem;color:#b42318}
    .ok{color:#0f6f50}
    @media(max-width:1020px){.content-grid{grid-template-columns:1fr}.stats-grid{grid-template-columns:1fr}.side-stack{order:-1}}
  </style>
</head>
<body>
  <div class="top"></div>

  <div class="wrap">
    <div class="header">
      <div>
        <h1>Admin Dashboard</h1>
        <div style="color:#667690">Faculty of Computing GPA Calculator</div>
      </div>
      <div class="admin-info">
        <div class="chip" id="admin-name">Admin</div>
        <button class="btn ghost" id="logout-btn">Logout</button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="panel stat-card">
        <div class="label">Total Students</div>
        <div class="value" id="stat-total">0</div>
      </div>
      <div class="panel stat-card">
        <div class="label">With Program Selected</div>
        <div class="value" id="stat-program">0</div>
      </div>
      <div class="panel stat-card">
        <div class="label">With Progress</div>
        <div class="value" id="stat-progress">0</div>
      </div>
    </div>

    <div class="content-grid">
      <div class="panel students-section">
        <h2>Student Accounts</h2>
        <div class="students-toolbar">
          <input class="search" id="student-search" placeholder="Search by username, name, ID, or program" />
          <div class="chip" id="search-count">0 shown</div>
        </div>
        <table class="students-table" id="students-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Full Name</th>
              <th>Student ID</th>
              <th>Program</th>
              <th>Progress</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="students-body">
            <tr><td colspan="6" style="text-align:center;color:var(--muted)">Loading...</td></tr>
          </tbody>
        </table>
      </div>

      <div class="side-stack">
        <div class="panel side-card">
          <h3>Change Admin Password</h3>
          <form class="form-grid" id="password-form">
            <input class="field" id="current-password" type="password" placeholder="Current password" required />
            <input class="field" id="new-password" type="password" placeholder="New password" required />
            <input class="field" id="confirm-password" type="password" placeholder="Confirm new password" required />
            <button class="btn primary" type="submit">Update Password</button>
            <div class="message" id="password-message"></div>
          </form>
        </div>

        <div class="panel side-card">
          <h3>Search Tips</h3>
          <div style="color:#4d5f7a;line-height:1.6;font-size:.95rem">
            Use the search box to quickly filter students by username, full name, student ID, or program.
            The rename action updates the student username across active sessions.
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let adminToken = localStorage.getItem('admin_token');
    let adminUsername = localStorage.getItem('admin_username');
    let studentsCache = [];
    let searchQuery = '';

    if (!adminToken) {
      window.location.href = '/admin/login.html';
    }

    document.getElementById('admin-name').textContent = adminUsername || 'Admin';

    function authHeaders(extra = {}) {
      return { ...extra, 'Authorization': 'Bearer ' + adminToken };
    }

    function matchesQuery(student, query) {
      if (!query) return true;
      const haystack = [student.username, student.full_name, student.student_id, student.program].join(' ').toLowerCase();
      return haystack.includes(query.toLowerCase());
    }

    function renderStudents() {
      const body = document.getElementById('students-body');
      const filtered = studentsCache.filter(student => matchesQuery(student, searchQuery));
      let withProgress = 0;
      body.innerHTML = '';

      for (const student of filtered) {
        if (student.has_progress) withProgress++;
        const row = document.createElement('tr');
        row.innerHTML = `
          <td><strong>${student.username}</strong></td>
          <td>${student.full_name || '-'}</td>
          <td>${student.student_id || '-'}</td>
          <td>${student.program}</td>
          <td><span class="status-badge ${student.has_progress ? 'active' : 'inactive'}">${student.has_progress ? 'Yes' : 'No'}</span></td>
          <td>
            <div class="row-actions">
              <button class="mini" data-rename="${student.username}">Rename</button>
            </div>
          </td>
        `;
        body.appendChild(row);
      }

      if (!filtered.length) {
        body.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted)">No students match your search.</td></tr>';
      }

      document.getElementById('stat-progress').textContent = withProgress;
      document.getElementById('search-count').textContent = `${filtered.length} shown`;

      for (const button of body.querySelectorAll('[data-rename]')) {
        button.addEventListener('click', async () => {
          const oldUsername = button.dataset.rename;
          const newUsername = prompt(`Rename ${oldUsername} to:` , oldUsername);
          if (!newUsername) return;
          const result = await fetch('/api/admin/rename-student', {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ old_username: oldUsername, new_username: newUsername.trim().toLowerCase() })
          }).then(r => r.json());
          if (!result.ok) {
            alert(result.message || 'Rename failed');
            return;
          }
          await loadStudents();
        });
      }
    }

    async function loadStats() {
      const resp = await fetch('/api/admin/stats', { headers: authHeaders() }).then(r => r.json());
      if (resp.ok) {
        document.getElementById('stat-total').textContent = resp.total_students;
        document.getElementById('stat-program').textContent = resp.with_program;
      }
    }

    async function loadStudents() {
      const resp = await fetch('/api/admin/students', { headers: authHeaders() }).then(r => r.json());
      if (!resp.ok) return;
      studentsCache = resp.students || [];
      renderStudents();
    }

    document.getElementById('student-search').addEventListener('input', (event) => {
      searchQuery = event.target.value.trim();
      renderStudents();
    });

    document.getElementById('password-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const currentPassword = document.getElementById('current-password').value;
      const newPassword = document.getElementById('new-password').value;
      const confirmPassword = document.getElementById('confirm-password').value;
      const message = document.getElementById('password-message');
      message.textContent = '';

      if (newPassword !== confirmPassword) {
        message.textContent = 'New password and confirmation do not match.';
        return;
      }

      const resp = await fetch('/api/admin/change-password', {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
      }).then(r => r.json());

      if (!resp.ok) {
        message.textContent = resp.message || 'Password update failed.';
        return;
      }

      message.textContent = 'Password updated successfully.';
      message.className = 'message ok';
      event.target.reset();
      setTimeout(() => { message.textContent = ''; message.className = 'message'; }, 2200);
    });

    document.getElementById('logout-btn').addEventListener('click', async () => {
      await fetch('/api/admin/logout', {
        method: 'POST',
        headers: authHeaders()
      });
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_username');
      window.location.href = '/admin/login.html';
    });

    loadStats();
    loadStudents();
    setInterval(() => { loadStats(); loadStudents(); }, 5000);
  </script>
</body>
</html>
"""


def main() -> None:
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), GPAHandler)
    url = f"http://{host}:{port}"
    print(f"SUSL GPA app running at {url}")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

from flask import Flask, request, jsonify, render_template, redirect, url_for
import requests

app = Flask(__name__)

# ---------- Supabase config ----------
SUPABASE_URL = "https://nlfqwznilwfmncghwwff.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5sZnF3em5pbHdmbW5jZ2h3d2ZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwNzA0NTgsImV4cCI6MjA3MTY0NjQ1OH0.--zoMyjNAQzlPYW1MV91SortRJ3wNL4-8opEQVN0xRA"

SB_HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def sb_request(method: str, path: str, data=None):
    """Small helper around Supabase REST (PostgREST)."""
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    resp = requests.request(method, url, headers=SB_HEADERS, json=data)
    try:
        return resp.status_code, resp.json()
    except ValueError:
        # Empty or non-JSON body
        return resp.status_code, {"message": resp.text or "OK"}

# ---------- UI routes ----------
@app.route("/")
def index():
    # Fetch all data for dashboard
    _, students = sb_request("GET", "students?select=register_number,student_name&order=register_number.asc")
    if isinstance(students, dict): students = []

    _, courses = sb_request("GET", "courses?select=id,course_name&order=id.asc")
    if isinstance(courses, dict): courses = []

    _, enrollments = sb_request(
        "GET",
        "student_courses?select=id,student_id,course_id,students(register_number,student_name),courses(id,course_name)&order=id.desc"
    )
    if isinstance(enrollments, dict): enrollments = []

    _, payments = sb_request(
        "GET",
        "payments?select=id,amount_paid,paid_at,student_courses(id,students(register_number,student_name),courses(id,course_name))&order=paid_at.desc"
    )
    if isinstance(payments, dict): payments = []

    return render_template(
        'dashboard.html',
        students=students,
        courses=courses,
        enrollments=enrollments,
        payments=payments
    )

@app.route("/students")
def students_page():
    # Get students with enrollment count
    _, students = sb_request("GET", "students?select=register_number,student_name&order=register_number.asc")
    if isinstance(students, dict): students = []
    
    # Get enrollment counts
    _, enrollments = sb_request("GET", "student_courses?select=student_id")
    if isinstance(enrollments, dict): enrollments = []
    
    enrollment_counts = {}
    for e in enrollments:
        sid = e.get('student_id')
        if sid:
            enrollment_counts[sid] = enrollment_counts.get(sid, 0) + 1
    
    for s in students:
        s['enrollment_count'] = enrollment_counts.get(s['register_number'], 0)

    return render_template('students.html', students=students)

@app.route("/courses")
def courses_page():
    # Get courses with enrollment count
    _, courses = sb_request("GET", "courses?select=id,course_name&order=id.asc")
    if isinstance(courses, dict): courses = []
    
    # Get enrollment counts
    _, enrollments = sb_request("GET", "student_courses?select=course_id")
    if isinstance(enrollments, dict): enrollments = []
    
    enrollment_counts = {}
    for e in enrollments:
        cid = e.get('course_id')
        if cid:
            enrollment_counts[cid] = enrollment_counts.get(cid, 0) + 1
    
    for c in courses:
        c['enrollment_count'] = enrollment_counts.get(c['id'], 0)

    return render_template('courses.html', courses=courses)

@app.route("/enrollments")
def enrollments_page():
    _, students = sb_request("GET", "students?select=register_number,student_name&order=student_name.asc")
    if isinstance(students, dict): students = []

    _, courses = sb_request("GET", "courses?select=id,course_name&order=course_name.asc")
    if isinstance(courses, dict): courses = []

    _, enrollments = sb_request(
        "GET",
        "student_courses?select=id,student_id,course_id,students(register_number,student_name),courses(id,course_name)&order=id.desc"
    )
    if isinstance(enrollments, dict): enrollments = []

    # Get payment totals for each enrollment
    _, payments = sb_request("GET", "payments?select=student_course_id,amount_paid")
    if isinstance(payments, dict): payments = []
    
    payment_totals = {}
    for p in payments:
        scid = p.get('student_course_id')
        if scid:
            payment_totals[scid] = payment_totals.get(scid, 0) + p.get('amount_paid', 0)
    
    for e in enrollments:
        e['total_paid'] = payment_totals.get(e['id'], 0)

    return render_template(
        'enrollments.html',
        students=students,
        courses=courses,
        enrollments=enrollments
    )

@app.route("/payments")
def payments_page():
    _, enrollments = sb_request(
        "GET",
        "student_courses?select=id,student_id,course_id,students(register_number,student_name),courses(id,course_name)&order=id.desc"
    )
    if isinstance(enrollments, dict): enrollments = []

    _, payments = sb_request(
        "GET",
        "payments?select=id,amount_paid,paid_at,student_courses(id,students(register_number,student_name),courses(id,course_name))&order=paid_at.desc"
    )
    if isinstance(payments, dict): payments = []

    return render_template(
        'payments.html',
        enrollments=enrollments,
        payments=payments
    )

# ---- UI: Create + Delete (POST) - Redirect to appropriate page ----
@app.post("/students/create")
def ui_create_student():
    reg_no = request.form.get("register_number")
    name = request.form.get("student_name")
    if not (reg_no and name):
        return redirect(request.referrer or url_for("index"))
    sb_request("POST", "students", {"register_number": int(reg_no), "student_name": name})
    return redirect(request.referrer or url_for("students_page"))

@app.post("/students/delete/<int:reg_no>")
def ui_delete_student(reg_no):
    sb_request("DELETE", f"students?register_number=eq.{reg_no}")
    return redirect(url_for("students_page"))

@app.post("/courses/create")
def ui_create_course():
    course_name = request.form.get("course_name")
    if course_name:
        sb_request("POST", "courses", {"course_name": course_name})
    return redirect(request.referrer or url_for("courses_page"))

@app.post("/courses/delete/<int:course_id>")
def ui_delete_course(course_id):
    sb_request("DELETE", f"courses?id=eq.{course_id}")
    return redirect(url_for("courses_page"))

@app.post("/enrollments/create")
def ui_create_enrollment():
    student_id = request.form.get("student_id")
    course_id = request.form.get("course_id")
    if student_id and course_id:
        sb_request("POST", "student_courses", {"student_id": int(student_id), "course_id": int(course_id)})
    return redirect(request.referrer or url_for("enrollments_page"))

@app.post("/enrollments/delete/<int:enroll_id>")
def ui_delete_enrollment(enroll_id):
    sb_request("DELETE", f"student_courses?id=eq.{enroll_id}")
    return redirect(url_for("enrollments_page"))

@app.post("/payments/create")
def ui_create_payment():
    sc_id = request.form.get("student_course_id")
    amount = request.form.get("amount_paid")
    if sc_id and amount:
        sb_request("POST", "payments", {"student_course_id": int(sc_id), "amount_paid": int(amount)})
    return redirect(request.referrer or url_for("payments_page"))

@app.post("/payments/delete/<int:payment_id>")
def ui_delete_payment(payment_id):
    sb_request("DELETE", f"payments?id=eq.{payment_id}")
    return redirect(url_for("payments_page"))

# ---------- REST API (CRUD) ----------
# Students
@app.post("/api/students")
def api_create_student():
    code, data = sb_request("POST", "students", request.json)
    return jsonify(data), code

@app.get("/api/students")
def api_list_students():
    code, data = sb_request("GET", "students?select=*")
    return jsonify(data), code

@app.put("/api/students/<int:reg_no>")
def api_update_student(reg_no):
    code, data = sb_request("PATCH", f"students?register_number=eq.{reg_no}", request.json)
    return jsonify(data), code

@app.delete("/api/students/<int:reg_no>")
def api_remove_student(reg_no):
    code, data = sb_request("DELETE", f"students?register_number=eq.{reg_no}")
    return jsonify(data), code

# Courses
@app.post("/api/courses")
def api_create_course():
    code, data = sb_request("POST", "courses", request.json)
    return jsonify(data), code

@app.get("/api/courses")
def api_list_courses():
    code, data = sb_request("GET", "courses?select=*")
    return jsonify(data), code

@app.put("/api/courses/<int:course_id>")
def api_update_course(course_id):
    code, data = sb_request("PATCH", f"courses?id=eq.{course_id}", request.json)
    return jsonify(data), code

@app.delete("/api/courses/<int:course_id>")
def api_remove_course(course_id):
    code, data = sb_request("DELETE", f"courses?id=eq.{course_id}")
    return jsonify(data), code

# Enrollments
@app.post("/api/student_courses")
def api_create_enrollment():
    code, data = sb_request("POST", "student_courses", request.json)
    return jsonify(data), code

@app.get("/api/student_courses")
def api_list_enrollments():
    code, data = sb_request(
        "GET",
        "student_courses?select=id,student_id,course_id&order=id.asc"
    )
    return jsonify(data), code



@app.delete("/api/student_courses/<int:enroll_id>")
def api_remove_enrollment(enroll_id):
    code, data = sb_request("DELETE", f"student_courses?id=eq.{enroll_id}")
    return jsonify(data), code

# Payments
@app.post("/api/payments")
def api_create_payment():
    code, data = sb_request("POST", "payments", request.json)
    return jsonify(data), code

@app.get("/api/payments")
def api_list_payments():
    code, data = sb_request(
        "GET",
        "payments?select=id,student_course_id,amount_paid,paid_at&order=id.asc"
    )
    return jsonify(data), code


@app.put("/api/payments/<int:payment_id>")
def api_update_payment(payment_id):
    # Use PATCH for partial updates
    code, data = sb_request("PATCH", f"payments?id=eq.{payment_id}", request.json)
    return jsonify(data), code


@app.delete("/api/payments/<int:payment_id>")
def api_remove_payment(payment_id):
    code, data = sb_request("DELETE", f"payments?id=eq.{payment_id}")
    return jsonify(data), code

if __name__ == "__main__":
    app.run(debug=True)

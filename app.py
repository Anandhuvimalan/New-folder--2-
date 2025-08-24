from flask import Flask, request, jsonify, render_template_string, redirect
import requests

app = Flask(__name__)

# Supabase config
SUPABASE_URL = "https://nlfqwznilwfmncghwwff.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5sZnF3em5pbHdmbW5jZ2h3d2ZmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwNzA0NTgsImV4cCI6MjA3MTY0NjQ1OH0.--zoMyjNAQzlPYW1MV91SortRJ3wNL4-8opEQVN0xRA"
TABLE_NAME = "students"   # Make sure you have created this table in Supabase

headers = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"  # ensure Supabase returns inserted/updated rows
}

# ------------------ HTML Form -------------------
form_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Student Payment Form</title>
</head>
<body>
    <h2>Student Payment Form</h2>
    <form action="/create" method="post">
        <label>Name:</label><br>
        <input type="text" name="name" required><br><br>

        <label>Course Taken:</label><br>
        <input type="text" name="course_taken" required><br><br>

        <label>Amount Paid:</label><br>
        <input type="number" name="amount_paid" required><br><br>

        <input type="submit" value="Submit">
    </form>

    <h3>All Records</h3>
    <ul>
        {% for student in students %}
            <li>
                {{ student["id"] }} - {{ student["name"] }} | {{ student["course_taken"] }} | ₹{{ student["amount_paid"] }}
                <a href="/delete/{{ student['id'] }}">Delete</a>
            </li>
        {% endfor %}
    </ul>
</body>
</html>
"""

# ------------------ Web Routes -------------------

@app.route("/")
def index():
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*", headers=headers)
    students = resp.json() if resp.text else []
    return render_template_string(form_html, students=students)


@app.route("/create", methods=["POST"])
def create():
    data = {
        "name": request.form["name"],
        "course_taken": request.form["course_taken"],
        "amount_paid": int(request.form["amount_paid"])
    }
    requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", headers=headers, json=data)
    return redirect("/")


@app.route("/delete/<int:student_id>")
def delete(student_id):
    requests.delete(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{student_id}", headers=headers)
    return redirect("/")

# ------------------ API Routes -------------------

# CREATE
@app.route("/api/students", methods=["POST"])
def api_create():
    data = request.json
    resp = requests.post(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}", headers=headers, json=data)
    try:
        return jsonify(resp.json())
    except ValueError:
        return jsonify({"status": resp.status_code, "message": "Inserted successfully"})

# READ
@app.route("/api/students", methods=["GET"])
def api_read():
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?select=*", headers=headers)
    try:
        return jsonify(resp.json())
    except ValueError:
        return jsonify({"status": resp.status_code, "message": "No data"})

# UPDATE
@app.route("/api/students/<int:student_id>", methods=["PUT"])
def api_update(student_id):
    data = request.json
    resp = requests.patch(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{student_id}", headers=headers, json=data)
    try:
        return jsonify(resp.json())
    except ValueError:
        return jsonify({"status": resp.status_code, "message": "Updated successfully"})

# DELETE
@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_delete(student_id):
    resp = requests.delete(f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?id=eq.{student_id}", headers=headers)
    return jsonify({"status": resp.status_code, "message": f"Deleted student {student_id}"})


if __name__ == "__main__":
    app.run(debug=True)

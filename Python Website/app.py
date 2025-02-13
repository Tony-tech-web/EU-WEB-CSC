import streamlit as st
import sqlite3
import bcrypt
import pandas as pd
import os

# Database setup
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matric_number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password TEXT NOT NULL
)''')

cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        project_file TEXT NOT NULL,
        preview_image TEXT,
        paid_content TEXT,
        student_name TEXT NOT NULL,
        matric_number TEXT NOT NULL
    )
""")

try:
    cursor.execute("ALTER TABLE projects ADD COLUMN preview_image TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass  # Ignore if the column already exists


cursor.execute('''
CREATE TABLE IF NOT EXISTS student_courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matric_number TEXT NOT NULL,
    course_code TEXT NOT NULL,
    FOREIGN KEY (matric_number) REFERENCES users(matric_number),
    FOREIGN KEY (course_code) REFERENCES subjects(course_code)
)
''')
conn.commit()

cursor.execute("INSERT INTO student_courses (matric_number, course_code) VALUES (?, ?)", ("EU230102-3696", "CSC201"))
conn.commit()


# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(name, matric_number, password):
    hashed_pw = hash_password(password)
    try:
        cursor.execute("INSERT INTO users (matric_number, name, password) VALUES (?, ?, ?)", 
                       (matric_number, name, hashed_pw))
        conn.commit()
        return True
    except:
        return False

def login_user(matric_number, password):
    cursor.execute("SELECT * FROM users WHERE matric_number = ?", (matric_number,))
    user = cursor.fetchone()
    if user and verify_password(password, user[3]):
        return user
    return None

def upload_project(title, description, project_file, preview_image, paid_content, paid_content_name, user):
    project_path = f"uploads/{project_file.name}"
    with open(project_path, "wb") as f:
        f.write(project_file.getbuffer())

    image_path = None
    if preview_image is not None:
        image_path = f"uploads/{preview_image.name}"
        with open(image_path, "wb") as f:
            f.write(preview_image.getbuffer())

    paid_path = None
    if isinstance(paid_content, str):  
        paid_path = paid_content  
    elif paid_content is not None and hasattr(paid_content, "type"):  
        paid_path = f"uploads/{paid_content.name}"
        with open(paid_path, "wb") as f:
            f.write(paid_content.getbuffer())

    # ✅ Use the provided name or fallback to the paid content itself
    paid_content_name = paid_content_name if paid_content_name else paid_path 

    cursor.execute("""
        INSERT INTO projects (title, description, project_file, preview_image, paid_content, paid_content_name, student_name, matric_number) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, description, project_path, image_path, paid_path, paid_content_name, user[2], user[1]))
    conn.commit()

def get_projects():
    return pd.read_sql_query("SELECT * FROM projects", conn)

def delete_project(project_id):
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()

def update_project(project_id, title, description):
    cursor.execute("UPDATE projects SET title = ?, description = ? WHERE id = ?", (title, description, project_id))
    conn.commit()

def get_student_courses(matric_number):
    cursor.execute("""
        SELECT subjects.course_code, subjects.course_title, subjects.semester 
        FROM student_courses 
        JOIN subjects ON student_courses.course_code = subjects.course_code
        WHERE student_courses.matric_number = ?
    """, (matric_number,))
    return cursor.fetchall()


# UI Elements
st.set_page_config(page_title="Student Project Hub", page_icon="📂", layout="wide")
st.title("📂 Student Project Hub")

# Authentication
auth_section = st.sidebar.radio("Navigation", ["Login", "Register", "View Projects"])

if auth_section == "Register":
    st.sidebar.subheader("Register")
    name = st.sidebar.text_input("Name")
    matric_number = st.sidebar.text_input("Matric Number")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Register"):
        if register_user(name, matric_number, password):
            st.sidebar.success("Registered successfully! Please log in.")
        else:
            st.sidebar.error("Matric Number already exists.")

elif auth_section == "Login":
    st.sidebar.subheader("Login")
    matric_number = st.sidebar.text_input("Matric Number")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        user = login_user(matric_number, password)
        if user:
            st.session_state["user"] = user
            st.sidebar.success("Logged in successfully!")
        else:
            st.sidebar.error("Invalid login details.")

# Main Application
if "user" in st.session_state:
    st.sidebar.write(f"Welcome, *{st.session_state['user'][2]}*")
    
    # Check if admin
    is_admin = st.session_state["user"][1] == "admin"

    options = ["Subjects", "Upload Project", "View Projects", "Admin Panel" if is_admin else None, "Logout"]
    options = [opt for opt in options if opt is not None]  # Remove None values

    page = st.sidebar.radio("Dashboard", options)

    if page == "Upload Project":
        st.subheader("📤 Upload Your Project")
        title = st.text_input("Project Title")
        description = st.text_area("Project Description")
        project_file = st.file_uploader("Upload Project File", type=["zip", "pdf", "py", "txt"])
        preview_image = st.file_uploader("Upload Preview Image (Optional)", type=["png", "jpg", "jpeg"])
        paid_content = st.file_uploader("Upload Paid Example (Optional)", type=["zip", "pdf", "mp4", "py"])
        paid_link = st.text_input("Paid Content Link (Optional)")

    if st.button("Upload"):
        if title and description and project_file:
            upload_project(title, description, project_file, preview_image, paid_link if paid_link else paid_content, st.session_state["user"])
            st.success("Project uploaded successfully!")
        else:
            st.error("Please fill in all required fields.")


    elif page == "View Projects":
        st.subheader("📜 Projects List")
        projects = get_projects()
        for index, row in projects.iterrows():
            with st.expander(f"📌 {row['title']} - {row['student_name']} ({row['matric_number']})"):
                st.write(row["description"])
             
                # Display preview image if available
                if row["preview_image"]:
                    st.image(row["preview_image"], caption="Project Preview", use_container_width=True)

                st.download_button(
                    label="Download Project",
                    data=open(row["project_file"], "rb"),
                    file_name=row["project_file"].split("/")[-1],
                    key=f"download_{index}"
                )
                if row["paid_content"]:
                    paid_link_name = row["paid_content_name"] if row["paid_content_name"] else row["paid_content"]  
                if row["paid_content"].startswith("http"):
                    st.markdown(f"[{paid_link_name}]({row['paid_content']})")
                else:
                    st.download_button(
                        label=f"Download {paid_link_name}",
                        data=open(row["paid_content"], "rb"),
                        file_name=row["paid_content"].split("/")[-1],
                        key=f"paid_download_{index}"
                    )
                    
                #Subjects
    elif page == "Subjects":
        st.subheader("📚 Your Courses")
    
    user_matric = st.session_state["user"][1]  # Get student matric number
    student_courses = get_student_courses(user_matric)  # Get enrolled courses

    if not student_courses:
        st.warning("You are not enrolled in any courses yet.")
    else:
        for course_code, course_title, semester in student_courses:
            with st.expander(f"📖 {course_title} ({course_code}) - {semester}"):
                st.write(f"**Course Code:** {course_code}")
                st.write(f"**Semester:** {semester}")
                
                # Fetch Scheme of Work for this course
                cursor.execute("SELECT week, topic FROM scheme_of_work WHERE course_code = ?", (course_code,))
                scheme = cursor.fetchall()
                
                if scheme:
                    st.subheader("📅 Scheme of Work")
                    for week, topic in scheme:
                        st.write(f"**Week {week}:** {topic}")
                else:
                    st.info("No scheme of work available for this course.")

                # Fetch Assignments for this course
                cursor.execute("SELECT assignment_title, description, due_date FROM assignments WHERE course_code = ?", (course_code,))
                assignments = cursor.fetchall()
                
                if assignments:
                    st.subheader("📝 Assignments")
                    for title, desc, due_date in assignments:
                        st.write(f"**{title}** - *Due: {due_date}*")
                        st.write(desc)
                else:
                    st.info("No assignments available for this course.")




    if page == "Admin Panel" and is_admin:
        st.subheader("🔧 Admin Panel - Manage Projects")
        projects = get_projects()
        for index, row in projects.iterrows():
            with st.expander(f"📌 {row['title']} - {row['student_name']} ({row['matric_number']})"):
                 new_title = st.text_input("Edit Title", value=row["title"], key=f"title_{index}")
                 new_description = st.text_area("Edit Description", value=row["description"], key=f"desc_{index}")
                
            if st.button("Update", key=f"update_{index}"):
                update_project(row["id"], new_title, new_description)
                st.success("Project updated successfully!")
                st.rerun()
                
            if st.button("Delete", key=f"delete_{index}"):
                delete_project(row["id"])
                st.warning("Project deleted!")
                st.rerun()

if "user" in st.session_state:
    user_role = st.session_state["user"][4]  # Fetch the role of the logged-in user
    if user_role == "admin":
        if user_role == "admin":
            st.sidebar.page_link("pages/admin.py", label="🔧 Admin Panel")


    elif page == "Logout":
        del st.session_state["user"]
        st.sidebar.success("Logged out successfully!")
        st.rerun()

else:
    st.info("Please log in or register to upload and view projects.")

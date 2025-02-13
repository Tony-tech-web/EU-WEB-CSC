import streamlit as st
import sqlite3
import pandas as pd

# ✅ Set page config ONLY IF NOT already set in app.py
if not hasattr(st.session_state, "page_config_set"):
    st.set_page_config(page_title="Admin Dashboard", page_icon="⚙", layout="wide")
    st.session_state.page_config_set = True  # Mark as set to prevent duplicate calls

# Database setup
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

# Check if user is logged in
if "user" not in st.session_state:
    st.warning("You must be logged in to access this page.")
    st.switch_page("app.py")  # Redirect to login page

# Get user details
user = st.session_state.get("user")

# Restrict access to admin only
if user is None or len(user) < 5 or user[4] != "admin":
    st.error("Access denied! Only admins can access this page.")
    st.stop()

st.title("⚙ Admin Dashboard")

# Restrict access to admin only
if user[4] != "admin":  # Assuming role is stored in index 3 of the user tuple
    st.error("Access denied! Only admins can access this page.")
    st.stop()

# Admin Dashboard Functions
def get_users():
    return pd.read_sql_query("SELECT * FROM users", conn)

def delete_user(user_id):
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()

def update_user_role(user_id, new_role):
    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()

def get_projects():
    return pd.read_sql_query("SELECT * FROM projects", conn)

def delete_project(project_id):
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()

def update_project(project_id, title, description):
    cursor.execute("UPDATE projects SET title = ?, description = ? WHERE id = ?", (title, description, project_id))
    conn.commit()

# Streamlit UI

section = st.sidebar.radio("Manage", ["Users", "Projects", "Reports", "Settings", "Logout"])

if section == "Users":
    st.subheader("User Management")
    users = get_users()
    for _, row in users.iterrows():
        with st.expander(f"{row['name']} ({row['matric_number']}) - {row['role']}"):
            # ✅ Add a unique key for each selectbox
            new_role = st.selectbox(
                "Update Role",
                ["student", "admin"],
                index=0 if row['role'] == "student" else 1,
                key=f"role_select_{row['id']}"  # Unique key
            )
            if st.button("Update Role", key=f"update_{row['id']}"):
                update_user_role(row['id'], new_role)
                st.success("Role updated!")
                st.rerun()
            if st.button("Delete User", key=f"delete_{row['id']}"):
                delete_user(row['id'])
                st.warning("User deleted!")
                st.rerun()

elif section == "Projects":
    st.subheader("Project Management")
    projects = get_projects()
    for _, row in projects.iterrows():
        with st.expander(f"{row['title']} - {row['student_name']}"):
            new_title = st.text_input("Edit Title", value=row["title"], key=f"title_{row['id']}")
            new_description = st.text_area("Edit Description", value=row["description"], key=f"desc_{row['id']}")
            if st.button("Update", key=f"update_{row['id']}"):
                update_project(row["id"], new_title, new_description)
                st.success("Project updated!")
                st.rerun()
            if st.button("Delete", key=f"delete_{row['id']}"):
                delete_project(row["id"])
                st.warning("Project deleted!")
                st.rerun()

elif section == "Reports":
    st.subheader("Reports & Analytics")
    st.write("Number of Users:", len(get_users()))
    st.write("Number of Projects:", len(get_projects()))

elif section == "Settings":
    st.subheader("System Settings")
    st.write("Modify system preferences, enable/disable features.")

elif section == "Logout":
    del st.session_state["user"]
    st.sidebar.success("Logged out successfully!")
    st.rerun()

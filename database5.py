import streamlit as st
import smtplib
from datetime import datetime
import pandas as pd
from streamlit_option_menu import option_menu
import os
import json

col1, col2, col3, col4 = st.columns([1, 1, 4, 1])
with col1:
    st.write("")
with col2:
    st.write("")
with col3:
    st.image("wingate.png", width=150, use_column_width=False, output_format='auto')
with col4:
    st.write("")

def primary():
    school_attendance_app("Primary School Attendance", "primary_students_database.xlsx", "primary_attendance_log.csv")

def secondary():
    school_attendance_app("Secondary School Attendance", "secondary_students_database.xlsx", "secondary_attendance_log.csv")

def load_admin_password():
    if os.path.exists("admin_password.json"):
        with open("admin_password.json", "r") as file:
            return json.load(file)["password"]
    else:
        return "admin123"

def save_admin_password(password):
    with open("admin_password.json", "w") as file:
        json.dump({"password": password}, file)

def school_attendance_app(title, database_file, attendance_log_file):
    admin_password = load_admin_password()

    try:
        df = pd.read_excel(database_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Name", "PIN_Dad", "PIN_Mom", "Dad Email", "Mom Email", "Last Action"])

    df = df.astype(str)

    if 'children_database' not in st.session_state:
        st.session_state.children_database = df

    def send_email(recipient_email, child_name, action, signer):
        sender_email = "wingateabuja@gmail.com"  # Replace with your email
        sender_password = "boki opay ozsu voyi"  # Replace with your password

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            subject = f"Child {action.capitalize()} Confirmation"
            body = f"Your child, {child_name}, has been {action} by {signer} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(sender_email, recipient_email, message)
            return True
        except smtplib.SMTPException as e:
            st.error(f"An error occurred while sending email for {action}: {e}")
            return False
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            return False
        finally:
            server.quit()

    def add_student(df, name, pin_dad, pin_mom, dad_email, mom_email):
        if not df[(df["PIN_Dad"] == pin_dad) | (df["PIN_Mom"] == pin_mom)].empty:
            st.error("Student with the same PIN for dad or mom already exists.")
        else:
            new_student = pd.DataFrame({
                "Name": [name],
                "PIN_Dad": [pin_dad],
                "PIN_Mom": [pin_mom],
                "Dad Email": [dad_email],
                "Mom Email": [mom_email],
                "Last Action": ["None"]
            })
            df = pd.concat([df, new_student], ignore_index=True)
            df.to_excel(database_file, index=False)
            st.session_state.children_database = df
            st.success("Student added successfully.")

    def remove_student(df, name):
        df = df[df["Name"] != name]
        df.to_excel(database_file, index=False)
        st.session_state.children_database = df
        st.success(f"Student {name} removed successfully.")

    def log_attendance(name, signer, action, attendance_log_file):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attendance_log = pd.DataFrame({"Name": [name], "Signer": [signer], "Action": [action], "DateTime": [now]})
        attendance_log.to_csv(attendance_log_file, mode='a', header=not st.session_state.log_file_exists, index=False)
        st.session_state.log_file_exists = True

    def edit_student(df, old_name, new_name, new_pin_dad, new_pin_mom, new_dad_email, new_mom_email):
        index = df[df['Name'] == old_name].index
        df.loc[index, 'Name'] = new_name
        df.loc[index, 'PIN_Dad'] = new_pin_dad
        df.loc[index, 'PIN_Mom'] = new_pin_mom
        df.loc[index, 'Dad Email'] = new_dad_email
        df.loc[index, 'Mom Email'] = new_mom_email
        df.to_excel(database_file, index=False)
        st.success("Student information updated successfully.")

    def change_admin_password(old_password, new_password, confirm_password):
        if old_password != admin_password:
            st.error("Old password is incorrect.")
            return False
        if new_password != confirm_password:
            st.error("New password and confirmation do not match.")
            return False
        save_admin_password(new_password)
        st.success("Admin password changed successfully.")
        return True

    def clear_report(attendance_log_file):
        open(attendance_log_file, "w").close()
        st.session_state.log_file_exists = False
        st.success("Attendance report cleared successfully.")

    if 'log_file_exists' not in st.session_state:
        st.session_state.log_file_exists = False

    if not os.path.isfile(attendance_log_file):
        with open(attendance_log_file, "w") as file:
            file.write("Name,Signer,Action,DateTime\n")

    st.title(title)

    with st.sidebar:
        selected = option_menu("Main Menu", ["Attendance", "View Report", "Admin"],
                               icons=['calendar3', 'clipboard-data', 'person-check'])

    if selected == "Attendance":
        child_pin = st.text_input("Enter Child's PIN:")

        if st.button("Sign In"):
            if df["PIN_Dad"].isin([child_pin]).any():
                student_data = df[df["PIN_Dad"] == child_pin]
                child_name = student_data.iloc[0]["Name"]
                dad_email = student_data.iloc[0]["Dad Email"]
                if send_email(dad_email, child_name, "signed in", "dad"):
                    st.success(f"{child_name} signed in successfully by dad!")
                    log_attendance(child_name, "dad", "sign in", attendance_log_file)
                    df.loc[df["Name"] == child_name, "Last Action"] = "Sign In by Dad"
            elif df["PIN_Mom"].isin([child_pin]).any():
                student_data = df[df["PIN_Mom"] == child_pin]
                child_name = student_data.iloc[0]["Name"]
                mom_email = student_data.iloc[0]["Mom Email"]
                if send_email(mom_email, child_name, "signed in", "mom"):
                    st.success(f"{child_name} signed in successfully by mom!")
                    log_attendance(child_name, "mom", "sign in", attendance_log_file)
                    df.loc[df["Name"] == child_name, "Last Action"] = "Sign In by Mom"
            else:
                st.error("Invalid PIN. Please enter a valid PIN.")

        if st.button("Sign Out"):
            if df["PIN_Dad"].isin([child_pin]).any():
                student_data = df[df["PIN_Dad"] == child_pin]
                child_name = student_data.iloc[0]["Name"]
                dad_email = student_data.iloc[0]["Dad Email"]
                if send_email(dad_email, child_name, "signed out", "dad"):
                    st.success(f"{child_name} signed out successfully by dad!")
                    log_attendance(child_name, "dad", "sign out", attendance_log_file)
                    df.loc[df["Name"] == child_name, "Last Action"] = "Sign Out by Dad"
            elif df["PIN_Mom"].isin([child_pin]).any():
                student_data = df[df["PIN_Mom"] == child_pin]
                child_name = student_data.iloc[0]["Name"]
                mom_email = student_data.iloc[0]["Mom Email"]
                if send_email(mom_email, child_name, "signed out", "mom"):
                    st.success(f"{child_name} signed out successfully by mom!")
                    log_attendance(child_name, "mom", "sign out", attendance_log_file)
                    df.loc[df["Name"] == child_name, "Last Action"] = "Sign Out by Mom"
            else:
                st.error("Invalid PIN. Please enter a valid PIN.")

    elif selected == "View Report":
        st.subheader("View Report")
        child_pin = st.text_input("Enter Child's PIN:")

        if st.button("Generate Report"):
            try:
                attendance_log = pd.read_csv(attendance_log_file)
                if df["PIN_Dad"].isin([child_pin]).any():
                    child_attendance = attendance_log[attendance_log["Signer"] == "dad"]
                elif df["PIN_Mom"].isin([child_pin]).any():
                    child_attendance = attendance_log[attendance_log["Signer"] == "mom"]
                else:
                    st.error("Invalid PIN. Please enter a valid PIN.")

                if not child_attendance.empty:
                    st.write(f"Attendance Report for Child with PIN {child_pin}:")
                    st.write(child_attendance)
                else:
                    st.write("No attendance records found for this child.")
            except FileNotFoundError:
                st.error("Attendance records not found.")

    elif selected == "Admin":
        password = st.text_input("Enter Admin Password:", type="password")
        if password == admin_password:
            st.subheader("Admin Panel")
            action = st.selectbox("Select Action:", options=["Add Student", "Remove Student", "Edit Student", "Change Password", "Clear Report", "View Report"])
            if action == "Add Student":
                new_name = st.text_input("Enter Student's Name:")
                new_pin_dad = st.text_input("Enter Dad's PIN:")
                new_pin_mom = st.text_input("Enter Mom's PIN:")
                new_dad_email = st.text_input("Enter Dad's Email:")
                new_mom_email = st.text_input("Enter Mom's Email:")
                if st.button("Add Student"):
                    add_student(df, new_name, new_pin_dad, new_pin_mom, new_dad_email, new_mom_email)
            elif action == "Remove Student":
                remove_name = st.selectbox("Select Student to Remove:", options=list(df[df["PIN_Dad"].str.len() > 0]["Name"]))
                if st.button("Remove Student"):
                    remove_student(df, remove_name)
            elif action == "Edit Student":
                st.subheader("Edit Student")
                edit_name = st.selectbox("Select Student to Edit:", options=list(df[df["PIN_Dad"].str.len() > 0]["Name"]))
                if not edit_name:
                    st.warning("Please select a student to edit.")
                    return
                new_name = st.text_input("Enter New Name:", value=edit_name)
                new_pin_dad = st.text_input("Enter New Dad's PIN:", value=df[df["Name"] == edit_name]["PIN_Dad"].iloc[0])
                new_pin_mom = st.text_input("Enter New Mom's PIN:", value=df[df["Name"] == edit_name]["PIN_Mom"].iloc[0])
                new_dad_email = st.text_input("Enter New Dad's Email:", value=df[df["Name"] == edit_name]["Dad Email"].iloc[0])
                new_mom_email = st.text_input("Enter New Mom's Email:", value=df[df["Name"] == edit_name]["Mom Email"].iloc[0])
                if st.button("Save Changes"):
                    edit_student(df, edit_name, new_name, new_pin_dad, new_pin_mom, new_dad_email, new_mom_email)
            elif action == "Change Password":
                st.subheader("Change Admin Password")
                old_password = st.text_input("Enter Old Password:", type="password")
                new_password = st.text_input("Enter New Password:", type="password")
                confirm_password = st.text_input("Confirm New Password:", type="password")
                if st.button("Change Password"):
                    change_admin_password(old_password, new_password, confirm_password)
            elif action == "Clear Report":
                st.subheader("Clear Attendance Report")
                if st.button("Clear Report"):
                    clear_report(attendance_log_file)
            elif action == "View Report":
                st.subheader("View Report")
                try:
                    attendance_log = pd.read_csv(attendance_log_file)
                    st.write("Attendance Log:")
                    st.write(attendance_log)
                except FileNotFoundError:
                    st.error("Attendance records not found.")
        else:
            st.error("Invalid password. Please try again.")

if __name__ == "__main__":
    st.sidebar.title("Choose Category")
    category = st.sidebar.radio("Select Category:", ("Primary School", "Secondary School"))

    if category == "Primary School":
        primary()
    elif category == "Secondary School":
        secondary()

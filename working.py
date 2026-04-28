import streamlit as st
import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from auth import login_page, register_page, logout
# Handle Authentication
query_params = st.experimental_get_query_params()
current_page = query_params.get("page", ["login"])[0]
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
if not st.session_state.logged_in:
    if current_page == "register":
        register_page()
    else:
        login_page()
    st.stop()

# Logout button
st.sidebar.button("Logout", on_click=logout)

# Set background image function
def set_background(image_url):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("{image_url}");
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Set background for the main page
set_background("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTvN_hTP_4vOdXH64DFj6c9sw5aWxrDhJQD2w&s")

# Load the trained model
model = load_model("student.h5", compile=False)
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005), loss="mse", metrics=["mae"])

# Load dataset
df = pd.read_csv("adjusted_student_performance.csv")

# Define feature columns
feature_columns = ["Gender", "AttendanceRate", "StudyHoursPerWeek_x", "PreviousGrade_x", 
                   "ExtracurricularActivities", "ParentalSupport", "StudyHoursPerWeek_y", "PreviousGrade_y"]

# Encode categorical variables
gender_encoder = LabelEncoder()
df["Gender"] = gender_encoder.fit_transform(df["Gender"])

parental_support_map = {"Low": 0, "Medium": 1, "High": 2}
df["ParentalSupport"] = df["ParentalSupport"].map(parental_support_map)

# Standardize data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[feature_columns])

# Sidebar Navigation
menu = st.sidebar.radio("Navigation", ["Predict Grade", "Quiz", "Upload Document", "Teacher Portal"])

# Initialize session storage for documents
if "documents" not in st.session_state:
    st.session_state.documents = {"teacher": [], "student": []}

document_store = st.session_state.documents

# ------------------ STUDENT GRADE PREDICTION ------------------
if menu == "Predict Grade":
    st.title("📚 Student Performance Predictor")

    gender_input = st.selectbox("Gender", ["Male", "Female"])
    attendance_rate = st.slider("Attendance Rate (0-100)", 0, 100, 85)
    study_hours_x = st.number_input("Study Hours Per Week (Dataset 1)", min_value=0.0, value=10.0)
    previous_grade_x = st.number_input("Previous Grade (Dataset 1, 0-100)", min_value=0.0, value=65.0)
    extracurricular = st.slider("Extracurricular Activities (0-3)", 0, 3, 2)
    parental_support_input = st.selectbox("Parental Support", ["Low", "Medium", "High"])
    study_hours_y = st.number_input("Study Hours Per Week (Dataset 2)", min_value=0.0, value=8.0)
    previous_grade_y = st.number_input("Previous Grade (Dataset 2, 0-100)", min_value=0.0, value=63.0)

    if st.button("Predict Grade"):
        gender_encoded = 1 if gender_input == "Male" else 0
        parental_support = parental_support_map[parental_support_input]
        
        user_input = np.array([[gender_encoded, attendance_rate, study_hours_x, previous_grade_x,
                                extracurricular, parental_support, study_hours_y, previous_grade_y]])
        
        user_input_scaled = scaler.transform(user_input).reshape((1, -1, 1))
        predicted_grade = model.predict(user_input_scaled)[0][0] * 100
        
        performance, recommendation = "", ""
        if predicted_grade >= 90:
            performance, recommendation = "Excellent 🌟", "Keep up the great work!"
        elif predicted_grade >= 75:
            performance, recommendation = "Good ✅", "Maintain consistency and focus on minor improvements."
        elif predicted_grade >= 50:
            performance, recommendation = "Average ⚠️", "Increase study hours and focus on weaker areas."
        else:
            performance, recommendation = "Needs Improvement ❌", "Seek tutoring and revise regularly."
        
        st.success(f"📊 **Predicted Final Grade:** {predicted_grade:.2f}/100")
        st.info(f"📌 **Performance Level:** {performance}")
        st.warning(f"📝 **Recommendation:** {recommendation}")

# ------------------ QUIZ SYSTEM ------------------
elif menu == "Quiz":
    st.title("📝 Student Quiz")
    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = []
    
    selected_questions = st.session_state.quiz_questions
    score = 0
    for i, (question, options, correct_answer) in enumerate(selected_questions):
        answer = st.radio(question, options, key=i)
        if answer == correct_answer:
            score += 1
    
    if st.button("Submit Quiz"):
        st.success(f"Your Score: {score}/{len(selected_questions)}")

# ------------------ STUDENT DOCUMENT UPLOAD ------------------
# ------------------ STUDENT DOCUMENT UPLOAD (LIMIT: 5 FILES) ------------------
if menu == "Upload Document":
    st.title("📂 Student Document Upload")

    uploaded_files = st.file_uploader("Upload up to 5 files", type=["pdf", "docx", "txt"], accept_multiple_files=True)

    if uploaded_files:
        # Remove duplicates and enforce 5-file limit
        existing_files = {file.name for file in document_store["student"]}
        new_files = [file for file in uploaded_files if file.name not in existing_files]
        
        if len(document_store["student"]) + len(new_files) > 5:
            st.warning("⚠️ You can only upload up to 5 files. Please remove old files if needed.")
        else:
            document_store["student"].extend(new_files)
            st.success(f"✅ {len(new_files)} new file(s) uploaded successfully!")

    # Display uploaded files
    st.write(f"📑 **Uploaded Student Files ({len(document_store['student'])}/5):**")
    if document_store["student"]:
        for idx, file in enumerate(document_store["student"]):
            st.download_button(label=f"📄 {file.name}", data=file, file_name=file.name, key=f"student_doc_{idx}")
    else:
        st.info("No student files uploaded yet.")
# ------------------ TEACHER PORTAL ------------------
elif menu == "Teacher Portal":
    st.title("👩‍🏫 Teacher Portal")

    # Upload Reference Documents (Teachers)
    with st.expander("📂 Upload Reference Documents"):
        uploaded_files = st.file_uploader("Upload up to 5 files", type=["pdf", "docx", "txt"], accept_multiple_files=True)

        if uploaded_files:
            # Remove duplicates and enforce 5-file limit
            existing_files = {file.name for file in document_store["teacher"]}
            new_files = [file for file in uploaded_files if file.name not in existing_files]
            
            if len(document_store["teacher"]) + len(new_files) > 5:
                st.warning("⚠️ You can only upload up to 5 files. Please remove old files if needed.")
            else:
                document_store["teacher"].extend(new_files)
                st.success(f"✅ {len(new_files)} new file(s) uploaded successfully!")

    # Display uploaded files
    st.write(f"📑 **Uploaded Teacher Files ({len(document_store['teacher'])}/5):**")
    if document_store["teacher"]:
        for idx, file in enumerate(document_store["teacher"]):
            st.download_button(label=f"📄 {file.name}", data=file, file_name=file.name, key=f"teacher_doc_{idx}")
    else:
        st.info("No teacher files uploaded yet.")

    # Quiz Section for Teachers
    with st.expander("📝 Create Quiz Questions"):
        question = st.text_input("Enter Question")
        options = [st.text_input(f"Option {i+1}") for i in range(3)]
        correct_answer = st.selectbox("Correct Answer", options)
        
        if st.button("Add Question"):
            if "quiz_questions" not in st.session_state:
                st.session_state.quiz_questions = []
            st.session_state.quiz_questions.append((question, options, correct_answer))
            st.success("Question added successfully!")
import streamlit as st
from database import init_db, authenticate_user
import time

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(
    page_title='College Placement Portal',
    page_icon='🎓',
    layout='wide',
    initial_sidebar_state='expanded'
)

# ---------------------- INITIALIZE DATABASE ----------------------
init_db()

# ---------------------- MODERN CSS THEME ----------------------
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

    @keyframes gradientMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background: linear-gradient(120deg, #00c6ff, #0072ff, #89f7fe, #4facfe);
        background-size: 300% 300%;
        animation: gradientMove 10s ease infinite;
        color: #001f54;
    }

    .login-card {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        text-align: center;
        backdrop-filter: blur(8px);
        transition: 0.4s;
    }
    .login-card:hover { transform: scale(1.02); }

    h1 { color: #001f54; font-size: 42px; font-weight: 700; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); }
    h2, h3, label { color: #002b5b !important; font-weight: 600 !important; }

    .stTextInput input, .stSelectbox select {
        background: #fff; border: 1px solid #cce0ff; border-radius: 10px; padding: 10px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1); color: #001f54;
    }

    .stButton > button {
        background: linear-gradient(90deg, #0072ff, #00c6ff);
        color: white; border: none; padding: 10px 40px;
        border-radius: 30px; font-weight: 600; transition: 0.3s;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #0052d4, #4364f7, #6fb1fc);
        transform: translateY(-2px);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #002b5b, #004b93);
        color: white;
    }
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: white !important;
    }
    </style>
''', unsafe_allow_html=True)

# ---------------------- TITLE ----------------------
st.markdown('''
    <div style='text-align:center;'>
        <h1>🎓 College Placement Management Portal</h1>
        <p class='subtitle'>Empowering Students • Connecting Departments • Driving Careers</p>
    </div>
''', unsafe_allow_html=True)

# ---------------------- LOGIN CARD ----------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    role = st.selectbox('Login as', ['Select Role', 'Student', 'HOD', 'Admin'])
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')

    if st.button('🚀 Login Now'):
        if role == 'Select Role':
            st.warning('⚠️ Please select your role.')
        elif not username or not password:
            st.warning('⚠️ Please enter all credentials.')
        else:
            user = authenticate_user(username, password, role)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = role

                # ✅ Redirect page setup
                if role == 'Admin':
                    redirect_page = 'pages/admin_portal.py'
                elif role == 'HOD':
                    redirect_page = 'pages/hod_portal.py'
                elif role == 'Student':
                    redirect_page = 'pages/student_portal.py'
                else:
                    redirect_page = None

                if redirect_page:
                    st.success('✅ Login successful! Redirecting...')
                    with st.spinner("Redirecting, please wait..."):
                        time.sleep(2)
                        st.switch_page(redirect_page)
            else:
                st.error('❌ Invalid username or password. Contact Placement Cell.')

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------- SIDEBAR ----------------------
st.sidebar.title('📌 Navigation')

if 'logged_in' in st.session_state and st.session_state['logged_in']:
    st.sidebar.success(f'👋 Welcome, {st.session_state["username"]} ({st.session_state["role"]})')

    if st.session_state['role'] == 'Student':
        st.sidebar.page_link('pages/student_portal.py', label='🎓 Student Portal')
    elif st.session_state['role'] == 'HOD':
        st.sidebar.page_link('pages/hod_portal.py', label='👨‍🏫 HOD Dashboard')
    elif st.session_state['role'] == 'Admin':
        st.sidebar.page_link('pages/admin_portal.py', label='👩‍💼 Admin Dashboard')
        st.sidebar.page_link('pages/drives_portal.py', label='🚀 Drive Portal')

    if st.sidebar.button('🚪 Logout'):
        st.session_state.clear()
        st.rerun()
else:
    st.sidebar.info('🔑 Please log in to access your portal.')

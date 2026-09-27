import streamlit as st
import base64
import os

from database import (
    get_db_connection,
    hash_password,
    log_audit
)


# ==========================================================
# BACKGROUND IMAGE
# ==========================================================

def get_background_image():

    image_path = os.path.join(
        "assets",
        "login_bg.jpg"
    )

    if not os.path.exists(image_path):
        return ""

    with open(
        image_path,
        "rb"
    ) as image_file:

        encoded = base64.b64encode(
            image_file.read()
        ).decode()

    return encoded


# ==========================================================
# LOGIN PAGE
# ==========================================================

def login_page():

    background_image = get_background_image()


    # ======================================================
    # BACKGROUND
    # ======================================================

    if background_image:

        background_css = f"""
        .stApp {{
            background-image:
                linear-gradient(
                    135deg,
                    rgba(255, 132, 186, 0.55),
                    rgba(255, 214, 230, 0.45)
                ),
                url("data:image/jpeg;base64,{background_image}");

            background-size: cover;
            background-position: center;
            background-attachment: fixed;

            min-height: 100vh;
            overflow-x: hidden;
        }}
        """

    else:

        background_css = """
        .stApp {

            background:
                linear-gradient(
                    135deg,
                    #FFB6D2,
                    #FFD6E6
                );

            min-height: 100vh;
            overflow-x: hidden;
        }
        """


    # ======================================================
    # CSS
    # ======================================================

    st.markdown(
        f"""
        <style>

        {background_css}


        /* =================================================
           GLOBAL
           ================================================= */

        * {{
            box-sizing:
                border-box;
        }}


        html,
        body {{
            margin:
                0;

            padding:
                0;

            overflow-x:
                hidden;
        }}


        /* =================================================
           PAGE CONTAINER
           ================================================= */

        .block-container {{

            width:
                100% !important;

            max-width:
                680px !important;

            margin:
                0 auto !important;

            padding-top:
                30px !important;

            padding-bottom:
                30px !important;

            padding-left:
                20px !important;

            padding-right:
                20px !important;
        }}


        /* =================================================
           MAIN LOGIN CARD
           ================================================= */

        .st-key-login_container {{

            width:
                100% !important;

            max-width:
                600px !important;

            margin:
                0 auto !important;

            background-color:
                #FFE4EF !important;

            background:
                #FFE4EF !important;

            background-image:
                none !important;

            border:
                2px solid #FFFFFF !important;

            border-radius:
                28px !important;

            padding:
                40px !important;

            box-shadow:
                0 20px 50px
                rgba(
                    190,
                    55,
                    115,
                    0.25
                ) !important;

            opacity:
                1 !important;

            overflow:
                hidden !important;
        }}


        /* =================================================
           FORCE INNER AREAS SOLID
           ================================================= */

        .st-key-login_container > div {{

            background-color:
                #FFE4EF !important;

            background:
                #FFE4EF !important;

            background-image:
                none !important;

            opacity:
                1 !important;
        }}


        .st-key-login_container
        [data-testid="stVerticalBlock"] {{

            background-color:
                #FFE4EF !important;

            background:
                #FFE4EF !important;

            background-image:
                none !important;

            opacity:
                1 !important;
        }}


        /* =================================================
           LOGO
           ================================================= */

        .login-logo {{

            width:
                135px;

            height:
                135px;

            max-width:
                35vw;

            max-height:
                35vw;

            margin:
                0 auto 20px auto;

            border-radius:
                50%;

            background-color:
                #FFE4EF !important;

            background:
                #FFE4EF !important;

            background-image:
                none !important;

            display:
                flex;

            align-items:
                center;

            justify-content:
                center;

            overflow:
                hidden;

            border:
                4px solid #FFFFFF !important;

            box-shadow:
                0 8px 25px
                rgba(
                    190,
                    55,
                    115,
                    0.20
                );

            flex-shrink:
                0;
        }}


        .login-logo img {{

            width:
                125px;

            height:
                125px;

            max-width:
                100%;

            max-height:
                100%;

            object-fit:
                contain;

            border-radius:
                50%;
        }}


        /* =================================================
           WELCOME TITLE
           ================================================= */

        .welcome-title {{

            text-align:
                center;

            color:
                #C21868;

            font-size:
                32px;

            font-weight:
                800;

            line-height:
                1.2;

            margin-top:
                5px;

            margin-bottom:
                8px;

            text-shadow:
                0 2px 4px
                rgba(
                    255,
                    255,
                    255,
                    0.60
                );

            word-wrap:
                break-word;
        }}


        /* =================================================
           WELCOME SUBTITLE
           ================================================= */

        .welcome-subtitle {{

            text-align:
                center;

            color:
                #6E4355;

            font-size:
                15px;

            line-height:
                1.5;

            margin-bottom:
                30px;

            word-wrap:
                break-word;
        }}


        /* =================================================
           TEXT INPUT CONTAINER
           ================================================= */

        .st-key-login_container
        div[data-testid="stTextInput"] {{

            background:
                transparent !important;

            padding:
                0 0 15px 0 !important;

            margin:
                0 !important;

            width:
                100% !important;
        }}


        /* =================================================
           INPUT LABEL
           ================================================= */

        .st-key-login_container
        div[data-testid="stTextInput"] label {{

            color:
                #6E4355 !important;

            font-weight:
                600 !important;

            font-size:
                14px !important;
        }}


        /* =================================================
           INPUT BOX
           ================================================= */

        .st-key-login_container
        div[data-testid="stTextInput"] input {{

            width:
                100% !important;

            height:
                50px !important;

            min-height:
                50px !important;

            border-radius:
                13px !important;

            border:
                2px solid #FFFFFF !important;

            background-color:
                #FFFFFF !important;

            background:
                #FFFFFF !important;

            color:
                #333333 !important;

            font-size:
                15px !important;

            padding-left:
                15px !important;

            padding-right:
                15px !important;

            box-shadow:
                0 4px 12px
                rgba(
                    150,
                    40,
                    90,
                    0.08
                ) !important;
        }}


        /* =================================================
           INPUT FOCUS
           ================================================= */

        .st-key-login_container
        div[data-testid="stTextInput"]
        input:focus {{

            border-color:
                #C21868 !important;

            box-shadow:
                0 0 0 3px
                rgba(
                    194,
                    24,
                    104,
                    0.15
                ) !important;
        }}


        /* =================================================
           ALL BUTTONS
           ================================================= */

        .st-key-login_container
        div.stButton > button {{

            width:
                100% !important;

            min-height:
                52px !important;

            border-radius:
                14px !important;

            border:
                none !important;

            font-size:
                16px !important;

            font-weight:
                700 !important;

            white-space:
                normal !important;

            word-wrap:
                break-word !important;

            transition:
                all 0.2s ease;
        }}


        /* =================================================
           LOGIN BUTTON
           ================================================= */

        .st-key-login_container
        div.stButton > button:first-child {{

            background:
                linear-gradient(
                    135deg,
                    #D41472,
                    #FF4F9A
                ) !important;

            color:
                #FFFFFF !important;

            box-shadow:
                0 7px 18px
                rgba(
                    180,
                    30,
                    100,
                    0.25
                ) !important;
        }}


        /* =================================================
           BUTTON HOVER
           ================================================= */

        .st-key-login_container
        div.stButton > button:hover {{

            transform:
                translateY(-1px);

            box-shadow:
                0 10px 22px
                rgba(
                    180,
                    30,
                    100,
                    0.35
                ) !important;
        }}


        /* =================================================
           PUBLIC MODE
           ================================================= */

        .public-mode {{

            width:
                100%;

            margin-top:
                25px;

            padding:
                20px;

            border-radius:
                17px;

            background-color:
                #FFE4EF !important;

            background:
                #FFE4EF !important;

            background-image:
                none !important;

            border:
                2px solid #FFFFFF !important;

            text-align:
                center;

            box-shadow:
                0 5px 15px
                rgba(
                    190,
                    55,
                    115,
                    0.08
                );

            opacity:
                1 !important;

            overflow:
                hidden;
        }}


        /* =================================================
           PUBLIC TITLE
           ================================================= */

        .public-title {{

            color:
                #C21868;

            font-size:
                17px;

            font-weight:
                800;

            margin-bottom:
                6px;

            line-height:
                1.3;
        }}


        /* =================================================
           PUBLIC TEXT
           ================================================= */

        .public-text {{

            color:
                #6E4355;

            font-size:
                13px;

            line-height:
                1.4;

            margin-bottom:
                0;
        }}


        /* =================================================
           CUSTOMER AI CHATBOT BUTTON
           ================================================= */

        .st-key-login_container
        div.stButton:last-child > button {{

            min-height:
                44px !important;

            border-radius:
                11px !important;

            background:
                #FFE4EF !important;

            background-color:
                #FFE4EF !important;

            color:
                #C21868 !important;

            border:
                2px solid #C21868 !important;

            font-size:
                13px !important;

            font-weight:
                600 !important;

            box-shadow:
                none !important;

            margin-top:
                10px !important;
        }}


        .st-key-login_container
        div.stButton:last-child > button:hover {{

            background:
                #FFD0E3 !important;

            background-color:
                #FFD0E3 !important;

            color:
                #C21868 !important;

            transform:
                none !important;
        }}


        /* =================================================
           ALERTS
           ================================================= */

        div[data-testid="stAlert"] {{

            border-radius:
                12px !important;

            font-size:
                13px !important;

            word-wrap:
                break-word;
        }}


        /* =================================================
           HIDE STREAMLIT UI
           ================================================= */

        header {{
            visibility:
                hidden;
        }}

        footer {{
            visibility:
                hidden;
        }}


        /* =================================================
           TABLET
           ================================================= */

        @media (max-width: 1100px) {{

            .block-container {{

                max-width:
                    680px !important;

                padding-left:
                    25px !important;

                padding-right:
                    25px !important;
            }}

            .st-key-login_container {{

                max-width:
                    600px !important;

                padding:
                    35px !important;
            }}
        }}


        /* =================================================
           SMALL TABLET
           ================================================= */

        @media (max-width: 768px) {{

            .block-container {{

                max-width:
                    100% !important;

                padding-top:
                    25px !important;

                padding-bottom:
                    25px !important;

                padding-left:
                    18px !important;

                padding-right:
                    18px !important;
            }}

            .st-key-login_container {{

                width:
                    100% !important;

                max-width:
                    600px !important;

                padding:
                    30px !important;

                border-radius:
                    24px !important;
            }}

            .login-logo {{

                width:
                    120px;

                height:
                    120px;
            }}

            .login-logo img {{

                width:
                    110px;

                height:
                    110px;
            }}

            .welcome-title {{

                font-size:
                    29px;
            }}

            .welcome-subtitle {{

                font-size:
                    14px;
            }}
        }}


        /* =================================================
           MOBILE
           ================================================= */

        @media (max-width: 480px) {{

            .block-container {{

                width:
                    100% !important;

                max-width:
                    100% !important;

                padding-top:
                    15px !important;

                padding-bottom:
                    15px !important;

                padding-left:
                    10px !important;

                padding-right:
                    10px !important;
            }}


            .st-key-login_container {{

                width:
                    100% !important;

                max-width:
                    100% !important;

                padding:
                    22px !important;

                border-radius:
                    20px !important;

                border-width:
                    1.5px !important;
            }}


            .login-logo {{

                width:
                    95px;

                height:
                    95px;

                margin-bottom:
                    15px;

                border-width:
                    3px;
            }}


            .login-logo img {{

                width:
                    87px;

                height:
                    87px;
            }}


            .welcome-title {{

                font-size:
                    24px;

                line-height:
                    1.2;
            }}


            .welcome-subtitle {{

                font-size:
                    12px;

                margin-bottom:
                    22px;
            }}


            .st-key-login_container
            div[data-testid="stTextInput"] label {{

                font-size:
                    12px !important;
            }}


            .st-key-login_container
            div[data-testid="stTextInput"] input {{

                height:
                    45px !important;

                min-height:
                    45px !important;

                font-size:
                    13px !important;

                border-radius:
                    11px !important;
            }}


            .st-key-login_container
            div.stButton > button {{

                min-height:
                    46px !important;

                font-size:
                    14px !important;

                border-radius:
                    12px !important;
            }}


            .public-mode {{

                margin-top:
                    20px;

                padding:
                    15px;

                border-radius:
                    14px;
            }}


            .public-title {{

                font-size:
                    14px;
            }}


            .public-text {{

                font-size:
                    11px;
            }}


            .st-key-login_container
            div.stButton:last-child > button {{

                min-height:
                    40px !important;

                font-size:
                    11px !important;
            }}
        }}


        /* =================================================
           VERY SMALL PHONES
           ================================================= */

        @media (max-width: 360px) {{

            .block-container {{

                padding-left:
                    7px !important;

                padding-right:
                    7px !important;
            }}


            .st-key-login_container {{

                padding:
                    17px !important;

                border-radius:
                    17px !important;
            }}


            .login-logo {{

                width:
                    80px;

                height:
                    80px;
            }}


            .login-logo img {{

                width:
                    74px;

                height:
                    74px;
            }}


            .welcome-title {{

                font-size:
                    21px;
            }}


            .welcome-subtitle {{

                font-size:
                    11px;
            }}


            .st-key-login_container
            div[data-testid="stTextInput"] input {{

                height:
                    42px !important;

                min-height:
                    42px !important;

                font-size:
                    12px !important;
            }}


            .st-key-login_container
            div.stButton > button {{

                min-height:
                    43px !important;

                font-size:
                    13px !important;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True
    )


    # ======================================================
    # PHARMACY LOGO
    # ======================================================

    logo_path = os.path.join(
        "assets",
        "pharmacy_logo.png"
    )


    if os.path.exists(logo_path):

        with open(
            logo_path,
            "rb"
        ) as logo_file:

            logo_encoded = base64.b64encode(
                logo_file.read()
            ).decode()

        logo_html = f"""
        <img
            src="data:image/png;base64,{logo_encoded}"
            alt="Pharmacy Logo"
        >
        """

    else:

        logo_html = "💊"


    # ======================================================
    # LOGIN CARD
    # ======================================================

    with st.container(
        key="login_container"
    ):

        # ==================================================
        # LOGO
        # ==================================================

        st.html(
            f"""
            <div class="login-logo">
                {logo_html}
            </div>
            """
        )


        # ==================================================
        # WELCOME MESSAGE
        # ==================================================

        st.html(
            """
            <div class="welcome-title">
                Welcome Back!
            </div>

            <div class="welcome-subtitle">
                Login to access your pharmacy system
            </div>
            """
        )


        # ==================================================
        # USERNAME
        # ==================================================

        username = st.text_input(
            "Username",
            placeholder="Enter Your Username"
        )


        # ==================================================
        # PASSWORD
        # ==================================================

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter Your Password"
        )


        # ==================================================
        # LOGIN BUTTON
        # ==================================================

        login_btn = st.button(
            "Log In",
            use_container_width=True
        )


        # ==================================================
        # LOGIN VALIDATION
        # ==================================================

        if login_btn:

            if not username.strip():

                st.error(
                    "Please enter your username."
                )

            elif not password:

                st.error(
                    "Please enter your password."
                )

            else:

                hashed_password = hash_password(
                    password
                )

                conn = get_db_connection()

                user = conn.execute(
                    """
                    SELECT *
                    FROM users
                    WHERE username = ?
                    AND password = ?
                    """,
                    (
                        username.strip(),
                        hashed_password
                    )
                ).fetchone()

                conn.close()


                if user:

                    st.session_state.logged_in = True

                    st.session_state.user_info = dict(
                        user
                    )


                    # ==================================
                    # AUDIT LOGIN
                    # ==================================

                    log_audit(
                        user["id"],
                        user["username"],
                        "User Login",
                        f"Role: {user['role']}"
                    )


                    st.success(
                        f"Welcome, {user['full_name']}!"
                    )

                    st.rerun()


                else:

                    st.error(
                        "Invalid Username or Password."
                    )


        # ==================================================
        # PUBLIC MODE
        # ==================================================

        st.html(
            """
            <div class="public-mode">

                <div class="public-title">
                    💡 Public Mode Available
                </div>

                <div class="public-text">
                    Launch the AI Chatbot Tablet-based.
                </div>

            </div>
            """
        )


        # ==================================================
        # CUSTOMER AI CHATBOT
        # ==================================================

        if st.button(
            "🤖 Launch Customer AI Chatbot Tablet-based",
            use_container_width=True
        ):

            st.session_state.logged_in = True

            st.session_state.user_info = {

                "id": 0,

                "username": "guest",

                "role": "guest",

                "full_name":
                    "Customer AI Chatbot Tablet-based"
            }

            st.session_state.page = "AI Chatbot"

            st.rerun()


# ==========================================================
# LOGOUT
# ==========================================================

def logout():

    user = st.session_state.get(
        "user_info"
    )


    # ======================================================
    # DO NOT AUDIT GUEST LOGOUT
    # ======================================================

    if user and user.get("role") != "guest":

        log_audit(
            user["id"],
            user["username"],
            "User Logout"
        )


    # ======================================================
    # CLEAR SESSION
    # ======================================================

    st.session_state.logged_in = False

    st.session_state.user_info = None

    st.session_state.page = "Dashboard"

    st.rerun()

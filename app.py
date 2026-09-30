import streamlit as st

from database import init_db
from auth import login_page, logout

from modules.dashboard import render as dashboard
from modules.users import render as user_management
from modules.medicine import render as medicine_information
from modules.inventory import render as inventory_management
from modules.expiry import render as expiry_tracking
from modules.suppliers import render as supplier_management
from modules.chatbot import render as ai_chatbot
from modules.inquiries import render as customer_inquiries
from modules.alerts import render as notifications_alerts
from modules.reports import render as reports_analytics
from modules.audit import render as audit_trail

# ORDER REQUESTS
from modules.order_requests import render as order_requests


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Tinay's Pharmacy",
    page_icon="💊",
    layout="wide"
)


# ==========================================
# PINK PHARMACY THEME
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #FFF5F8;
}


/* ==========================================
   SIDEBAR
   ========================================== */

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #F8BBD0 0%,
        #FCE4EC 50%,
        #FFF5F8 100%
    );

    border-right: 2px solid #F48FB1;
}


section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #AD1457;
}


section[data-testid="stSidebar"] p {
    color: #880E4F;
}


/* ==========================================
   NAVIGATION
   ========================================== */

section[data-testid="stSidebar"]
div[role="radiogroup"]
label {

    background-color: rgba(
        255,
        255,
        255,
        0.65
    );

    border-radius: 10px;

    padding: 10px 12px;

    margin-bottom: 6px;

    transition: 0.2s;
}


section[data-testid="stSidebar"]
div[role="radiogroup"]
label:hover {

    background-color: #F8BBD0;
}


/* ==========================================
   BUTTONS
   ========================================== */

.stButton > button {

    background-color: #E91E63;

    color: white;

    border: none;

    border-radius: 10px;

    padding: 8px 18px;

    font-weight: 600;

    transition: 0.2s;
}


.stButton > button:hover {

    background-color: #C2185B;

    color: white;

    border: none;
}


/* ==========================================
   HEADERS
   ========================================== */

h1 {
    color: #AD1457;
    font-weight: 700;
}

h2 {
    color: #C2185B;
}

h3 {
    color: #D81B60;
}


/* ==========================================
   METRIC CARDS
   ========================================== */

div[data-testid="stMetric"] {

    background-color: white;

    border: 1px solid #F8BBD0;

    border-left: 5px solid #E91E63;

    border-radius: 12px;

    padding: 15px;

    box-shadow:
        0px 3px 10px
        rgba(233, 30, 99, 0.12);
}


/* ==========================================
   INPUT BOXES
   ========================================== */

.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"],
.stMultiSelect div[data-baseweb="select"] {

    border-radius: 8px;
}


.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus {

    border-color: #E91E63;
}


/* ==========================================
   TABS
   ========================================== */

button[data-baseweb="tab"] {

    color: #AD1457;

    font-weight: 600;
}


button[data-baseweb="tab"][aria-selected="true"] {

    color: #E91E63;
}


/* ==========================================
   DATAFRAMES / TABLES
   ========================================== */

div[data-testid="stDataFrame"] {

    border: 1px solid #F8BBD0;

    border-radius: 10px;
}


/* ==========================================
   ALERTS
   ========================================== */

div[data-testid="stAlert"] {

    border-radius: 10px;
}


/* ==========================================
   DIVIDERS
   ========================================== */

hr {

    border-color: #F8BBD0;
}


/* ==========================================
   EXPANDERS
   ========================================== */

.streamlit-expanderHeader {

    background-color: #FCE4EC;

    color: #AD1457;

    border-radius: 10px;
}


/* ==========================================
   LOGIN / CARD STYLE
   ========================================== */

.pharmacy-card {

    background-color: white;

    border-radius: 18px;

    padding: 30px;

    border: 1px solid #F8BBD0;

    box-shadow:
        0px 5px 20px
        rgba(233, 30, 99, 0.15);
}


/* ==========================================
   CUSTOM PINK TITLE
   ========================================== */

.pink-title {

    color: #E91E63;

    font-size: 32px;

    font-weight: 700;
}


/* ==========================================
   CUSTOM KIOSK CARD
   ========================================== */

.kiosk-card {

    background: linear-gradient(
        135deg,
        #FCE4EC,
        #FFFFFF
    );

    border: 2px solid #F48FB1;

    border-radius: 20px;

    padding: 25px;

    box-shadow:
        0px 5px 15px
        rgba(233, 30, 99, 0.12);
}


/* ==========================================
   ORDER REQUEST SIDEBAR ITEM
   ========================================== */

.order-request-menu {

    background-color: #FCE4EC;

    border-left: 5px solid #E91E63;

    border-radius: 10px;

    padding: 10px;
}


/* ==========================================
   SCROLLBAR
   ========================================== */

::-webkit-scrollbar {

    width: 8px;
}


::-webkit-scrollbar-track {

    background: #FFF5F8;
}


::-webkit-scrollbar-thumb {

    background: #F48FB1;

    border-radius: 10px;
}


::-webkit-scrollbar-thumb:hover {

    background: #E91E63;
}


/* ==========================================================
   FULL-SCREEN PHONE/TABLET LANDSCAPE
   Applies to the AI Chatbot page when the device is rotated.
   The browser/Streamlit page itself stays fixed; only the
   Chat and My Cart panels may scroll internally if needed.
   ========================================================== */
@media screen and (orientation: landscape) and (max-width: 900px) {

    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main {
        width: 100% !important;
        max-width: 100% !important;
        height: 100dvh !important;
        min-height: 100dvh !important;
        overflow: hidden !important;
    }

    /* Remove the Streamlit top bar/extra vertical space */
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
    }

    div[data-testid="stToolbar"] {
        display: none !important;
    }

    div[data-testid="stDecoration"] {
        display: none !important;
    }

    /* Only lock the page when the chatbot workspace exists */
    [data-testid="stAppViewContainer"]:has(.st-key-chat_area) .main {
        height: 100dvh !important;
        min-height: 100dvh !important;
        overflow: hidden !important;
    }

    [data-testid="stAppViewContainer"]:has(.st-key-chat_area)
    .main .block-container {
        width: 100% !important;
        max-width: 100% !important;
        height: 100dvh !important;
        min-height: 100dvh !important;
        padding: 4px 6px 4px !important;
        margin: 0 !important;
        overflow: hidden !important;
    }

    /* Chat + My Cart columns */
    [data-testid="stHorizontalBlock"]:has(.st-key-chat_area) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        width: 100% !important;
        height: calc(100dvh - 8px) !important;
        min-height: 0 !important;
        max-height: calc(100dvh - 8px) !important;
        gap: 7px !important;
        overflow: hidden !important;
    }

    [data-testid="stHorizontalBlock"]:has(.st-key-chat_area)
    > [data-testid="stColumn"] {
        min-width: 0 !important;
        min-height: 0 !important;
        height: 100% !important;
        max-height: 100% !important;
        overflow: hidden !important;
    }

    [data-testid="stHorizontalBlock"]:has(.st-key-chat_area)
    > [data-testid="stColumn"]:first-child {
        flex: 1.55 1 0 !important;
        width: auto !important;
        max-width: none !important;
    }

    [data-testid="stHorizontalBlock"]:has(.st-key-chat_area)
    > [data-testid="stColumn"]:last-child {
        flex: 1 1 0 !important;
        width: auto !important;
        max-width: none !important;
    }

    /* Remove Streamlit vertical gaps around the two panels */
    [data-testid="stHorizontalBlock"]:has(.st-key-chat_area)
    > [data-testid="stColumn"] > div {
        height: 100% !important;
        min-height: 0 !important;
    }

    /* Chat panel */
    .st-key-chat_area {
        width: 100% !important;
        height: calc(100dvh - 16px) !important;
        max-height: calc(100dvh - 16px) !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 4px 5px 5px !important;
        border-radius: 12px !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        box-sizing: border-box !important;
    }

    /* Cart panel */
    .st-key-cart_area {
        width: 100% !important;
        height: calc(100dvh - 16px) !important;
        max-height: calc(100dvh - 16px) !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 6px !important;
        border-radius: 12px !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        box-sizing: border-box !important;
    }

    /* Keep chat input compact */
    .st-key-chat_input_bar {
        width: 100% !important;
        max-width: 100% !important;
        margin: 2px 0 0 !important;
        padding: 0 !important;
    }

    .st-key-chat_input_bar input {
        min-height: 34px !important;
        height: 34px !important;
        font-size: 12px !important;
    }

    .st-key-chat_input_bar button,
    .st-key-chat_input_bar .stButton > button {
        min-width: 34px !important;
        width: 34px !important;
        min-height: 34px !important;
        height: 34px !important;
        padding: 0 !important;
    }

    /* Compact chatbot content */
    .chatgpt-welcome {
        min-height: 0 !important;
        padding: 8px 7px 6px !important;
    }

    .welcome-row {
        gap: 7px !important;
    }

    .chatbot-avatar-large {
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        font-size: 18px !important;
    }

    .chatgpt-welcome-title {
        font-size: 16px !important;
        line-height: 1.1 !important;
    }

    .chatgpt-welcome-subtitle {
        font-size: 10px !important;
        line-height: 1.2 !important;
    }

    .language-note {
        margin-top: 5px !important;
        font-size: 9px !important;
    }

    div[data-testid="stChatMessage"] {
        padding: 3px 4px !important;
        margin-bottom: 1px !important;
    }

    div[data-testid="stChatMessage"] p {
        font-size: 11px !important;
        line-height: 1.25 !important;
        margin-bottom: 1px !important;
    }

    /* Compact cart */
    .st-key-cart_area .cart-item {
        padding: 5px !important;
        margin: 4px 1px !important;
    }

    .st-key-cart_area .cart-item-name {
        font-size: 11px !important;
    }

    .st-key-cart_area .cart-item-generic,
    .st-key-cart_area .cart-item-details {
        font-size: 9px !important;
    }

    .st-key-cart_area .stButton > button,
    .st-key-cart_area input,
    .st-key-cart_area [data-baseweb="select"] {
        min-height: 32px !important;
    }

    .st-key-cart_items_area {
        max-height: none !important;
        height: auto !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }

    /* Prevent wide cards/text from creating horizontal page scrolling */
    .st-key-chat_area *,
    .st-key-cart_area * {
        max-width: 100%;
        box-sizing: border-box;
        overflow-wrap: anywhere;
        word-break: break-word;
    }
}

/* Very short landscape phones */
@media screen and (orientation: landscape) and (max-height: 430px) and (max-width: 900px) {

    [data-testid="stAppViewContainer"]:has(.st-key-chat_area)
    .main .block-container {
        padding: 2px 4px 2px !important;
    }

    [data-testid="stHorizontalBlock"]:has(.st-key-chat_area) {
        height: calc(100dvh - 4px) !important;
        max-height: calc(100dvh - 4px) !important;
        gap: 5px !important;
    }

    .st-key-chat_area,
    .st-key-cart_area {
        height: calc(100dvh - 8px) !important;
        max-height: calc(100dvh - 8px) !important;
        padding: 3px 4px !important;
    }

    .chatgpt-welcome {
        padding: 5px !important;
    }

    .chatbot-avatar-large {
        width: 32px !important;
        height: 32px !important;
        min-width: 32px !important;
        font-size: 15px !important;
    }

    .chatgpt-welcome-title {
        font-size: 14px !important;
    }

    .chatgpt-welcome-subtitle {
        font-size: 9px !important;
    }

    div[data-testid="stChatMessage"] p {
        font-size: 10px !important;
    }
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# INITIALIZE DATABASE
# ==========================================

init_db()


# ==========================================
# SESSION STATE
# ==========================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if "user_info" not in st.session_state:

    st.session_state.user_info = None


# ==========================================
# LOGIN
# ==========================================

if not st.session_state.logged_in:

    login_page()


# ==========================================
# LOGGED-IN SYSTEM
# ==========================================

else:

    user = st.session_state.user_info

    role = user["role"]


    # ==========================================
    # SIDEBAR
    # ==========================================

    st.sidebar.title(
        "Tinay's Pharmacy"
    )


    st.sidebar.write(
        f"**User:** {user['full_name']}"
    )


    st.sidebar.write(
        f"**Role:** {role}"
    )


    # ==========================================
    # LOGOUT
    # ==========================================

    if st.sidebar.button(
        "🚪 Logout"
    ):

        logout()


    st.sidebar.markdown(
        "---"
    )


    # ==========================================
    # ADMINISTRATOR
    # ==========================================

    if role == "Administrator":

        menu = [

            "Dashboard",

            "User Management",

            "Medicine Information",

            "Inventory Management",

            "Batch & Expiration Tracking",

            "Supplier Management",

            "Notifications & Alerts",

            "Reports & Analytics",

            "Customer Inquiries",

            "Order Requests",

            "Audit Trail",

        ]


    # ==========================================
    # PHARMACIST
    # ==========================================

    elif role == "Pharmacist":

        menu = [

            "Dashboard",

            "Medicine Information",

            "Inventory Management",

            "Batch & Expiration Tracking",

            "Supplier Management",

            "Notifications & Alerts",

            "Reports & Analytics",

            "Customer Inquiries",

            "Order Requests",

        ]


    # ==========================================
    # STAFF
    # SAME ACCESS AS PHARMACIST
    # ==========================================

    elif role == "Staff":

        menu = [

            "Dashboard",

            "Medicine Information",

            "Inventory Management",

            "Batch & Expiration Tracking",

            "Supplier Management",

            "Notifications & Alerts",

            "Reports & Analytics",

            "Customer Inquiries",

            "Order Requests",

        ]


    # ==========================================
    # TABLET-BASED CUSTOMER
    # ==========================================

    elif role == "Tablet-based":

        menu = [

            "AI Chatbot Tablet-based"

        ]


    # ==========================================
    # DEFAULT
    # ==========================================

    else:

        menu = [

            "AI Chatbot Tablet-based"

        ]


    # ==========================================
    # NAVIGATION
    # ==========================================

    choice = st.sidebar.radio(
        "",
        menu
    )


    # ==========================================
    # DASHBOARD
    # ==========================================

    if choice == "Dashboard":

        dashboard(user)


    # ==========================================
    # USER MANAGEMENT
    # ==========================================

    elif choice == "User Management":

        if role != "Administrator":

            st.error(
                "🚫 Access Denied. "
                "Only Administrators can "
                "access User Management."
            )

        else:

            user_management(user)


    # ==========================================
    # MEDICINE
    # ==========================================

    elif choice == "Medicine Information":

        medicine_information(user)


    # ==========================================
    # INVENTORY
    # ==========================================

    elif choice == "Inventory Management":

        inventory_management(user)


    # ==========================================
    # EXPIRATION
    # ==========================================

    elif choice == "Batch & Expiration Tracking":

        expiry_tracking(user)


    # ==========================================
    # SUPPLIERS
    # ==========================================

    elif choice == "Supplier Management":

        supplier_management(user)


    # ==========================================
    # ALERTS
    # ==========================================

    elif choice == "Notifications & Alerts":

        notifications_alerts(user)


    # ==========================================
    # REPORTS
    # ==========================================

    elif choice == "Reports & Analytics":

        reports_analytics(user)


    # ==========================================
    # CUSTOMER INQUIRIES
    # ==========================================

    elif choice == "Customer Inquiries":

        customer_inquiries(user)


    # ==========================================
    # ORDER REQUESTS
    # ADMINISTRATOR + PHARMACIST + STAFF
    # ==========================================

    elif choice == "Order Requests":

        if role not in [
            "Administrator",
            "Pharmacist",
            "Staff"
        ]:

            st.error(
                "🚫 Access Denied. "
                "Only Administrators, Pharmacists, "
                "and Staff can access "
                "Order Requests."
            )

        else:

            order_requests(user)


    # ==========================================
    # AUDIT TRAIL
    # ==========================================

    elif choice == "Audit Trail":

        if role != "Administrator":

            st.error(
                "🚫 Access Denied. "
                "Only Administrators can "
                "access the Audit Trail."
            )

        else:

            audit_trail(user)


    # ==========================================
    # AI CHATBOT TABLET
    # ==========================================

    elif choice == "AI Chatbot Tablet-based":

        ai_chatbot(user)
import streamlit as st


ROLE_PERMISSIONS = {

    "Administrator": [
        "dashboard",
        "medicines",
        "inventory",
        "stock_in",
        "stock_out",
        "expiry_alerts",
        "suppliers",
        "reports",
        "inquiries",
        "users",
        "settings"
    ],

    "Pharmacist": [
        "dashboard",
        "medicines",
        "inventory",
        "stock_in",
        "stock_out",
        "expiry_alerts",
        "suppliers",
        "reports",
        "inquiries"
    ],

    "Staff": [
        "dashboard",
        "inventory",
        "stock_in",
        "stock_out",
        "expiry_alerts",
        "inquiries"
    ],

    "Customer": [
        "chatbot",
        "customer_orders",
        "medicine_availability",
        "inquiries"
    ]
}


def has_permission(user, permission):

    if not user:
        return False

    role = user.get("role")

    return permission in ROLE_PERMISSIONS.get(role, [])


def require_permission(user, permission):

    if not has_permission(user, permission):

        st.error(
            "🚫 Access Denied. "
            "You do not have permission to access this page."
        )

        st.stop()
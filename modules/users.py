import sqlite3
import pandas as pd
import streamlit as st

from database import (
    get_db_connection,
    hash_password,
    log_audit
)


def render(user):

    # ==========================================
    # SECURITY CHECK
    # ==========================================

    if user["role"] != "Administrator":

        st.error(
            "🚫 Access Denied."
        )

        st.stop()


    # ==========================================
    # PAGE TITLE
    # ==========================================

    st.header(
        "👥 User Management"
    )


    # ==========================================
    # TABLE / REGISTER TABS
    # ==========================================

    tab1, tab2 = st.tabs([
        "Users",
        "Register User"
    ])


    conn = get_db_connection()


    # ==========================================
    # USERS TAB
    # ==========================================

    with tab1:

        st.subheader(
            "Registered Users"
        )


        # ======================================
        # GET USERS
        # ======================================

        df = pd.read_sql_query(
            """
            SELECT
                id,
                username,
                role,
                full_name,
                created_at
            FROM users
            ORDER BY id
            """,
            conn
        )


        # ======================================
        # TABLE CSS
        # ======================================

        st.markdown(
            """
            <style>

            .user-table-header {
                font-weight: 700;
                color: #172033;
                font-size: 14px;
                padding-bottom: 8px;
            }

            .user-table-cell {
                color: #172033;
                font-size: 14px;
                display: flex;
                align-items: center;
                min-height: 40px;
                word-break: break-word;
            }

            .user-table-row {
                border-bottom: 1px solid #eadde3;
                margin-top: 8px;
                margin-bottom: 8px;
            }

            div[data-testid="stButton"] button {
                border-radius: 8px !important;
                min-height: 38px !important;
                height: 38px !important;
                padding: 0 10px !important;
                font-size: 15px !important;
            }

            button[kind="secondary"] {
                border: 1px solid #d8d8d8 !important;
            }

            </style>
            """,
            unsafe_allow_html=True
        )


        # ======================================
        # EMPTY TABLE
        # ======================================

        if df.empty:

            st.info(
                "No registered users."
            )

        else:

            # ==================================
            # COLUMN WIDTHS
            # ID IS NOT DISPLAYED
            # ==================================

            col_widths = [
                1.6,   # Username
                2.0,   # Role
                2.5,   # Full Name
                2.2,   # Created At
                1.2    # Action
            ]


            # ==================================
            # TABLE HEADER
            # ==================================

            header = st.columns(
                col_widths,
                gap="small"
            )


            # ==================================
            # USERNAME HEADER
            # ==================================

            header[0].markdown(
                """
                <div class="user-table-header">
                    Username
                </div>
                """,
                unsafe_allow_html=True
            )


            # ==================================
            # ROLE HEADER
            # ==================================

            header[1].markdown(
                """
                <div class="user-table-header">
                    Role
                </div>
                """,
                unsafe_allow_html=True
            )


            # ==================================
            # FULL NAME HEADER
            # ==================================

            header[2].markdown(
                """
                <div class="user-table-header">
                    Full Name
                </div>
                """,
                unsafe_allow_html=True
            )


            # ==================================
            # CREATED AT HEADER
            # ==================================

            header[3].markdown(
                """
                <div class="user-table-header">
                    Created At
                </div>
                """,
                unsafe_allow_html=True
            )


            # ==================================
            # ACTION HEADER
            # ==================================

            header[4].markdown(
                """
                <div class="user-table-header">
                    Action
                </div>
                """,
                unsafe_allow_html=True
            )


            st.divider()


            # ==================================
            # USER ROWS
            # ==================================

            for _, row in df.iterrows():

                row_columns = st.columns(
                    col_widths,
                    gap="small"
                )


                # ==================================
                # USERNAME
                # ==================================

                with row_columns[0]:

                    st.markdown(
                        f"""
                        <div class="user-table-cell">
                            {row["username"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                # ==================================
                # ROLE
                # ==================================

                with row_columns[1]:

                    # --------------------------------
                    # ADMINISTRATOR
                    # --------------------------------

                    if row["role"] == "Administrator":

                        role_html = """
                        <span style="
                            background:#FCE4EC;
                            color:#AD1457;
                            padding:5px 10px;
                            border-radius:10px;
                            font-weight:600;
                        ">
                            Administrator
                        </span>
                        """


                    # --------------------------------
                    # PHARMACIST
                    # --------------------------------

                    elif row["role"] == "Pharmacist":

                        role_html = """
                        <span style="
                            background:#E3F2FD;
                            color:#1565C0;
                            padding:5px 10px;
                            border-radius:10px;
                            font-weight:600;
                        ">
                            Pharmacist
                        </span>
                        """


                    # --------------------------------
                    # STAFF
                    # --------------------------------

                    elif row["role"] == "Staff":

                        role_html = """
                        <span style="
                            background:#FFF3E0;
                            color:#E65100;
                            padding:5px 10px;
                            border-radius:10px;
                            font-weight:600;
                        ">
                            Staff
                        </span>
                        """


                    # --------------------------------
                    # OTHER ROLE
                    # --------------------------------

                    else:

                        role_html = f"""
                        <span style="
                            padding:5px 10px;
                            border-radius:10px;
                            font-weight:600;
                        ">
                            {row["role"]}
                        </span>
                        """


                    st.markdown(
                        role_html,
                        unsafe_allow_html=True
                    )


                # ==================================
                # FULL NAME
                # ==================================

                with row_columns[2]:

                    st.markdown(
                        f"""
                        <div class="user-table-cell">
                            {row["full_name"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                # ==================================
                # CREATED AT
                # ==================================

                with row_columns[3]:

                    st.markdown(
                        f"""
                        <div class="user-table-cell">
                            {row["created_at"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                # ==================================
                # ACTION
                # ==================================

                with row_columns[4]:

                    action_col1, action_col2 = st.columns(
                        [1, 1],
                        gap="small"
                    )


                    # ==================================
                    # EDIT USER
                    # ==================================

                    with action_col1:

                        if st.button(
                            "✏️",
                            key=f"edit_{row['id']}",
                            help="Edit User Role"
                        ):

                            st.session_state[
                                "edit_user_id"
                            ] = row["id"]


                            st.session_state.pop(
                                "delete_user_id",
                                None
                            )


                            st.session_state.pop(
                                "delete_confirmation",
                                None
                            )


                            st.rerun()


                    # ==================================
                    # REMOVE USER
                    # ==================================

                    with action_col2:

                        # Do not allow administrator
                        # to delete own account

                        if row["id"] != user["id"]:

                            if st.button(
                                "🗑️",
                                key=f"delete_{row['id']}",
                                help="Remove User"
                            ):

                                st.session_state[
                                    "delete_user_id"
                                ] = row["id"]


                                st.session_state.pop(
                                    "edit_user_id",
                                    None
                                )


                                st.session_state.pop(
                                    "delete_confirmation",
                                    None
                                )


                                st.rerun()

                        else:

                            st.markdown(
                                """
                                <div
                                    style="
                                        height:38px;
                                        display:flex;
                                        align-items:center;
                                        justify-content:center;
                                        color:#999;
                                    "
                                >
                                    —
                                </div>
                                """,
                                unsafe_allow_html=True
                            )


                st.markdown(
                    """
                    <div class="user-table-row"></div>
                    """,
                    unsafe_allow_html=True
                )


        # ==========================================
        # EDIT USER ROLE
        # ==========================================

        if "edit_user_id" in st.session_state:

            edit_user_id = st.session_state[
                "edit_user_id"
            ]


            edit_user = df[
                df["id"] == edit_user_id
            ]


            if not edit_user.empty:

                edit_user = edit_user.iloc[0]


                st.markdown("---")


                st.subheader(
                    "✏️ Edit User Role"
                )


                st.info(
                    f"Editing: "
                    f"{edit_user['username']} — "
                    f"{edit_user['full_name']}"
                )


                # ==================================
                # AVAILABLE ROLES
                # ==================================

                roles = [
                    "Administrator",
                    "Pharmacist",
                    "Staff"
                ]


                current_role = edit_user["role"]


                # ==================================
                # HANDLE OLD COMBINED ROLE
                # ==================================

                if current_role in roles:

                    role_index = roles.index(
                        current_role
                    )

                else:

                    role_index = 0


                new_role = st.selectbox(
                    "New Role",
                    roles,
                    index=role_index,
                    key="edit_role_select"
                )


                edit_col1, edit_col2 = st.columns(
                    2
                )


                # ==================================
                # SAVE ROLE
                # ==================================

                with edit_col1:

                    if st.button(
                        "💾 Save Changes",
                        use_container_width=True
                    ):

                        if (
                            new_role == edit_user["role"]
                        ):

                            st.warning(
                                "The selected role is "
                                "already assigned."
                            )

                        else:

                            try:

                                conn.execute(
                                    """
                                    UPDATE users
                                    SET role = ?
                                    WHERE id = ?
                                    """,
                                    (
                                        new_role,
                                        edit_user_id
                                    )
                                )


                                conn.commit()


                                # ==========================
                                # AUDIT LOG
                                # ==========================

                                log_audit(
                                    user["id"],
                                    user["username"],
                                    "Changed User Role",
                                    f"{edit_user['username']}: "
                                    f"{edit_user['role']} → "
                                    f"{new_role}"
                                )


                                # ==========================
                                # CLEAR EDIT STATE
                                # ==========================

                                del st.session_state[
                                    "edit_user_id"
                                ]


                                st.success(
                                    "User role updated "
                                    "successfully!"
                                )


                                st.rerun()


                            except sqlite3.Error as e:

                                conn.rollback()


                                st.error(
                                    f"Error updating role: {e}"
                                )


                # ==================================
                # CANCEL EDIT
                # ==================================

                with edit_col2:

                    if st.button(
                        "❌ Cancel",
                        use_container_width=True
                    ):

                        del st.session_state[
                            "edit_user_id"
                        ]


                        st.rerun()


        # ==========================================
        # DELETE USER CONFIRMATION
        # ==========================================

        if "delete_user_id" in st.session_state:

            delete_user_id = st.session_state[
                "delete_user_id"
            ]


            # ======================================
            # SECURITY CHECK
            # ======================================

            if delete_user_id == user["id"]:

                del st.session_state[
                    "delete_user_id"
                ]


                st.error(
                    "🚫 You cannot remove "
                    "your own account."
                )

            else:

                delete_user = df[
                    df["id"] == delete_user_id
                ]


                if not delete_user.empty:

                    delete_user = delete_user.iloc[0]


                    st.markdown("---")


                    st.subheader(
                        "🗑️ Remove User"
                    )


                    st.warning(
                        f"Are you sure you want to remove "
                        f"**{delete_user['username']}** "
                        f"({delete_user['full_name']})?"
                    )


                    st.write(
                        f"**Username:** "
                        f"{delete_user['username']}"
                    )


                    st.write(
                        f"**Full Name:** "
                        f"{delete_user['full_name']}"
                    )


                    st.write(
                        f"**Role:** "
                        f"{delete_user['role']}"
                    )


                    # ==================================
                    # CONFIRMATION
                    # ==================================

                    confirm = st.checkbox(
                        "I confirm that I want to permanently remove this user.",
                        key="delete_confirmation"
                    )


                    delete_col1, delete_col2 = st.columns(
                        2
                    )


                    # ==================================
                    # CONFIRM REMOVE
                    # ==================================

                    with delete_col1:

                        if st.button(
                            "🗑️ Confirm Remove",
                            use_container_width=True,
                            type="primary"
                        ):

                            if not confirm:

                                st.warning(
                                    "Please confirm the "
                                    "deletion first."
                                )

                            else:

                                try:

                                    username_removed = (
                                        delete_user["username"]
                                    )


                                    full_name_removed = (
                                        delete_user["full_name"]
                                    )


                                    role_removed = (
                                        delete_user["role"]
                                    )


                                    # ==========================
                                    # DELETE USER
                                    # ==========================

                                    cursor = conn.execute(
                                        """
                                        DELETE FROM users
                                        WHERE id = ?
                                        """,
                                        (
                                            delete_user_id,
                                        )
                                    )


                                    # ==========================
                                    # CHECK DELETE
                                    # ==========================

                                    if cursor.rowcount == 0:

                                        conn.rollback()


                                        st.error(
                                            "User could not "
                                            "be removed."
                                        )

                                    else:

                                        conn.commit()


                                        # ======================
                                        # AUDIT LOG
                                        # ======================

                                        log_audit(
                                            user["id"],
                                            user["username"],
                                            "Removed User",
                                            f"Username: "
                                            f"{username_removed} | "
                                            f"Name: "
                                            f"{full_name_removed} | "
                                            f"Role: "
                                            f"{role_removed}"
                                        )


                                        # ======================
                                        # CLEAR SESSION
                                        # ======================

                                        st.session_state.pop(
                                            "delete_user_id",
                                            None
                                        )


                                        st.session_state.pop(
                                            "delete_confirmation",
                                            None
                                        )


                                        st.success(
                                            f"User "
                                            f"'{username_removed}' "
                                            f"was removed "
                                            f"successfully."
                                        )


                                        st.rerun()


                                except sqlite3.IntegrityError:

                                    conn.rollback()


                                    st.error(
                                        "This user cannot be "
                                        "removed because other "
                                        "records are linked to "
                                        "this account."
                                    )


                                except sqlite3.Error as e:

                                    conn.rollback()


                                    st.error(
                                        f"Error removing user: "
                                        f"{e}"
                                    )


                    # ==================================
                    # CANCEL DELETE
                    # ==================================

                    with delete_col2:

                        if st.button(
                            "❌ Cancel",
                            use_container_width=True
                        ):

                            st.session_state.pop(
                                "delete_user_id",
                                None
                            )


                            st.session_state.pop(
                                "delete_confirmation",
                                None
                            )


                            st.rerun()


                else:

                    # User no longer exists

                    st.session_state.pop(
                        "delete_user_id",
                        None
                    )


    # ==========================================
    # REGISTER USER TAB
    # ==========================================

    with tab2:

        st.subheader(
            "➕ Register New User"
        )


        st.info(
            "Administrators can create "
            "Administrator, Pharmacist, or Staff "
            "accounts."
        )


        # ======================================
        # REGISTRATION FORM
        # ======================================

        with st.form(
            "new_user"
        ):

            username = st.text_input(
                "Username",
                placeholder="Enter username"
            )


            full_name = st.text_input(
                "Full Name",
                placeholder="Enter full name"
            )


            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password"
            )


            role = st.selectbox(
                "Role",
                [
                    "Administrator",
                    "Pharmacist",
                    "Staff"
                ]
            )


            submit = st.form_submit_button(
                "➕ Register User",
                use_container_width=True
            )


            # ==================================
            # REGISTER USER
            # ==================================

            if submit:

                username = username.strip()

                full_name = full_name.strip()


                # ==================================
                # VALIDATION
                # ==================================

                if not username:

                    st.warning(
                        "Please enter a username."
                    )

                elif not full_name:

                    st.warning(
                        "Please enter the full name."
                    )

                elif not password:

                    st.warning(
                        "Please enter a password."
                    )

                else:

                    try:

                        # ==============================
                        # INSERT USER
                        # ==============================

                        conn.execute(
                            """
                            INSERT INTO users
                            (
                                username,
                                password,
                                role,
                                full_name
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                username,
                                hash_password(password),
                                role,
                                full_name
                            )
                        )


                        conn.commit()


                        # ==============================
                        # AUDIT LOG
                        # ==============================

                        log_audit(
                            user["id"],
                            user["username"],
                            "Created User",
                            f"Username: {username} | "
                            f"Full Name: {full_name} | "
                            f"Role: {role}"
                        )


                        st.success(
                            f"User '{username}' was "
                            f"registered successfully "
                            f"as {role}."
                        )


                        st.rerun()


                    except sqlite3.IntegrityError:

                        conn.rollback()


                        st.error(
                            "❌ Username already exists."
                        )


                    except sqlite3.Error as e:

                        conn.rollback()


                        st.error(
                            f"❌ Error registering user: "
                            f"{e}"
                        )


    # ==========================================
    # CLOSE DATABASE
    # ==========================================

    conn.close()
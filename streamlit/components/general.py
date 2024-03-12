import utils

import streamlit as st


def sidebar() -> None:
    """Sidebar component for all pages."""
    st.header(f"**Welkom, {st.session_state.name}**")
    st.divider()
    st.subheader("**Accountgegevens:**")
    st.markdown("**Organisatie:**")
    st.markdown(st.session_state.organisation_name)
    st.markdown("**BRO Credentials ingevuld:**")
    st.markdown(
        ":white_check_mark: Ja"
    ) if st.session_state.credentials_set else st.markdown(":exclamation: Nee")
    st.markdown("**Standaard project nummer:**")
    st.markdown(st.session_state.default_project_number)

    if st.button("Wijzig instellingen"):
        with st.form(key="setting-change-form"):
            st.text_input(
                label="Standaard project nummer:",
                value=st.session_state.default_project_number,
                key="change-default-project-number",
            )
            st.text_input(
                label="BRO User Token:", key="change-bro-user-token", type="password"
            )
            st.text_input(
                label="BRO User Password:",
                key="change-bro-user-password",
                type="password",
            )

            st.form_submit_button("Opslaan", on_click=utils.patch_user_profile)

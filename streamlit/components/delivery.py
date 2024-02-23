import streamlit as st

import config
import utils

def delivery() -> None:
    """Component for the Aanlevering page"""
    upload_data = {}

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Vul de aanlever gegevens in:")

        upload_data["bro_domain"] = st.selectbox("Selecteer een BRO domein om in aan te leveren:", options=config.CURRENT_SUPPORTED_BRO_DOMAINS, key="delivery_domain")
        
        upload_data["project_number"] = st.text_input(
                "Projectnummer:",
                value=st.session_state.default_project_number,
                key='import_task_kvk_number'
            )
        upload_data["registration_type"] = st.selectbox("Selecteer type bericht:", options=config.CURRENT_SUPPORTED_DELIVERIES[upload_data["bro_domain"]])
        upload_data["request_type"] = st.selectbox("Selecteer request type:", options=config.CURRENT_SUPPORTED_DELIVERIES[upload_data["bro_domain"]][upload_data["registration_type"]])

        st.subheader("Vul de metadata gegevens in:")

        metadata_fields = config.METADATA_FIELDS[f"{upload_data['request_type']}_{upload_data['registration_type']}"]
        upload_data["metadata"] = {}
        
        for field in metadata_fields:
            upload_data["metadata"][field] = st.text_input(field, key=f"metadata_{field}")
        
        st.subheader("Vul de sourcedocument gegevens in:")

        sourcedocument_fields = config.SOURCEDOCUMENT_FIELDS[f"{upload_data['request_type']}_{upload_data['registration_type']}"]
        upload_data['sourcedocument_data'] = {}
        for field in sourcedocument_fields:
            upload_data['sourcedocument_data'][field] = st.text_input(field, key=f"srcdocs+{field}")

    with col2:
        st.subheader("Controleer de gegevens:")
        st.json(upload_data)

    if st.button("Aanleveren"):
        utils.start_upload_task(upload_data)




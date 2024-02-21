
import streamlit as st
import authentication as auth


def main():
    
    if auth.authenticate():
        st.text("Lever hier data aan")
    

if __name__ == "__main__":
    main()

import streamlit as st
import authentication as auth


def main():
    
    if auth.authenticate():
        st.map()
    

if __name__ == "__main__":
    main()
import streamlit as st
import authentication as auth
import utils

def main():
    
    if auth.is_authenticated():
        utils.set_user_details()

    
if __name__ == "__main__":
    main()
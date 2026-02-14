import streamlit as st
import pandas as pd
import numpy as np
import time
import base64
import random
from groq import Groq

def hiring_dashboard():
    """
    Main function for the Hiring Manager Dashboard.
    Requires go_to_func for logout.
    """
    
    # --- Dashboard Header and Logout Button ---
    col_title, nav_col = st.columns([10, 2])
    
    with col_title:
        st.title("👨‍💼 Hiring Manager Dashboard")
        st.caption("Manage JDs, review top candidates, and track interviews.")
    
    with nav_col:
        # FIX: The logout logic must be placed inside the if st.button(...) block
        # rather than an on_click callback for immediate state changes and rerun() to work reliably.
        if st.button("🚪 Log Out", use_container_width=True):
            # 1. Clear authentication state
            st.session_state.logged_in = False
            st.session_state.user_type = None
            
            # 2. Set the target page using the passed function
            go_to_func("login")
            
            # 3. Force the application to re-run
            st.rerun()
            
    st.markdown("---") # Visual separator after the header/logout

if __name__ == "__main__":
    main()
     

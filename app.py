import streamlit as st
from src import helpers as h

title, contents = h.read_md_file("./README.md", extract_header=True)

st.title(title)
st.markdown(contents, unsafe_allow_html=True)
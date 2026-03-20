import streamlit as st
from src import helpers as h

header, contents = h.read_md_file("./docs/python.md", extract_header=True)

st.title(header)
st.markdown(contents, unsafe_allow_html=True)
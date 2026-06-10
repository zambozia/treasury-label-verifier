import streamlit as st

st.set_page_config(
    page_title="Alcohol Label Verification App",
    page_icon="🏷️",
    layout="wide"
)

st.title("Alcohol Label Verification App")
st.caption("Batch-first OCR-assisted label review prototype")

st.header("Step 1: Upload Application Records")
csv_file = st.file_uploader("Upload CSV file", type=["csv"])

st.header("Step 2: Upload Label Images")
image_files = st.file_uploader(
    "Upload PNG, JPG, or JPEG label images",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

st.header("Step 3: Verify Labels")

if st.button("Run Verification"):
    if csv_file is None:
        st.error("No CSV file was uploaded. Please upload an application records CSV first.")
    elif not image_files:
        st.error("No image files were uploaded. Please upload at least one label image.")
    else:
        st.success("Application shell is working. Next step: CSV validation and OCR.")
        st.write(f"CSV uploaded: {csv_file.name}")
        st.write(f"Images uploaded: {len(image_files)}")
import streamlit as st
import numpy as np
import pandas as pd
import io

st.set_page_config(page_title='Data Cleaning Application', page_icon='🧹', layout='wide')

st.title('🧹 Data Cleaning Application')
st.write('📁 Upload A **CSV** Or An **Excel** File')

# for uploading file
uploaded_file = st.file_uploader('Upload A CSV Or An Excel File', type=['CSV','xlsx'])

if uploaded_file is not None:
    try:
        data = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file, engine='openpyxl')
        bool_cols = data.select_dtypes(include=['bool']).columns
        data[bool_cols] = data[bool_cols].astype('str')
    except Exception as e:
        st.error('Could Not Read Excel / CSV File. Please Check The File Format.')
        st.exception(e)
        st.stop()

    st.success('✅ File Uploaded Successfully!')

# tabs
    tab1, tab2 = st.tabs(['📊 Summary', '🧹 Cleaning'])
    
    # TAB 1: SUMMARY 
    with tab1:          
        # Data Info
        st.write('### 📋 Data Summary')
        buffer = io.StringIO()
        data.info(buf=buffer)
        info_text = buffer.getvalue()
        st.text(info_text)      

        # Data Preview
        st.write('### 🔎 Data Preview')
        st.write('#### First 10 Rows')
        st.dataframe(data.head(10), use_container_width=True)  
            
    # TAB 2: DATA CLEANING
    with tab2:  
        # Initialize session state for data if not exists
        if 'data' not in st.session_state:
            st.session_state.data = data.copy()
        
        st.write('Cleaning Missing Values and Duplicates')
        
        # MISSING VALUES
        st.write('### ❓ Missing Values')

        # Calculate missing values using session state data
        missing_count = st.session_state.data.isnull().sum()
        missing_data = pd.DataFrame({
            'Column': missing_count.index,
            'Missing Count': missing_count.values,
            'Missing Percentage': (missing_count.values / len(st.session_state.data) * 100).round(2)
        })
        missing_data = missing_data[missing_data['Missing Count'] > 0]

        if len(missing_data) == 0:
            st.success('🎉 No missing values found!')
        else:
            st.dataframe(missing_data, use_container_width=True)
            
            # Check for columns with all missing values
            all_missing_cols = [col for col in st.session_state.data.columns 
                               if st.session_state.data[col].isnull().all()]
            
            if all_missing_cols:
                st.warning(f'⚠️ Warning: These columns have ALL missing values: {", ".join(all_missing_cols)}')
                st.info('💡 Tip: Consider removing these empty columns first before cleaning other missing values.')
                
                if st.button('🗑️ Remove empty columns', use_container_width=True):
                    st.session_state.data = st.session_state.data.drop(columns=all_missing_cols)
                    st.success(f'✅ Removed {len(all_missing_cols)} empty columns!')
                    st.rerun()
                
                st.write('---')
            
            st.write('')
            st.write('**What would you like to do?**')
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button('🗑️ Delete rows with missing values', use_container_width=True):
                    original_rows = len(st.session_state.data)
                    st.session_state.data = st.session_state.data.dropna()
                    removed = original_rows - len(st.session_state.data)
                    
                    if len(st.session_state.data) == 0:
                        st.error('❌ This would delete all rows! Please use "Fill missing values" instead or remove empty columns first.')
                        st.stop()
                    else:
                        st.success(f'✅ Deleted {removed} rows!')
                        st.rerun()
            
            with col2:
                if st.button('📝 Fill missing values as Unknown', use_container_width=True):
                    # Fill numbers with average, text with "Unknown"
                    numeric_cols = st.session_state.data.select_dtypes(include=[np.number]).columns
                    text_cols = st.session_state.data.select_dtypes(include=['object']).columns
                    
                    st.session_state.data[numeric_cols] = st.session_state.data[numeric_cols].fillna(
                        st.session_state.data[numeric_cols].mean()
                    )
                    st.session_state.data[text_cols] = st.session_state.data[text_cols].fillna('Unknown')
                    
                    st.success('✅ Filled all missing values!')
                    st.rerun()

        # DUPLICATE RECORDS
        st.write('### 🔄 Duplicate Records')
        duplicate_count = st.session_state.data.duplicated().sum()

        if duplicate_count == 0:
            st.success('🎉 No duplicate rows found!')
        else:
            st.warning(f'⚠️ Found {duplicate_count} duplicate rows')
            
            # Show duplicates
            st.write('Preview of duplicate rows:')
            duplicates = st.session_state.data[st.session_state.data.duplicated(keep=False)]
            st.dataframe(duplicates.head(10), use_container_width=True)
            
            # Remove duplicates
            st.write('#### Remove Duplicates')
            if st.button('🗑️ Remove Duplicate Rows'):
                st.session_state.data = st.session_state.data.drop_duplicates(keep='first')
                st.success(f'✅ Removed duplicates! New number of rows: {len(st.session_state.data)}')
                st.rerun()
    
        # Download cleaned data
        st.write('---')
        st.write('### 💾 Download Cleaned Data')
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Download as CSV - use session state data
            csv = st.session_state.data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label='📥 Download as CSV',
                data=csv,
                file_name='cleaned_data.csv',
                mime='text/csv',
                key='download_csv'
            )
        
        with col2:
            # Download as Excel - use session state data
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                st.session_state.data.to_excel(writer, index=False, sheet_name='Cleaned Data')
            
            st.download_button(
                label='📥 Download as Excel',
                data=buffer.getvalue(),
                file_name='cleaned_data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                key='download_excel'
            )
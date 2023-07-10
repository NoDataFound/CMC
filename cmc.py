import os
import shutil
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from PIL import Image
from git import Repo
from urllib.request import urlopen
from bs4 import BeautifulSoup

@st.cache_data()
def count_lines_of_code(repo_path, ext):
    total = 0
    for path, dirs, files in os.walk(repo_path):
        for name in files:
            if name.endswith(ext):  
                with open(os.path.join(path, name)) as f:
                    total += sum(1 for line in f if line.strip() != '')
    return total

def clone_and_count_lines(user, repo, ext):
    repo_url = f'https://github.com/{user}/{repo}'
    local_path = f'temp/{repo}'
    
    if os.path.isdir(local_path):
        shutil.rmtree(local_path)
        
    Repo.clone_from(repo_url, local_path)
    
    lines = count_lines_of_code(local_path, ext)
    
    shutil.rmtree(local_path)
    
    return lines

def update_progress_file(filename, repo_name):
    with open(filename, 'a') as f:
        f.write(repo_name + '\n')

def is_repo_processed(filename, repo_name):
    if not os.path.exists(filename):
        return False
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
    return repo_name in lines

def get_all_user_repos(user):
    response = requests.get(f'https://github.com/{user}?tab=repositories')
    repos = []
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        repo_elements = soup.find_all('a', itemprop='name codeRepository')
        repos = [repo.text.strip() for repo in repo_elements]
    return repos

def main():
    st.set_page_config(layout="wide")  # For wide layout
    logo_url = 'https://raw.githubusercontent.com/NoDataFound/CMC/main/githublogo.png'
    total_lines = 0
  
    lang_ext = {
        'Python': '.py',
        'Java': '.java',
        'JavaScript': '.js',
        'C': '.c',
        'C++': '.cpp',
        'C#': '.cs',
        'TypeScript': '.ts',
        'PHP': '.php',
        'Swift': '.swift',
        'Go': '.go'
    }

    df = pd.DataFrame(columns=['User', 'Repo', 'Lines of Code', 'Language'])

    with st.sidebar:
        st.image(logo_url, width=200)
        st.title('Lines of Code Counter')
        user = st.text_input('Enter GitHub Username')
        language = st.selectbox('Select Language', list(lang_ext.keys())) 

    if user and language:
        st.sidebar.code(f'Fetching repositories for {user}...')
        repos = get_all_user_repos(user)
        #st.sidebar.code(f'Found {len(repos)} repositories for {user}.')
        data = []
        progress_bar = st.progress(0)
        progress_filename = f"{user}_progress.txt"
        processing_message = st.empty()
        total_lines_metric = st.empty()
        for i, repo in enumerate(repos):
            if not is_repo_processed(progress_filename, repo):  
                processing_message.code(f'Processing {repo}...')
                lines = clone_and_count_lines(user, repo, lang_ext[language])
                data.append([user, repo, lines, language])
                total_lines += lines
                total_lines_metric.metric(label="Total Lines of Code", value=total_lines)
                update_progress_file(progress_filename, repo)  
            else:
                processing_message.code(f'Skipping {repo}, already processed...')
            progress_bar.progress((i + 1) / len(repos))  
        df = pd.DataFrame(data, columns=['User', 'Repo', 'Lines of Code', 'Language'])
        st.sidebar.dataframe(df)
            
        fig0 = px.parallel_categories(df, color="Lines of Code", color_continuous_scale=px.colors.sequential.Inferno)
        st.plotly_chart(fig0, use_container_width=True)
        cols = st.columns(2)  
        
        with cols[0]:
            fig1 = px.bar(df, x='Repo', y='Lines of Code', title='Lines of Code per Repository')
            st.plotly_chart(fig1, use_container_width=True)
        
        with cols[1]:
            fig2 = px.pie(df, names='Repo', values='Lines of Code', title='Lines of Code per Repository (Pie Chart)')
            st.plotly_chart(fig2, use_container_width=True)
            
        with cols[0]:
            fig3 = px.scatter(df, x='Repo', y='Lines of Code', title='Lines of Code per Repository (Scatter Plot)')
            st.plotly_chart(fig3, use_container_width=True)
            
        with cols[1]:
            fig4 = px.histogram(df, x='Lines of Code', nbins=20, title='Lines of Code Distribution (Histogram)')
            st.plotly_chart(fig4, use_container_width=True)


if __name__ == "__main__":
    main()

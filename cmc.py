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
import json
import matplotlib.pyplot as plt
import subprocess
import sys





def run_gitleaks(user, repo):
    repo_url = f'https://github.com/{user}/{repo}.git'
    output_file = f"{user}_secrets.txt"
    
    cmd = f"chmod +x /app/cmc/gitleaks && /app/cmc/gitleaks --repo-url={repo_url} --report={output_file}"
    subprocess.run(cmd, shell=True)


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




     # For wide layout
def get_all_user_repos(user):
    page = 1
    repos = []

    while True:
        response = requests.get(f'https://github.com/{user}?page={page}&tab=repositories')
        
        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        repo_elements = soup.find_all('a', itemprop='name codeRepository')
        
        if not repo_elements:  # If no more repos found, stop looping
            break

        page_repos = [repo.text.strip() for repo in repo_elements]
        repos.extend(page_repos)
        
        page += 1

    return repos

def get_user_repos(user):
    repo_names = get_all_user_repos(user)
    df = pd.DataFrame(repo_names, columns=['repo_name'])
    
    
    df['repo_size'] = [len(name) for name in df['repo_name']]
    
    return df



def main():
    st.set_page_config(layout="wide")  # For wide layout
    logo_url = 'https://raw.githubusercontent.com/NoDataFound/CMC/main/githublogo.png'

    st.sidebar.markdown(
    f"<div style='text-align: center'><img src='{logo_url}' width='40%'></div>", 
    unsafe_allow_html=True,
)


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
        #st.image(logo_url, width=200)
        #st.title('Lines of Code Counter')
        user = st.text_input('Enter GitHub Username')
        language = st.selectbox('Select Language', list(lang_ext.keys())) 

    if user and language:
        st.sidebar.success(f'Fetching repositories for {user}')
        repos = get_all_user_repos(user)
        #st.sidebar.code(f'Found {len(repos)} repositories for {user}.')
        data = []
        progress_bar = st.progress(0)
        progress_filename = f"{user}_progress.txt"
        df.to_csv('progress.csv', index=False)
        processing_message = st.empty()
        metrics_message = st.empty()
        repo_metrics_message = st.empty()
        

        
        for i, repo in enumerate(repos):
            if not is_repo_processed(progress_filename, repo):  
               
                lines = clone_and_count_lines(user, repo, lang_ext[language])
                
                data.append([user, repo, lines, language])
                total_lines += lines
                metrics_message.info(f'𝖳𝗈𝗍𝖺𝗅 𝖫𝗂𝗇𝖾𝗌 𝗈𝖿 {language}: {total_lines}')
                repo_metrics_message.success(f'𝖳𝗈𝗍𝖺𝗅 𝖱𝖾𝗉𝗈𝗌𝗂𝗍𝗈𝗋𝗂𝖾𝗌: {i+1}')
                processing_message.code(f'Processing {repo}')
                update_progress_file(progress_filename, repo)
            else:
                processing_message.code(f'Skipping {repo}, already processed...')
            progress_bar.progress((i + 1) / len(repos))  
        df = pd.DataFrame(data, columns=['User', 'Repo', 'Lines of Code', 'Language'])
        #st.dataframe(df)  
        st.sidebar.dataframe(df)
        fig0 = px.parallel_categories(df, color="Lines of Code", dimensions=['Repo','Lines of Code', 'Language'],color_continuous_scale=px.colors.sequential.Inferno)
        st.plotly_chart(fig0, use_container_width=True)    
        #fig0 = px.parallel_categories(df, color="Lines of Code", dimensions=['User', 'Repo', 'Lines of Code', 'Language'], color_continuous_scale=px.colors.sequential.Inferno)
        #st.plotly_chart(fig0, use_container_width=True)
        cols = st.columns(2)  
        
        show_secrets = st.sidebar.checkbox('Show secrets', key='show_secrets_key')
        run_secrets = st.sidebar.checkbox('Look for secrets?', key='run_secrets_key')
        if run_secrets:
            run_gitleaks(user, repo)
        if show_secrets:
            secrets_file = f"{user}_secrets.txt"
            if os.path.exists(secrets_file):
                with open(secrets_file, 'r') as f:
                    secrets = f.read()
                st.code(secrets)
                st.markdown(f'<a href="{secrets_file}" download>Download {user} secrets</a>', unsafe_allow_html=True)
            else:
                st.error("No secrets file found. Please run the gitleaks scan.")
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

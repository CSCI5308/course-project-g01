# course-project-g01


## Project Name
## Community Smell Detection Tool


## Overview

Community Smell Detection Tool is a web application solution designed to assist developers in automatically identifying "community smells" within their GitHub repositories. These smells represent patterns of ineffective collaboration, communication, or organizational practices within development teams that can negatively impact project productivity, quality, and timeline. By simply entering the URL of an GitHub repository, developers can analyze their projects for potential community smells and gain actionable insights to improve team dynamics and project outcomes.

This project is built upon and extends the existing [ **CSDetector** ](https://github.com/Nuri22/csDetector) tool, originally created by Nuri22. We have transformed the original command-line interface (CLI) tool into a more accessible and user-friendly web application. This web-based version enhances usability and ensures that the tool is available to a broader audience, including those who may not be comfortable with CLI environments.


**Key Features:**

* **Easy-to-use Web Interface:** A user-friendly web interface allows developers to input their GitHub repository URL and receive detailed analysis results with a copy of report as email.

* **Comprehensive Smell Detection:** The tool identifies a wide range of community smells, including:
    * Organizational Silo Effect
    * Black-cloud Effect
    * Prima-donnas Effect
    * Sharing Villainy
    * Organizational Skirmish
    * Solution Defiance
    * Radio Silence
    * Truck Factor Smell
    * Unhealthy Interaction
    * Toxic Communication

* **Actionable Insights:** Detailed reports provide clear explanations of detected smells and other key metrics detected.


**How it Works:**

1. **User-Friendly Interface**: A simple and intuitive interface for easy input of GitHub repository URL, PAT, and email address.

2. **Data Extraction:** The tool automatically extracts relevant data from the repository, including commit history, issue tracker, pull requests, and discussions.

3. **Smell Detection:** Advanced algorithms analyze the extracted data to identify potential community smells.

4. **Secure Authentication:**  Utilizes GitHub PAT for secure access to repository data.

5. **Report Generation:** The tool generates detailed reports highlighting the detected smells. It also automatically sends the PDF report to the specified email address.

**Limitations:**

1. **Data Accessibility**: The tool works with repositories that provide proper authentication via GitHub PAT.

2. **Smell Detection Scope:** The tool is currently limited to detecting the specified community smells and does not assess technical or code-related issues within the repository.

3. **GitHub Dependency:** The tool relies on GitHub's API and available data; therefore, any changes to GitHub's API or data structures could affect the tool’s functionality

## System Requirements and Pre-requisites

Before you begin, ensure your system meets the following requirements and that the necessary tools are installed:

**1. Operating System**
- Windows 10 or higher
- macOS 10.15 (Catalina) or higher
- Linux (Ubuntu 18.04+ or equivalent)

**2. Python**
- Python 3.8 or higher
  - Verify Python installation using:
    ```bash
    python --version
    ```
    or, for some systems:
    ```bash
    python3 --version
    ```

**3. Git**
- Git is required to clone the repository.
  - Verify Git installation using:
    ```bash
    git --version
    ```
  - Download Git from [https://git-scm.com/downloads](https://git-scm.com/downloads) if not already installed.

**4. Virtual Environment**
- A virtual environment is recommended to avoid dependency conflicts with system-level Python packages.

**5. Dependencies**
- All required Python dependencies are listed in the `requirements.txt` file and will be installed via pip.

**6. Ports and Network**
- Ensure port `3000` is available for the application to run.
- Allow network access to `localhost` or `0.0.0.0` if running on a server.

**7. GitHub Personal Access Token (PAT)**
- If the repository requires authentication, you will need a valid GitHub Personal Access Token (PAT) to clone it. 
- Follow [this guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token) to create a fine-grained PAT.

**8. Repository URL**
-  The URL of project repository to be tested:

**9. Email Address**
- A valid email ID to receive the generated PDF report.

## Installation and Setup Guide

Follow the steps below to set up the project on your system.

**1. Install Python**

Ensure that Python is installed on your machine. You can download Python from the official website:  
[https://www.python.org/downloads/](https://www.python.org/downloads/)

**2. Clone the GitHub Repository**

Clone the repository to your local machine using the following command:

```
git clone https://github.com/CSCI5308/course-project-g01.git
```
**3. Create a Virtual Environment**

Creating a virtual environment is recommended to isolate the project dependencies from your system's Python installation.

* For Windows and Linux distributions other than Ubuntu/Debian, run:
```
python -m venv cs_venv
```
* For Ubuntu/Debian, use:
```
python3 -m venv cs_venv
```
This will create a virtual environment named cs_venv.

**4. Activate the Virtual Environment**

Activate the virtual environment to start working within it:

* For Bash, ZSH, or Windows shell:
```
source cs_venv/bin/activate
```
* For Fish shell:

```
source cs_venv/bin/activate.fish
```

Once activated, your terminal prompt should change, indicating that the virtual environment is active.

**5. Install Required Python Packages**

With the virtual environment activated, install the required dependencies using pip:

```
pip install -r requirements.txt
```
This will install all the necessary libraries for the project.

**6. Verify Virtual Environment is Active**

To ensure the virtual environment is activated correctly, you can run:
```
which python
```
This should return the path to the Python executable within the cs_venv directory.

**7. Update the `.env` File**

The project uses environment variables stored in a .env file. You must update this file with your secret keys and Gmail email credentials for SMTP setup.
- 1. Locate the .env file in the project directory (if it doesn't exist, create one).
- 2. Add the following entries:
```
SMTP_EMAIL=<your-gmail-address>
SMTP_PASSWORD=<your-gmail-app-password>
```
Replace <your-gmail-address>, and <your-gmail-app-password> with your actual values.


**8. Start the Application**

To start the application, use the following command:
```
python -m MLbackend.app
```
This will launch the application.

You can access it in your browser at http://localhost:3000

## Completed Features and Milestones

**1. Functional Web Application**

**2. GitHub Repository Analysis**

**3. Results Page and Visualization**

**4. PDF Report Generation**

**5. Email Notification System for Report**

## Planned Features and Future Enhancements

**1. Enhanced Smell Detection**

**2. Advanced Data Visualizations**

**3.Support for Additional Platforms**

## Work flow diagram

![User Flow Diagram](userflow.svg)


## Folder Structure

- **frontend/**: This directory contains all the code related to the client-side of the application, including user interface components, styling, and client-side logic

- **backend/**: This directory contains the server-side code, including the application logic, GitHub API integrations, and API endpoints that handle requests from the frontend.


## Branches

- **main**: This branch holds the stable, production-ready version of the code, which is deployed in the live environment.

- **development**: This branch is dedicated to ongoing development work, where new features, bug fixes, and improvements are implemented before being merged into the main branch.

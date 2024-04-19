# Final Project

An exercise to put to practice software development teamwork, subsystem communication, containers, deployment, and CI/CD pipelines. See [instructions](./instructions.md) for details.

# Budget Tracker Application

## Introduction
The Budget Tracker is a web-based application designed to help users manage their personal finances effectively. It allows users to track their income and expenses, categorize transactions, and view detailed spending summaries by day, week, month, or year. This tool aims to provide users with clear insights into their financial habits, aiding in better budget management and planning.

## System Architecture
This application is composed of two primary subsystems:

### Subsystem 1: MongoDB Database
**Purpose:** Stores and manages all application data including user credentials, transaction records, and categorization details.
- **Features:**
  - CRUD operations for transactions and user profiles.
  - Efficient data retrieval for reporting and analysis.

### Subsystem 2: Flask Web Application
**Purpose:** Provides the user interface and handles all interactions with the MongoDB database. It processes user requests, performs business logic, and delivers data presentation.
- **Features:**
  - **User Authentication:** Secure registration and login mechanism, session management.
  - **Transaction Management:** Interfaces for adding, editing, and deleting transactions.
  - **Data Visualization:** Detailed spending summaries displayed by various time frames and categories.

## Functionality
- **Registration and Login:** Users can register an account and log in securely to manage their personal transactions.
- **Transaction Handling:** Users can enter transactions with details such as the date, amount, category, and a description of the spend.
- **Financial Summaries:** The application provides reports on spending:
  - **Detailed Summaries:** Users can select specific years or months to retrieve financial data, which is then displayed with percentages showing the distribution of spending across categories.
  - **Periodic Reports:** Automatically generated weekly, monthly, and yearly spending reports help users track their budget compliance over time.

## How It Works
1. **User Interaction:** Through the web interface, users interact with forms and views to enter and manage data.
2. **Data Processing:** The Flask backend processes this data, handling business logic and interacting with the MongoDB database.
3. **Data Storage and Retrieval:** Transactions and user data are stored in MongoDB, which provides fast and reliable access to the data.
4. **Reporting:** Aggregation queries are used to compile spending data into meaningful reports, which are rendered to the user through the Flask application.


# MY health friend: Personalized Health Recommendation System

## Overview
This project is a web-based application powered by **Flask** and **Reinforcement Learning (RL)** to provide personalized health and lifestyle recommendations. It uses user-provided data, including age, gender, BMI, and stress level, to deliver tailored suggestions for improving health outcomes such as stress management, sleep hygiene, and physical activity.

The project incorporates:
- A **user authentication system** (signup/login).
- A **questionnaire** to collect user health data.
- An RL model to generate personalized recommendations based on user data.
- Feedback integration to continuously improve recommendations.

---

## Features
1. **User Authentication**:
   - Signup and login functionality with password hashing.
   - User sessions are securely managed.

2. **Personalized Health Questionnaire**:
   - Users provide data such as age, BMI category, stress level, and sleep duration.
   - Data is stored in a SQLite database for further analysis.

3. **Reinforcement Learning for Recommendations**:
   - Recommendations are generated using an RL agent that adapts over time based on user feedback.
   - Categories include:
     - Stress Management
     - Sleep Hygiene
     - Exercise and Physical Activity
     - Diet and Nutrition

4. **Feedback Integration**:
   - Users provide feedback on the recommendations, which updates the RL model’s Q-table.

5. **Data Visualization**:
   - View and analyze collected questionnaire data.

---

## Technologies Used
- **Python**: Core programming language.
- **Flask**: Web framework for routing and templates.
- **SQLite**: Database for user and questionnaire data.
- **Pandas**: Data manipulation and analysis.
- **Reinforcement Learning**:
  - Epsilon-Greedy Policy
  - Q-Learning Algorithm

---

## Setup Instructions
### Prerequisites
- Python 3.9+
- `pip` (Python package manager)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>

###Set up a virtual environment:

python -m venv venv
source venv/bin/activate   # On Windows: venv\\Scripts\\activate

###Install dependencies:

pip install -r requirements.txt

###Initialize the database:

python app.py

###Place the dataset file (Scientifically_Grounded_Dataset.csv) in the root directory or as configured in bbl3.py

###Run the application:

python app.py

###Open the application in your browser:

http://127.0.0.1:5000/

###Usage

#Sign Up: Create an account to access the personalized recommendation system.
#Complete Questionnaire: Provide your health data for tailored suggestions.
#View Recommendations: Receive actionable advice based on your inputs.
#Provide Feedback: Help improve the RL model by rating the recommendations.

###Dataset

The application uses a dataset (Scientifically_Grounded_Dataset.csv) to generate recommendations. The dataset includes columns such as:

-Stress Management
-Sleep Hygiene
-Exercise and Physical Activity
-Diet and Nutrition

###Future Enhancements
-Add support for advanced analytics and visualizations.
-Integrate machine learning models for enhanced prediction accuracy.
-Expand the dataset with additional health-related metrics.
-Support multi-language functionality.

###Contributors
-Kassraoui Mohammed  
-Oumam Anass
-El Mir Saad 
-Yassine Yasmine

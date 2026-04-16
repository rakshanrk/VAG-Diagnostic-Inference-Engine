# VAG Diagnostic Inference Engine

## Project Overview
This project is a Rule-Based Expert System designed for the diagnostic analysis of the Volkswagen Polo 1.2 TSI (2015 Edition). It leverages Artificial Intelligence principles to simulate the decision-making process of an automotive technician, specifically targeting the VAG (Volkswagen AG) drivetrain and engine ecosystem.

## Artificial Intelligence Implementation

### 1. Knowledge Representation (Knowledge Base)
The core of the system is a structured Knowledge Base (KB) implemented as a symbolic decision tree. The KB contains over 50 discrete states (nodes) covering specific failure modes of the 1.2 TSI engine and the DQ200 DSG transmission. Each node represents either a symptomatic query or a terminal diagnostic conclusion.

### 2. Inference Engine
The system utilizes a Breadth-First-Search (BFS) equivalent traversal logic within its Inference Engine. The engine is purely functional, receiving the current state and a boolean input (Yes/No) to perform forward chaining across the state space. It programmatically determines the next logical node in the graph until a terminal diagnosis is reached.

### 3. Audit Trail (Explainable AI)
A key feature of this Expert System is its Explainable AI (XAI) component. The system maintains an Audit Trail—a temporal trace of the reasoning path. Upon reaching a diagnosis, the system outputs the sequence of rules and user inputs that led to that specific conclusion, ensuring transparency in the decision-making process.

## Technical Architecture
- Backend: Python with Flask Framework (Purely functional, non-OOP implementation)
- Frontend: Vanilla JavaScript, HTML5, and CSS3
- Communication: RESTful JSON payload exchange between the client-side state manager and the server-side inference engine

## Key Modules
- app.py: Contains the Knowledge Base dictionary and the Inference Engine logic.
- templates/index.html: Provides the interactive questionnaire interface and handles the rendering of the diagnostic audit trail.

## How to Run
1. Install dependencies:
   pip install flask
2. Execute the application:
   python app.py
3. Access the system via:
   http://127.0.0.1:8000/

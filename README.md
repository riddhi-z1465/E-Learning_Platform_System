# E-Learning Platform API

A robust **GraphQL API** designed for an E-Learning platform, built with **FastAPI**, **Strawberry**, and backed by **Neo4j Aura** (Graph Database). 

It models complex relationships between students, instructors, courses, assessments, and submissions as a graph, making it highly efficient to navigate deep connections (e.g., getting a completion certificate requires traversing course enrollments, assessments, and submission scores).

**Documentation:** [E-Learning Platform Documentation](https://docs.google.com/document/d/1b4VuupwuHMY_p-5eTYQY8_HM6n-GGEovYgoSQEZHySE/edit?usp=sharing)

## Features

- **GraphQL API**: Exposes a flexible API using Strawberry GraphQL for fast and precise data fetching.
- **Neo4j Graph Database**: Models entities and relationships natively as a graph:
  - `(Instructor) -[:TEACHES]-> (Course)`
  - `(Student) -[:HAS_ENROLLMENT]-> (Enrollment) -[:FOR_COURSE]-> (Course)`
  - `(Course) -[:HAS_ASSESSMENT]-> (Assessment)`
  - `(Student) -[:HAS_SUBMISSION]-> (Submission) -[:FOR_ASSESSMENT]-> (Assessment)`
- **Auto-Increment IDs**: Implements reliable integer IDs using a custom `Counter` node pattern in Neo4j to mimic relational DB auto-incrementing.
- **FastAPI Framework**: Uses async context managers for safe and reliable database connection lifecycle management.
- **Certificates**: Automatically checks enrollment status and submission scores to generate course completion certificates.

## Prerequisites

- Python 3.9+
- A running Neo4j instance (e.g., [Neo4j AuraDB](https://neo4j.com/cloud/platform/aura-graph-database/) Free Tier)

## Setup & Installation

1. **Clone the repository and set up your virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   Make sure you have installed the required libraries (as usually defined in `requirements.txt`). Key dependencies include `fastapi`, `uvicorn`, `strawberry-graphql`, `neo4j`, `python-dotenv`, and `certifi`.

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your Neo4j credentials:

   ```env
   NEO4J_URI=neo4j+s://your-db-id.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_secure_password
   ```

4. **Run the API:**

   ```bash
   uvicorn main:app --reload
   ```

5. **Initialize the Database:**
   The application automatically handles database initialization on startup (creating constraints and seed counters). Look for `Neo4j Aura: database initialised ✓` in the console.

## Usage

Once the server is running, you can access the interactive GraphQL playground built-in with Strawberry:
👉 **[http://localhost:8000/graphql](http://localhost:8000/graphql)**

### Example GraphQL Queries

**Get All Courses and Instructors:**
```graphql
query {
  courses {
    id
    title
    instructor {
      id
      name
    }
  }
}
```

**Enroll a Student:**
```graphql
mutation {
  enrollStudent(studentId: 1, courseId: 101) {
    enrollment {
      id
      status
    }
  }
}
```

## Structure

- `main.py` - FastAPI application setup and GraphQL router integration.
- `db.py` - Neo4j driver connection pooling, SSL patching for macOS, and counter-based ID generation logic.
- `schema.py` - Main GraphQL schema defining queries and mutations.
- `app/types.py` - Strawberry GraphQL type definitions mapping to graph nodes.
- `app/resolvers/` - Cypher execution logic that fetches and mutates graph data. 
- `app/utils.py` - Helper functions used across resolvers.

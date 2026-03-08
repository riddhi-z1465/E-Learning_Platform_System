"""
db.py – Neo4j Aura driver setup for the E-Learning Platform.

Graph model
───────────
Nodes      : Instructor | Student | Course | Assessment | Enrollment | Submission
Counters   : (:Counter {name, value})  →  used for integer auto-increment IDs

Key relationships
  (Instructor) -[:TEACHES]->          (Course)
  (Student)    -[:HAS_ENROLLMENT]->   (Enrollment)
  (Enrollment) -[:FOR_COURSE]->       (Course)
  (Course)     -[:HAS_ASSESSMENT]->   (Assessment)
  (Student)    -[:HAS_SUBMISSION]->   (Submission)
  (Submission) -[:FOR_ASSESSMENT]->   (Assessment)
"""

import os
import ssl
import certifi
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI",      "neo4j+s://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Singleton driver (re-used across requests)
_driver = None


def get_driver():
    global _driver
    if _driver is None:
        # macOS Python 3.13 doesn't auto-pick up the system CA store.
        # Patch the default SSL context to use certifi's bundle so that
        # the 'neo4j+s://' TLS handshake with Aura succeeds.
        _orig_create_default_context = ssl.create_default_context

        def _patched_create_default_context(*args, **kwargs):
            ctx = _orig_create_default_context(*args, **kwargs)
            ctx.load_verify_locations(certifi.where())
            return ctx

        ssl.create_default_context = _patched_create_default_context

        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        )

        # Restore original after driver is created
        ssl.create_default_context = _orig_create_default_context
    return _driver


def close_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def get_session():
    """Return a new Neo4j driver session (caller must close it)."""
    return get_driver().session()


# ─── Database initialisation ─────────────────────────────────────────────────

_INIT_QUERIES = [
    # Uniqueness constraints (also create an index automatically)
    "CREATE CONSTRAINT inst_email  IF NOT EXISTS FOR (n:Instructor)  REQUIRE n.email  IS UNIQUE",
    "CREATE CONSTRAINT stud_email  IF NOT EXISTS FOR (n:Student)     REQUIRE n.email  IS UNIQUE",
    "CREATE CONSTRAINT inst_id     IF NOT EXISTS FOR (n:Instructor)  REQUIRE n.id     IS UNIQUE",
    "CREATE CONSTRAINT stud_id     IF NOT EXISTS FOR (n:Student)     REQUIRE n.id     IS UNIQUE",
    "CREATE CONSTRAINT course_id   IF NOT EXISTS FOR (n:Course)      REQUIRE n.id     IS UNIQUE",
    "CREATE CONSTRAINT enroll_id   IF NOT EXISTS FOR (n:Enrollment)  REQUIRE n.id     IS UNIQUE",
    "CREATE CONSTRAINT assess_id   IF NOT EXISTS FOR (n:Assessment)  REQUIRE n.id     IS UNIQUE",
    "CREATE CONSTRAINT subm_id     IF NOT EXISTS FOR (n:Submission)  REQUIRE n.id     IS UNIQUE",
    # Seed counters (idempotent – only created if not already present, always value:0)
    "MERGE (c:Counter {name:'Instructor'})  ON CREATE SET c.value = 0",
    "MERGE (c:Counter {name:'Student'})     ON CREATE SET c.value = 0",
    "MERGE (c:Counter {name:'Course'})      ON CREATE SET c.value = 0",
    "MERGE (c:Counter {name:'Enrollment'})  ON CREATE SET c.value = 0",
    "MERGE (c:Counter {name:'Assessment'})  ON CREATE SET c.value = 0",
    "MERGE (c:Counter {name:'Submission'})  ON CREATE SET c.value = 0",
]


def init_db():
    """Create constraints, seed counter nodes, and sync counter values to match existing data."""
    with get_session() as session:
        for q in _INIT_QUERIES:
            session.run(q)
        # Sync counters to max existing ID (safe to run on every startup)
        for label in ["Instructor", "Student", "Course", "Enrollment", "Assessment", "Submission"]:
            session.run(
                f"""
                MATCH (c:Counter {{name: $label}})
                OPTIONAL MATCH (n:{label})
                WITH c, coalesce(max(n.id), 0) AS max_id
                SET c.value = CASE WHEN max_id > c.value THEN max_id ELSE c.value END
                """,
                label=label,
            )
    print("Neo4j Aura: database initialised ✓")



# ─── Counter helper ──────────────────────────────────────────────────────────

def next_id(session, label: str) -> int:
    """
    Atomically increment the counter for `label` and return the new integer ID.
    Uses MATCH + SET (coalesce) to handle both fresh and pre-existing counters.
    """
    result = session.run(
        """
        MATCH (c:Counter {name: $label})
        SET c.value = coalesce(c.value, 0) + 1
        RETURN c.value AS new_id
        """,
        label=label,
    )
    record = result.single()
    if record is None:
        raise RuntimeError(f"Counter node for '{label}' not found. Was init_db() called?")
    return record["new_id"]
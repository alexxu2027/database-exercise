-- Schema for data/class_dataset.csv (one row per student intake response).
-- Rules: entity -> table, 1:N -> foreign key, M:N -> bridge table.

-- Entity: student. Single-valued columns stay here as attributes.
CREATE TABLE students (
    student_id            SERIAL PRIMARY KEY,         -- generated; names can repeat
    netid                 TEXT NOT NULL UNIQUE,       -- natural identifier, kept unique
    name                  TEXT NOT NULL,
    school_year           TEXT NOT NULL
        CHECK (school_year IN ('First-year', 'Sophomore', 'Junior', 'Senior')),
    intro_programming     TEXT NOT NULL
        CHECK (intro_programming IN ('took_it', 'equivalent', 'neither')),
    skill_programming     SMALLINT NOT NULL CHECK (skill_programming BETWEEN 1 AND 5),
    skill_data_stats      SMALLINT NOT NULL CHECK (skill_data_stats BETWEEN 1 AND 5),
    skill_frontend_design SMALLINT NOT NULL CHECK (skill_frontend_design BETWEEN 1 AND 5),
    skill_business_pitch  SMALLINT NOT NULL CHECK (skill_business_pitch BETWEEN 1 AND 5),
    working_style         TEXT,                       -- free text
    interests             TEXT,                       -- free text, not delimited
    semester_goal         TEXT,                       -- free text
    submitted_at          TIMESTAMPTZ NOT NULL
);

-- Entity: tool (Python, SQL, Excel, ...).
CREATE TABLE tools (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- M:N students <-> tools.
CREATE TABLE student_tools (
    student_id INTEGER NOT NULL REFERENCES students (student_id) ON DELETE CASCADE,
    tool_id    INTEGER NOT NULL REFERENCES tools (id) ON DELETE CASCADE,
    PRIMARY KEY (student_id, tool_id)
);

-- Entity: availability slot (e.g. "Weekday mornings").
CREATE TABLE availability_slots (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- M:N students <-> availability slots.
CREATE TABLE student_availability (
    student_id INTEGER NOT NULL REFERENCES students (student_id) ON DELETE CASCADE,
    slot_id    INTEGER NOT NULL REFERENCES availability_slots (id) ON DELETE CASCADE,
    PRIMARY KEY (student_id, slot_id)
);

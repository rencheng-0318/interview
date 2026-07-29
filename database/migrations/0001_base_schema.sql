CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE document_type AS ENUM (
    'diagnostic_note',
    'specialist_note',
    'radiology_report',
    'lab_report'
);

CREATE TABLE practices (
    id          text PRIMARY KEY,
    name        text NOT NULL,
    slug        text NOT NULL UNIQUE,
    city        text NOT NULL,
    region      text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT practices_name_not_blank CHECK (btrim(name) <> '')
);

CREATE TABLE users (
    id            text PRIMARY KEY,
    practice_id   text NOT NULL REFERENCES practices (id) ON DELETE CASCADE,
    display_name  text NOT NULL,
    email         text NOT NULL,
    role          text NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT users_role_allowed CHECK (role IN ('clinician', 'nurse', 'admin'))
);

CREATE UNIQUE INDEX users_email_key ON users (lower(email));
CREATE INDEX users_practice_id_idx ON users (practice_id);

CREATE TABLE patients (
    id             text PRIMARY KEY,
    practice_id    text NOT NULL REFERENCES practices (id) ON DELETE CASCADE,
    mrn            text NOT NULL,
    first_name     text NOT NULL,
    last_name      text NOT NULL,
    date_of_birth  date NOT NULL,
    sex            text NOT NULL,
    created_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT patients_sex_allowed CHECK (sex IN ('female', 'male', 'other', 'unknown'))
);

CREATE UNIQUE INDEX patients_practice_mrn_key ON patients (practice_id, mrn);
CREATE INDEX patients_practice_id_idx ON patients (practice_id);

CREATE TABLE clinical_documents (
    id                 text PRIMARY KEY,
    practice_id        text NOT NULL REFERENCES practices (id) ON DELETE CASCADE,
    patient_id         text NOT NULL REFERENCES patients (id) ON DELETE CASCADE,
    document_type      document_type NOT NULL,
    title              text NOT NULL,
    document_date      date NOT NULL,
    author_name        text NOT NULL,
    body               text NOT NULL,
    source_updated_at  timestamptz NOT NULL DEFAULT now(),
    created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX clinical_documents_practice_type_idx
    ON clinical_documents (practice_id, document_type);
CREATE INDEX clinical_documents_patient_idx
    ON clinical_documents (patient_id);
CREATE INDEX clinical_documents_practice_date_idx
    ON clinical_documents (practice_id, document_date DESC);

CREATE FUNCTION clinical_documents_enforce_patient_practice() RETURNS trigger AS $$
BEGIN
    IF NEW.practice_id IS DISTINCT FROM (
        SELECT practice_id FROM patients WHERE id = NEW.patient_id
    ) THEN
        RAISE EXCEPTION
            'clinical_documents.practice_id % does not match patient % practice',
            NEW.practice_id, NEW.patient_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER clinical_documents_practice_matches_patient
    AFTER INSERT OR UPDATE OF practice_id, patient_id ON clinical_documents
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION clinical_documents_enforce_patient_practice();

CREATE FUNCTION clinical_documents_touch_source_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.source_updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER clinical_documents_source_changed
    BEFORE UPDATE ON clinical_documents
    FOR EACH ROW
    WHEN (OLD.body IS DISTINCT FROM NEW.body OR OLD.title IS DISTINCT FROM NEW.title)
    EXECUTE FUNCTION clinical_documents_touch_source_updated_at();

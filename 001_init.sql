-- Jegede Postgres kit, v0.1. Idempotent: safe to run on every startup.
-- Requires PostgreSQL 13+ (for normalize()) and a UTF8 database.

CREATE SCHEMA IF NOT EXISTS jegede;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Locale-independent lowercase for Yoruba text (works even in a "C" locale).
CREATE OR REPLACE FUNCTION jegede.lower(t text) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
  SELECT lower(translate(t, E'\u1EB8\u1ECC\u1E62', E'\u1EB9\u1ECD\u1E63'))
$$;

-- Canonical storage form: NFC.
CREATE OR REPLACE FUNCTION jegede.nfc(t text) RETURNS text
LANGUAGE sql IMMUTABLE AS $$ SELECT normalize(t, NFC) $$;

-- Search key: no tone marks or under-dots, lowercase. 'iṣẹ́' -> 'ise'.
CREATE OR REPLACE FUNCTION jegede.fold(t text) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
  SELECT jegede.lower(normalize(
    regexp_replace(normalize(t, NFD), E'[\u0300-\u036f]', '', 'g'), NFC))
$$;

-- Sort key giving Yoruba alphabetical order under COLLATE "C".
-- Order: a b d e ẹ f g gb h i j k l m n o ọ p r s ṣ t u w y
-- Tone marks are ignored for the primary order, then break ties.
CREATE OR REPLACE FUNCTION jegede.sort_key(t text) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
  SELECT translate(
           replace(
             jegede.lower(normalize(
               regexp_replace(normalize(t, NFD), E'[\u0300\u0301\u0304]', '', 'g'),
               NFC)),
             'gb', E'\uE007'),
           E'abdeg\u1EB9fhijklmno\u1ECDprs\u1E63tuwy',
           E'\uE000\uE001\uE002\uE003\uE006\uE004\uE005\uE008\uE009\uE00A\uE00B\uE00C\uE00D\uE00E\uE00F\uE010\uE011\uE012\uE013\uE014\uE015\uE016\uE017\uE018')
         || E'\u0001' || normalize(t, NFD)
$$;

-- Escape LIKE wildcards in user input.
CREATE OR REPLACE FUNCTION jegede.like_escape(t text) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
  SELECT replace(replace(replace(t, '\', '\\'), '%', '\%'), '_', '\_')
$$;

-- Generic content table: words, proverbs, articles, anything textual.
CREATE TABLE IF NOT EXISTS jegede.entries (
  id          bigserial PRIMARY KEY,
  kind        text        NOT NULL DEFAULT 'entry',
  body        text        NOT NULL,
  body_search text        NOT NULL,
  sort_key    text        NOT NULL COLLATE "C",
  meta        jsonb       NOT NULL DEFAULT '{}',
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION jegede.entries_prepare() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  NEW.body        := jegede.nfc(NEW.body);
  NEW.body_search := jegede.fold(NEW.body);
  NEW.sort_key    := jegede.sort_key(NEW.body);
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS entries_prepare ON jegede.entries;
CREATE TRIGGER entries_prepare
  BEFORE INSERT OR UPDATE OF body ON jegede.entries
  FOR EACH ROW EXECUTE FUNCTION jegede.entries_prepare();

CREATE INDEX IF NOT EXISTS entries_kind_sort_idx ON jegede.entries (kind, sort_key);
CREATE INDEX IF NOT EXISTS entries_search_trgm_idx
  ON jegede.entries USING gin (body_search gin_trgm_ops);

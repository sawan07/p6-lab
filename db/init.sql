-- Invented data. The same script seeds the primary and each read-replica stand-in.
CREATE TABLE IF NOT EXISTS profiles (id INT PRIMARY KEY, ui_id TEXT, display_name TEXT);
INSERT INTO profiles SELECT g, 'UI_0' || (1 + g % 5), 'User ' || g FROM generate_series(1, 5000) g ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS transactions (transaction_id UUID PRIMARY KEY, ui_id TEXT, user_id TEXT, operation TEXT,
  payload_hash TEXT, applied_at TIMESTAMPTZ DEFAULT now());

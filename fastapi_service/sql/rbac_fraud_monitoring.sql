CREATE TABLE IF NOT EXISTS roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE,
  description VARCHAR(255) NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS user_roles (
  user_id INT PRIMARY KEY,
  role VARCHAR(30) NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  action VARCHAR(50) NOT NULL,
  card_id INT NULL,
  old_value VARCHAR(100) NULL,
  new_value VARCHAR(100) NULL,
  created_at DATETIME NOT NULL,
  INDEX (user_id), INDEX (card_id)
);
CREATE TABLE IF NOT EXISTS fraud_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  transaction_id INT NOT NULL,
  user_id INT NOT NULL,
  card_id INT NULL,
  rule_triggered VARCHAR(100) NOT NULL,
  details VARCHAR(255) NOT NULL DEFAULT '',
  email_sent BOOLEAN NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL,
  INDEX (transaction_id)
);
CREATE TABLE IF NOT EXISTS api_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  endpoint VARCHAR(200) NOT NULL,
  method VARCHAR(10) NOT NULL,
  status_code INT NOT NULL,
  response_time_ms FLOAT NOT NULL,
  error_message VARCHAR(500) NULL,
  created_at DATETIME NOT NULL,
  INDEX (created_at)
);
-- run once (MySQL has no ADD COLUMN IF NOT EXISTS)
ALTER TABLE transactions
  ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'Other',
  ADD COLUMN location VARCHAR(100) NULL,
  ADD COLUMN device_id VARCHAR(100) NULL,
  ADD COLUMN fraud_status VARCHAR(20) NOT NULL DEFAULT 'clean';
CREATE INDEX idx_txn_created_at ON transactions (created_at);
CREATE INDEX idx_txn_amount ON transactions (amount);
CREATE INDEX idx_txn_status ON transactions (status);
CREATE INDEX idx_txn_user_created ON transactions (user_id, created_at);
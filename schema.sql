-- IIDA Display schema (also created automatically via SQLAlchemy db.create_all())

CREATE TABLE IF NOT EXISTS "user" (
  id SERIAL PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(256) NOT NULL,
  credits INTEGER DEFAULT 30,
  ai_create_access_paid BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  pm_access_expiry TIMESTAMP
);

CREATE TABLE IF NOT EXISTS report (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES "user"(id),
  question TEXT NOT NULL,
  category VARCHAR(100),
  subcategory VARCHAR(100),
  report_content TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS index_content (
  id SERIAL PRIMARY KEY,
  section VARCHAR(200) NOT NULL,
  content TEXT NOT NULL,
  section_number INTEGER
);

CREATE TABLE IF NOT EXISTS execution_plan (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES "user"(id),
  event_type VARCHAR(100) NOT NULL,
  problem_type TEXT NOT NULL,
  budget VARCHAR(50) NOT NULL,
  currency VARCHAR(10) NOT NULL,
  region VARCHAR(100) NOT NULL,
  timeline VARCHAR(100) NOT NULL,
  plan_content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES "user"(id),
  message TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payment (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES "user"(id),
  cashfree_order_id VARCHAR(255) NOT NULL UNIQUE,
  amount DOUBLE PRECISION NOT NULL,
  currency VARCHAR(10) DEFAULT 'INR',
  credits INTEGER NOT NULL,
  status VARCHAR(50) DEFAULT 'PENDING',
  payment_method VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mentor_chat (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES "user"(id),
  topic VARCHAR(255) NOT NULL,
  location VARCHAR(255) NOT NULL,
  messages TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

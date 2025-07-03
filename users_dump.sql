PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (
	id INTEGER NOT NULL, 
	username VARCHAR, 
	password_hash VARCHAR, 
	email VARCHAR, 
	created_at DATETIME, 
	PRIMARY KEY (id)
);
INSERT INTO users VALUES(1,'nawal','scrypt:32768:8:1$ATpzGPUEQopTcHFF$d8b9c461158a3963171a87b3ecf98582226bc518ab483a2f65c210b0e837eeda16ad913f701d1356ca8857b1024fc037adc326f6cac17bec107bd5fbc57c1a14','naoualkhelloufitmp@gmail.com','2025-07-02 14:52:22.486493');
INSERT INTO users VALUES(2,'naoual','scrypt:32768:8:1$kCWvXpl3pUZzyGm1$ced7ea01f4c1b2694092f2c780a5d8a687b5b8c894094eb7c3972fbd63aa0bcd9da34da8787da13f9e47bc9119cb319aed0061f09f34580b8909933d3a924faa','khelloufinaoual@gmail.com','2025-07-02 15:00:34.118309');
CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_username ON users (username);
COMMIT;

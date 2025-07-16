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
INSERT INTO users VALUES(3,'khelloufi','scrypt:32768:8:1$4IQgIDULaT8sCQsT$20c0c7f5af77557256b1f2e40e778f15b9d239d1656fca076541e611aa9e8b7e020ff96df39995f4a51210b9c816fae397d25ef2ae8a5c3ddc4412f936f42342','','2025-07-03 14:09:36.393244');
INSERT INTO users VALUES(4,'Loubna','scrypt:32768:8:1$pLjW6V6eLXBLvukp$a5c6695c65a12dca34be0b3c07cee8da91c3500246aa8ed3cafb5186d14eefe723c95cee89ad160a156f8b5d0e9ae8cc48c7fbc3c70485402aaea7f061b4fe1a','','2025-07-10 12:08:32.970636');
INSERT INTO users VALUES(5,'nawal1','scrypt:32768:8:1$ql6sPzKnTev7Yek8$fa5038ad47dba571e0eb70f375df5613e9546974a8a78e2999ebafcc39ba2ed75d200a9c8017e711ede923daff29d2f507a30bb94e287fae9e33f6704c290ed5','','2025-07-16 00:52:40.357563');
INSERT INTO users VALUES(6,'nawal2','scrypt:32768:8:1$HR8TyLxvJ6SxN35W$421b6b2b18f9fe7d6d2e6866fce91ee2ea32554fcadf5caf3e741406a12b609af46aa434efad056c012e799ae2577996e708e0c2ac727bdd58765486352f95ba','','2025-07-16 13:17:30.595482');
INSERT INTO users VALUES(7,'loubna1','scrypt:32768:8:1$L5uK3emUSS2tIFHw$19491f73a23a0117a52eec281e34643f7606ceeade5a20487cf583899758edf1a153ee6e7afadfc5ba127c11665330a8f3bf51f5508b5be3b90ca6e60dd8e404','','2025-07-16 13:24:19.126205');
CREATE TABLE chat_history (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	question TEXT NOT NULL, 
	answer TEXT NOT NULL, 
	timestamp DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO chat_history VALUES(1,1,'c''est quoi le titre de ce document ?','Le titre de ce document est : "Projet d''application de chatbot pour analyse de contenu" ou plus précisément "Détails du projet d''application de chatbot pour analyse de contenu"','2025-07-11 15:49:43.963880');
INSERT INTO chat_history VALUES(2,1,'Donne moi un résumer de ce document',replace('Voici un résumé du document :\n\nLe document décrit la conception et le développement d''une application web qui permet aux utilisateurs de télécharger des fichiers, d''auto-entraîner un modèle NLP (Réseau de neurones artificiel) avec ces fichiers et d''utiliser l''intelligence artificielle pour répondre à leurs questions. L''application doit être ergonomique, sécurisée et performante.\n\nLes fonctionnalités clés de l''application sont :\n\n* Téléchargement de fichiers PDF, TXT, CSV, etc.\n* Entraînement automatique du modèle NLP avec les fichiers téléchargés\n* Interface de chat pour poser des questions et obtenir des réponses contextuelles\n\nLe document décrit également les contraintes techniques, telles que la mise en œuvre d''un backend Python ou Node.js, d''un frontend JavaScript avec React ou Angular, ainsi que la nécessité d''une base de données sécurisée.\n\nLes livrables attendus incluent :\n\n* Une documentation technique détaillée\n* Le code source développé avec gestion de versions Git\n* Des instructions pour le déploiement et la maintenance\n* Un prototype opérationnel de l''application\n* Un rapport de stage détaillant le processus de développement, les tests effectués et les perspectives d''évolution\n\nLes critères de réussite incluent :\n\n* Les fonctionnalités complètes et opérationnelles\n* L''intuitivité de l''interface utilisateur\n* La performance et la rapidité des réponses\n* La sécurité des données','\n',char(10)),'2025-07-11 15:59:49.991869');
CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_username ON users (username);
CREATE INDEX ix_chat_history_id ON chat_history (id);
COMMIT;

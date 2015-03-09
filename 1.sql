DROP TABLE IF EXISTS `user`;

CREATE TABLE `user` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`username` VARCHAR(50),
	`email` VARCHAR(100),
	`password` CHAR(60),
	`youtube_access_token` VARCHAR(255),
	`last_update` DATETIME DEFAULT NULL,
	`created` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	`status` CHAR(1),
	PRIMARY KEY(id)
);

CREATE TABLE `playlist` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`user_id` INT,
	`playlist_name` VARCHAR(50),
	`last_update` DATETIME DEFAULT NULL,
	`created` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	`status` CHAR(1),
	PRIMARY KEY(id)
);

CREATE TABLE `video` (
	`id` INT NOT NULL AUTO_INCREMENT,
	`user_id` INT,
	`playlist_id` INT,
	`video_id` VARCHAR(100), 
	`created` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	`status` CHAR(1),
	PRIMARY KEY(id)
);
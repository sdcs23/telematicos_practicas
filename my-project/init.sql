CREATE DATABASE myflaskapp;
use myflaskapp;

CREATE TABLE users (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name varchar(100),
    email varchar(100),
    username varchar(30),
    password varchar(100),
    register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

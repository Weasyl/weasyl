CREATE DATABASE weasyl_test;
ALTER DATABASE weasyl_test SET search_path TO public, extension_objects;

\c weasyl_test

CREATE SCHEMA extension_objects;
CREATE EXTENSION hstore WITH SCHEMA extension_objects;
CREATE EXTENSION fuzzystrmatch WITH SCHEMA extension_objects;

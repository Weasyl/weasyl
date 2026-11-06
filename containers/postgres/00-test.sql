ALTER DATABASE weasyl_test SET search_path TO public, extension_objects;

CREATE SCHEMA extension_objects;
CREATE EXTENSION hstore WITH SCHEMA extension_objects;
CREATE EXTENSION fuzzystrmatch WITH SCHEMA extension_objects;

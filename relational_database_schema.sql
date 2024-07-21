-- Switch to the schema
SET search_path TO relational_database_schema;

-- Create the Articles table
CREATE TABLE Articles (
    article_id INT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    content TEXT,
    url VARCHAR(255) NOT NULL UNIQUE
);

-- Create the Entities table
CREATE TABLE Entities (
    entity_id INT PRIMARY KEY,
    name VARCHAR(255),
    type VARCHAR(50) 
);

-- Create the ArticleEntities table to link articles and entities
CREATE TABLE ArticleEntities (
    article_id INT,
    entity_id INT,
    PRIMARY KEY (article_id, entity_id),
    FOREIGN KEY (article_id) REFERENCES Articles(article_id) ON DELETE CASCADE,
    FOREIGN KEY (entity_id) REFERENCES Entities(entity_id) ON DELETE CASCADE
);

-- Create the EntityRelationships table to capture relationships between entities
CREATE TABLE EntityRelationships (
    relationship_id INT PRIMARY KEY,
    entity1_id INT,
    entity2_id INT,
    article_id INT,
    sentence TEXT,
    FOREIGN KEY (entity1_id) REFERENCES Entities(entity_id) ON DELETE CASCADE,
    FOREIGN KEY (entity2_id) REFERENCES Entities(entity_id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES Articles(article_id) ON DELETE CASCADE
);

-- Create the ArticleKeywords table to store keywords associated with articles
CREATE TABLE ArticleKeywords (
    article_id INT,
    keyword VARCHAR(255),
    PRIMARY KEY (article_id, keyword),
    FOREIGN KEY (article_id) REFERENCES Articles(article_id) ON DELETE CASCADE
);

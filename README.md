# Web_Scraping_LLM_SQL
Description: This assignment integrates web scraping, knowledge graph development, and large language model (LLM) technology to create a structured database for a news website.

Files used: 
1. app.py: Python script used for the web scraping, knowledge graph development, and  large language model.
2. relational_database_schema.sql: a relational database schema to store the extracted article information (title, date, content, URL) and the knowledge graph data (nodes and relationships).
3. Knowledge_Graph.png

Steps: 
1. Used web scraping libraries to gather news articles from a website, extracting titles, publication dates, content, and URLs, and applied NLP libraries to identify named entities and keywords in the content.
2. Created nodes for entities and articles, and established relationships between them based on co-occurrence in articles, as well as linking articles by shared keywords or topics.
3. Leveraged the OpenAI API to analyze article content, uncover additional relationships between entities, and integrate these LLM-derived connections into the knowledge graph.
4. Designed a relational database schema to store the extracted article information and knowledge graph data using the PostgreSQL database management system.





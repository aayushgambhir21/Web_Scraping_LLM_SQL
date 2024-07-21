#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 21 02:35:53 2024

@author: aayushgambhir
"""
import requests
from bs4 import BeautifulSoup
import re
import networkx as nx
import matplotlib.pyplot as plt
import textwrap
import spacy
from datetime import datetime

# Load the spaCy model
nlp = spacy.load('en_core_web_sm')

def wrap_text(text, width=1.0):
    """Wrap text for better fitting in the node."""
    return '\n'.join(textwrap.wrap(text, width))

def extract_date(text):
    """Extract and parse date from text."""
    # Define various date patterns
    patterns = [
        r'\b(?:Updated:|Published:)?\s*(\d{1,2}(?:st|nd|rd|th)? \w+ \d{4})\b',  # e.g., "21st July 2024"
        r'\b(?:Updated:|Published:)?\s*(\w+ \d{1,2}(?:st|nd|rd|th)?, \d{4})\b',  # e.g., "July 21st, 2024"
        r'\b(?:Updated:|Published:)?\s*(\d{1,2}-\w{3}-\d{4})\b',  # e.g., "21-Jul-2024"
        r'\b(?:Updated:|Published:)?\s*(\d{4}-\d{2}-\d{2})\b',  # e.g., "2024-07-21"
        r'\b(\d{1,2} [A-Za-z]+ \d{4})\b',  # e.g., "21 July 2024"
        r'\b([A-Za-z]+ \d{1,2}, \d{4})\b',  # e.g., "July 21, 2024"
        r'\b(\d{2}/\d{2}/\d{4})\b'  # e.g., "07/21/2024"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            # Normalize the date string by removing suffixes and parsing it
            date_str = re.sub(r'(st|nd|rd|th)', '', date_str).strip()
            try:
                # Handle different formats
                try:
                    date_obj = datetime.strptime(date_str, '%d %B %Y')  # e.g., "21 July 2024"
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_str, '%B %d, %Y')  # e.g., "July 21, 2024"
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(date_str, '%d-%b-%Y')  # e.g., "21-Jul-2024"
                        except ValueError:
                            try:
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')  # e.g., "2024-07-21"
                            except ValueError:
                                try:
                                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')  # e.g., "07/21/2024"
                                except ValueError:
                                    return "No Date"
                return date_obj.strftime('%Y-%m-%d')  # Standard format YYYY-MM-DD
            except ValueError:
                continue
    return "No Date"

def fetch_article_details(article_url):
    """Fetch and parse details from an article URL."""
    try:
        page_request = requests.get(article_url)
        page_request.raise_for_status()
        data = page_request.content
        soup = BeautifulSoup(data, "html.parser")

        # Extract the title
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        # Extract the date from various potential locations
        date_text = "No Date"
        
        # Check common HTML tags for date
        possible_date_tags = [
            soup.find('meta', {'property': 'article:published_time'}),
            soup.find('time'),
            soup.find('span', class_=re.compile(r'date', re.IGNORECASE)),
            soup.find('p', class_=re.compile(r'date', re.IGNORECASE)),
            soup.find('div', class_=re.compile(r'date', re.IGNORECASE)),
            soup.find('meta', {'name': 'date'}),
            soup.find('meta', {'name': 'pubdate'})
        ]
        
        for tag in possible_date_tags:
            if tag and tag.get_text(strip=True):
                date_text = extract_date(tag.get_text(strip=True))
                if date_text != "No Date":
                    break
        
        # Check anchor tags for additional date information
        if date_text == "No Date":
            anchor_tags = soup.find_all('a', href=True)
            for anchor_tag in anchor_tags:
                date_text = extract_date(anchor_tag.get_text(strip=True))
                if date_text != "No Date":
                    break

        # Extract the content
        meta_description = soup.find('meta', {'name': 'description'})
        content = meta_description['content'] if meta_description else "No Content"

        # Process content with spaCy
        doc = nlp(content)
        
        # Extract named entities and categorize them
        people = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
        organizations = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
        locations = [ent.text for ent in doc.ents if ent.label_ == 'GPE']
        
        # Extract keywords (for simplicity, we'll use noun chunks)
        keywords = [chunk.text for chunk in doc.noun_chunks]

        # Extract relationships based on sentence parsing
        relationships = []
        for sent in doc.sents:
            ents = [ent.text for ent in sent.ents]
            if len(ents) > 1:
                for i in range(len(ents) - 1):
                    relationships.append((ents[i], ents[i + 1], sent.text))

        return title, date_text, article_url, content, people, organizations, locations, keywords, relationships

    except requests.RequestException as e:
        print(f"Error fetching article details: {e}")
        return None

def timesofindia():
    """Fetch and process articles from Times of India."""
    url = "https://timesofindia.indiatimes.com/home/headlines"
    page_request = requests.get(url)
    data = page_request.content
    soup = BeautifulSoup(data, "html.parser")

    counter = 0
    articles = []
    for divtag in soup.find_all('div', {'class': 'headlines-list'}):
        for ultag in divtag.find_all('ul', {'class': 'clearfix'}):
            if counter < 10:
                for litag in ultag.find_all('li'):
                    counter += 1
                    article_url = "https://timesofindia.indiatimes.com" + litag.find('a')['href']
                    details = fetch_article_details(article_url)
                    if details:
                        articles.append({
                            "url": details[2],
                            "title": details[0],
                            "date": details[1],
                            "content": details[3],
                            "people": details[4],
                            "organizations": details[5],
                            "locations": details[6],
                            "keywords": details[7],
                            "relationships": details[8]
                        })

    # Print the details of the articles
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"Date: {article['date']}")
        print(f"URL: {article['url']}")
        print(f"Content: {article['content']}")
        print(f"People: {', '.join(article['people'])}")
        print(f"Organizations: {', '.join(article['organizations'])}")
        print(f"Locations: {', '.join(article['locations'])}")
        print(f"Keywords: {', '.join(article['keywords'])}")
        print("-" * 80)

    # Create the graph
    G = nx.Graph()

    for article in articles:
        title_wrapped = wrap_text(article["title"], width=40)  # Adjust width for better wrapping
        G.add_node(title_wrapped, type="article", title=title_wrapped, date=article["date"])

        # Add people, organizations, and locations as nodes
        for person in article["people"]:
            G.add_node(person, type="person")
            G.add_edge(title_wrapped, person)

        for organization in article["organizations"]:
            G.add_node(organization, type="organization")
            G.add_edge(title_wrapped, organization)

        for location in article["locations"]:
            G.add_node(location, type="location")
            G.add_edge(title_wrapped, location)

        # Create relationships between entities
        for entity1, entity2, sentence in article["relationships"]:
            if entity1 != entity2:
                G.add_edge(entity1, entity2, label=sentence)

        # Create relationships between articles based on shared keywords
        for keyword in article["keywords"]:
            G.add_node(keyword, type="keyword")
            G.add_edge(title_wrapped, keyword)

    # Position the nodes using a spring layout
    pos = nx.spring_layout(G, k=1.0)  # Increase the k value to further increase the distance between nodes

    plt.figure(figsize=(40, 40))  # Adjust figure size
    nx.draw(G, pos, with_labels=False, node_size=5000, node_color="skyblue", font_size=6, font_weight="bold", font_family="Arial", edge_color='gray')

    # Adjust text wrapping for better readability
    for node, (x, y) in pos.items():
        plt.text(x, y, node, fontsize=10, ha='center', va='center', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))

    plt.show()

if __name__ == "__main__":
    timesofindia()


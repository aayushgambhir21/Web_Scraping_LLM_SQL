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
import openai
import time

# Load the spaCy model
nlp = spacy.load('en_core_web_sm')

# OpenAI API key (make sure to set your own API key here)
openai.api_key = 'sk-proj-QKVpaH15mS3fCIyJOnGZT3BlbkFJi8Q8XbwldaOTOfJMMeuW'

def wrap_text(text, width=1.0):
    """Wrap text for better fitting in the node."""
    return '\n'.join(textwrap.wrap(text, width))

def extract_date(text):
    """Extract and parse date from text."""
    patterns = [
        r'\b(?:Updated:|Published:)?\s*(\d{1,2}(?:st|nd|rd|th)? \w+ \d{4})\b',
        r'\b(?:Updated:|Published:)?\s*(\w+ \d{1,2}(?:st|nd|rd|th)?, \d{4})\b',
        r'\b(?:Updated:|Published:)?\s*(\d{1,2}-\w{3}-\d{4})\b',
        r'\b(?:Updated:|Published:)?\s*(\d{4}-\d{2}-\d{2})\b',
        r'\b(\d{1,2} [A-Za-z]+ \d{4})\b',
        r'\b([A-Za-z]+ \d{1,2}, \d{4})\b',
        r'\b(\d{2}/\d{2}/\d{4})\b'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            date_str = re.sub(r'(st|nd|rd|th)', '', date_str).strip()
            try:
                try:
                    date_obj = datetime.strptime(date_str, '%d %B %Y')
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_str, '%B %d, %Y')
                    except ValueError:
                        try:
                            date_obj = datetime.strptime(date_str, '%d-%b-%Y')
                        except ValueError:
                            try:
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            except ValueError:
                                try:
                                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                                except ValueError:
                                    return "No Date"
                return date_obj.strftime('%Y-%m-%d')
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

        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        date_text = "No Date"
        
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
        
        if date_text == "No Date":
            anchor_tags = soup.find_all('a', href=True)
            for anchor_tag in anchor_tags:
                date_text = extract_date(anchor_tag.get_text(strip=True))
                if date_text != "No Date":
                    break

        meta_description = soup.find('meta', {'name': 'description'})
        content = meta_description['content'] if meta_description else "No Content"

        doc = nlp(content)
        
        people = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
        organizations = [ent.text for ent in doc.ents if ent.label_ == 'ORG']
        locations = [ent.text for ent in doc.ents if ent.label_ == 'GPE']
        
        keywords = [chunk.text for chunk in doc.noun_chunks]

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

def analyze_relationships_with_openai(text, entities):
    """Use OpenAI API to analyze relationships between entities in the text."""
    prompt = f"""
    Analyze the following text and identify any cause-and-effect relationships, 
    as well as other relationships between the listed entities. 
    Entities: {', '.join(entities)}
    
    Text:
    {text}
    
    Identify relationships in the format: (Entity1, Entity2, Relationship Type)
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that helps analyze relationships between entities."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )
        relationships_text = response.choices[0].message['content'].strip()
        relationships = []
        for rel in relationships_text.split('\n'):
            parts = rel.strip().split(', ')
            if len(parts) == 3:
                relationships.append(tuple(parts))
        return relationships

    except openai.error.RateLimitError:
        print("Rate limit exceeded. Retrying in 60 seconds...")
        time.sleep(60)  # Wait before retrying
        return []

    except openai.error.AuthenticationError:
        print("Authentication error. Please check your API key.")
        return []

    except openai.error.InvalidRequestError as e:
        print(f"Invalid request error: {e}")
        return []

    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return []

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
                        all_entities = set(details[4] + details[5] + details[6])  # Combine people, organizations, and locations
                        openai_relationships = analyze_relationships_with_openai(details[3], all_entities)
                        
                        articles.append({
                            "url": details[2],
                            "title": details[0],
                            "date": details[1],
                            "content": details[3],
                            "people": details[4],
                            "organizations": details[5],
                            "locations": details[6],
                            "keywords": details[7],
                            "relationships": details[8] + openai_relationships  # Concatenate lists
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
        print(f"Relationships: {article['relationships']}")  # Added for debugging
        print("-" * 80)

    G = nx.Graph()

    for article in articles:
        title_wrapped = wrap_text(article["title"], width=40)
        G.add_node(title_wrapped, type="article", title=title_wrapped, date=article["date"])

        for person in article["people"]:
            G.add_node(person, type="person")
            G.add_edge(title_wrapped, person)

        for organization in article["organizations"]:
            G.add_node(organization, type="organization")
            G.add_edge(title_wrapped, organization)

        for location in article["locations"]:
            G.add_node(location, type="location")
            G.add_edge(title_wrapped, location)

        for relationship in article["relationships"]:
            if len(relationship) == 3:  # Ensure correct unpacking
                entity1, entity2, sentence = relationship
                if entity1 != entity2:
                    G.add_edge(entity1, entity2, label=sentence)

        for keyword in article["keywords"]:
            G.add_node(keyword, type="keyword")
            G.add_edge(title_wrapped, keyword)

    pos = nx.spring_layout(G, k=1.0)

    plt.figure(figsize=(40, 40))
    nx.draw(G, pos, with_labels=False, node_size=5000, node_color="skyblue", font_size=6, font_weight="bold", font_family="Arial", edge_color='gray')

    for node, (x, y) in pos.items():
        plt.text(x, y, node, fontsize=10, ha='center', va='center', bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))

    plt.show()

if __name__ == "__main__":
    timesofindia()

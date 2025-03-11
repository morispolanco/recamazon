import streamlit as st
import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict
import os
import re

# Set page config
st.set_page_config(page_title="Amazon Book Analyzer", layout="wide")

# Function to get OpenRouter response
def get_openrouter_response(prompt: str) -> str:
    api_key = st.secrets["OPENROUTER_API_KEY"]
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "amazon/nova-lite-v1",  # Replace with actual model if needed
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error connecting to OpenRouter: {str(e)}")
        return None

# Updated function to search related books
def search_related_products(product_name: str) -> List[Dict]:
    prompt = f"""Search Amazon for books related to '{product_name}'. Return a JSON list of up to 10 book URLs in this exact format: 
    ["url1", "url2", ...]. 
    Only include books, no other product types. Ensure the response is valid JSON. If no books are found, return an empty JSON list []."""
    st.write(f"Debug: Sending prompt to OpenRouter: {prompt}")
    
    response = get_openrouter_response(prompt)
    if response is None:
        st.error("No response from OpenRouter")
        return []
    
    st.write(f"Debug: Raw API response: '{response}'")
    
    if not response.strip():
        st.error("Empty response received from API")
        return []
    
    try:
        parsed_urls = json.loads(response)
        if isinstance(parsed_urls, list):
            st.write(f"Debug: Successfully parsed URLs: {parsed_urls}")
            return [{"url": url} for url in parsed_urls[:10] if isinstance(url, str) and url.startswith("http")]
        else:
            st.write("Debug: Response is not a valid list")
            return []
    except json.JSONDecodeError as e:
        st.error(f"Error parsing API response as JSON: {str(e)}")
        st.write("Debug: Attempting to extract URLs from plain text as fallback")
        # Fallback: Extract URLs from plain text
        urls = re.findall(r'https?://[^\s"]+', response)
        if urls:
            st.write(f"Debug: Extracted URLs from text: {urls}")
            return [{"url": url} for url in urls[:10]]
        else:
            st.write("Debug: No URLs found in response")
            return []
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return []

# Function to get book details
def get_product_details(urls: List[str]) -> List[Dict]:
    prompt = f"""Get detailed information for these Amazon book URLs including price, description, author, publisher, and ISBN:
    {json.dumps(urls)}
    Support up to 50 book URLs and return as JSON. Only process URLs that correspond to books."""
    
    response = get_openrouter_response(prompt)
    if response:
        try:
            return json.loads(response)[:50]
        except:
            return []
    return []

# Function to get book reviews
def get_product_reviews(urls: List[str]) -> List[Dict]:
    prompt = f"""Retrieve detailed customer reviews and ratings for these Amazon book URLs:
    {json.dumps(urls)}
    Support up to 50 book URLs and return as JSON with review text and rating. Only process URLs that correspond to books."""
    
    response = get_openrouter_response(prompt)
    if response:
        try:
            return json.loads(response)[:50]
        except:
            return []
    return []

# Function to generate book recommendations
def generate_recommendations(product_data: List[Dict]) -> str:
    prompt = f"""Based on this book data:
    {json.dumps(product_data)}
    Generate recommendations for book title, features (like genre, length, or target audience), and price."""
    
    return get_openrouter_response(prompt)

# Main Streamlit app
def main():
    st.title("Amazon Book Analyzer")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        product_name = st.text_input("Enter a book title or topic")
        analyze_button = st.button("Analyze Books")
    
    # Main content
    if analyze_button and product_name:
        with st.spinner("Analyzing books..."):
            # Step 1: Search related books
            related_books = search_related_products(product_name)
            if not related_books:
                st.error("No related books found")
                return
                
            urls = [book["url"] for book in related_books]
            
            # Step 2: Get book details
            book_details = get_product_details(urls)
            
            # Step 3: Get reviews
            reviews = get_product_reviews(urls)
            
            # Step 4: Generate recommendations
            recommendations = generate_recommendations(book_details)
            
            # Display results
            tab1, tab2, tab3, tab4 = st.tabs(["Related Books", "Book Details", "Reviews", "Recommendations"])
            
            with tab1:
                st.subheader("Related Books")
                st.json(related_books)
                
            with tab2:
                st.subheader("Book Details")
                if book_details:
                    df_details = pd.DataFrame(book_details)
                    st.dataframe(df_details)
                else:
                    st.write("No book details available")
                    
            with tab3:
                st.subheader("Customer Reviews")
                if reviews:
                    df_reviews = pd.DataFrame(reviews)
                    st.dataframe(df_reviews)
                else:
                    st.write("No reviews available")
                    
            with tab4:
                st.subheader("Book Recommendations")
                st.write(recommendations if recommendations else "No recommendations generated")

if __name__ == "__main__":
    # Check if API key is set in secrets
    if "OPENROUTER_API_KEY" not in st.secrets:
        st.error("Please add your OpenRouter API key to Streamlit secrets")
    else:
        main()

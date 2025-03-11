import streamlit as st
import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict
import os

# Set page config
st.set_page_config(page_title="Amazon Product Analyzer", layout="wide")

# Function to get OpenRouter response
def get_openrouter_response(prompt: str) -> str:
    api_key = st.secrets["OPENROUTER_API_KEY"]
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "amazon/nova-lite-v1",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error connecting to OpenRouter: {str(e)}")
        return None

# Function to search related products
def search_related_products(product_name: str) -> List[Dict]:
    prompt = f"Search for products related to '{product_name}' on Amazon and return a list of product URLs (up to 10)"
    response = get_openrouter_response(prompt)
    if response:
        try:
            urls = json.loads(response)
            return [{"url": url} for url in urls[:10]]
        except:
            return []
    return []

# Function to get product details
def get_product_details(urls: List[str]) -> List[Dict]:
    prompt = f"""Get detailed product information from these Amazon URLs including price, description, and specifications:
    {json.dumps(urls)}
    Support up to 50 URLs and return as JSON"""
    
    response = get_openrouter_response(prompt)
    if response:
        try:
            return json.loads(response)[:50]
        except:
            return []
    return []

# Function to get reviews
def get_product_reviews(urls: List[str]) -> List[Dict]:
    prompt = f"""Retrieve detailed customer reviews and ratings from these Amazon URLs:
    {json.dumps(urls)}
    Support up to 50 URLs and return as JSON with review text and rating"""
    
    response = get_openrouter_response(prompt)
    if response:
        try:
            return json.loads(response)[:50]
        except:
            return []
    return []

# Function to generate recommendations
def generate_recommendations(product_data: List[Dict]) -> str:
    prompt = f"""Based on this product data:
    {json.dumps(product_data)}
    Generate recommendations for product name, features, and price"""
    
    return get_openrouter_response(prompt)

# Main Streamlit app
def main():
    st.title("Amazon Product Analyzer")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        product_name = st.text_input("Enter your product name")
        analyze_button = st.button("Analyze")
    
    # Main content
    if analyze_button and product_name:
        with st.spinner("Analyzing products..."):
            # Step 1: Search related products
            related_products = search_related_products(product_name)
            if not related_products:
                st.error("No related products found")
                return
                
            urls = [product["url"] for product in related_products]
            
            # Step 2: Get product details
            product_details = get_product_details(urls)
            
            # Step 3: Get reviews
            reviews = get_product_reviews(urls)
            
            # Step 4: Generate recommendations
            recommendations = generate_recommendations(product_details)
            
            # Display results
            tab1, tab2, tab3, tab4 = st.tabs(["Related Products", "Product Details", "Reviews", "Recommendations"])
            
            with tab1:
                st.subheader("Related Products")
                st.json(related_products)
                
            with tab2:
                st.subheader("Product Details")
                if product_details:
                    df_details = pd.DataFrame(product_details)
                    st.dataframe(df_details)
                else:
                    st.write("No details available")
                    
            with tab3:
                st.subheader("Customer Reviews")
                if reviews:
                    df_reviews = pd.DataFrame(reviews)
                    st.dataframe(df_reviews)
                else:
                    st.write("No reviews available")
                    
            with tab4:
                st.subheader("Recommendations")
                st.write(recommendations if recommendations else "No recommendations generated")

if __name__ == "__main__":
    # Check if API key is set in secrets
    if "OPENROUTER_API_KEY" not in st.secrets:
        st.error("Please add your OpenRouter API key to Streamlit secrets")
    else:
        main()

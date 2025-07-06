import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from products.models import Product, OrderItem, Review
from recommendations.models import UserProductInteraction
from django.db import models

def get_popular_products(limit=5):
    """Get most popular products based on purchases and reviews"""
    # Get top purchased products
    top_purchased = list(OrderItem.objects.values('product')
                        .annotate(count=models.Count('product'))
                        .order_by('-count')[:limit])
    
    # Get top rated products
    top_rated = list(Review.objects.values('product')
                    .annotate(avg_rating=models.Avg('rating'))
                    .order_by('-avg_rating')[:limit])
    
    # Combine and deduplicate
    product_ids = set()
    popular_products = []
    
    for item in top_purchased + top_rated:
        if item['product'] not in product_ids:
            product_ids.add(item['product'])
            try:
                product = Product.objects.get(id=item['product'])
                popular_products.append(product)
            except Product.DoesNotExist:
                continue
    
    return popular_products[:limit]

def create_interaction_matrix():
    """Create a user-product interaction matrix for collaborative filtering"""
    interactions = UserProductInteraction.objects.all().values('user', 'product', 'view_count', 'purchased')
    
    if not interactions:
        return None, None, None
    
    df = pd.DataFrame.from_records(interactions)
    
    # Create a weight for each interaction
    df['weight'] = df['view_count'] * 0.1 + df['purchased'] * 1.0
    
    # Create pivot table
    interaction_matrix = df.pivot_table(index='user', columns='product', values='weight', fill_value=0)
    
    # Calculate cosine similarity
    user_similarity = cosine_similarity(interaction_matrix)
    product_similarity = cosine_similarity(interaction_matrix.T)
    
    return interaction_matrix, user_similarity, product_similarity

def get_personalized_recommendations(user_id, limit=5):
    """Get personalized recommendations for a user"""
    interaction_matrix, user_similarity, product_similarity = create_interaction_matrix()
    
    if interaction_matrix is None:
        return get_popular_products(limit)
    
    try:
        user_idx = interaction_matrix.index.get_loc(user_id)
    except KeyError:
        return get_popular_products(limit)
    
    # Get similar users
    similar_users = np.argsort(user_similarity[user_idx])[::-1][1:4]  # top 3 similar users
    
    # Get products those users interacted with
    recommended_products = set()
    for sim_user_idx in similar_users:
        sim_user_id = interaction_matrix.index[sim_user_idx]
        top_products = interaction_matrix.loc[sim_user_id].sort_values(ascending=False).index[:5]
        recommended_products.update(top_products)
    
    # Get products the user hasn't interacted with
    user_products = set(interaction_matrix.columns[interaction_matrix.loc[user_id] > 0])
    recommended_products = recommended_products - user_products
    
    # Get product objects
    products = Product.objects.filter(id__in=recommended_products)[:limit]
    
    return products

def enhance_search_with_keywords(query, products):
    """
    Enhanced search for small catalogs that:
    1. Prioritizes exact matches
    2. Boosts matches in important fields
    3. Uses simple keyword matching
    """
    if not query or not products:
        return products
    
    query = query.lower().strip()
    query_words = query.split()
    
    scored_products = []
    
    for product in products:
        score = 0
        
        # Fields to check with different weights
        fields = [
            (product.name.lower(), 3),          # Highest priority
            (product.brand_name.lower(), 2),    # Medium priority
            (product.description.lower(), 1),   # Lower priority
            (product.category.name.lower(), 2)  # Medium priority
        ]
        
        # Exact match bonus
        for field_text, weight in fields:
            if query in field_text:
                score += 10 * weight  # Big bonus for exact match
        
        # Partial/word match
        for word in query_words:
            for field_text, weight in fields:
                if word in field_text:
                    score += weight
        
        # Add base score so all products stay in original order if no matches
        scored_products.append((product, score + 1))
    
    # Sort by score (descending) but keep original order for same scores
    scored_products.sort(key=lambda x: -x[1])
    
    return [p for p, score in scored_products]
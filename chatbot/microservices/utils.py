def get_products_and_categories_json():
    """
    Extract all products and categories and format them as JSON.
    Returns a hierarchical structure with categories containing their products.
    """
    # Import json module
    import json
    from products.models import Category, Product
    
    # Initialize the result dictionary
    result = {
        "categories": []
    }
    
    # Get all categories
    categories = Category.objects.prefetch_related('products').all()
    
    # Loop through each category
    for category in categories:
        category_data = {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "products": []
        }
        
        # Get all products for this category
        products = category.products.all()
        
        # Add each product to the category
        for product in products:
            product_data = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "link": product.link
            }
            category_data["products"].append(product_data)
        
        # Add the category to the result
        result["categories"].append(category_data)
    
    # Convert to JSON string
    json_data = json.dumps(result, indent=2)
    
    return json_data
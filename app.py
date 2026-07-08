import os
import re
import unicodedata
from flask import Flask, render_template, request, redirect, url_for, flash
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = 'super_secret_cozy_kitchen_key'

# --- Supabase Configuration ---
SUPABASE_URL = "https://zozsojlszffjcpfwzlpf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvenNvamxzemZmamNwZnd6bHBmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI5MDIyNTcsImV4cCI6MjA5ODQ3ODI1N30.HIMh7UPORg1XqSLAz18XVbJehm-OojNI-wYDhGQgCvc" # <--- PASTE YOUR ANON KEY HERE!

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Slug Generation Helpers ---
def generate_slug(text):
    """Converts a string into a URL-friendly slug."""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def get_unique_slug(title):
    """Ensures the generated slug is unique in the database."""
    base_slug = generate_slug(title)
    slug = base_slug
    counter = 1
    while True:
        # Check if slug exists
        response = supabase.table('recipes').select('id').eq('slug', slug).execute()
        if not response.data:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1

# --- Routes ---
@app.route('/')
def cookbook():
    # Fetch all recipes ordered by creation date
    response = supabase.table('recipes').select('*').order('created_at', desc=True).execute()
    recipes = response.data
    return render_template('cookbook.html', recipes=recipes)

@app.route('/recipe/<slug>')
def recipe_detail(slug):
    response = supabase.table('recipes').select('*').eq('slug', slug).execute()
    if not response.data:
        flash('Recipe not found.', 'error')
        return redirect(url_for('cookbook'))
    recipe = response.data[0]
    return render_template('recipe_detail.html', recipe=recipe)

@app.route('/share', methods=['GET', 'POST'])
def share_recipe():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        image_url = request.form.get('image_url', '')
        
        prep_time = int(request.form.get('prep_time') or 0)
        cook_time = int(request.form.get('cook_time') or 0)
        servings = int(request.form.get('servings') or 1)
        category = request.form.get('category', 'General')

        if not title:
            flash('Title is required!', 'error')
        else:
            unique_slug = get_unique_slug(title)
            
            new_recipe = {
                'title': title,
                'description': description,
                'ingredients': ingredients,
                'instructions': instructions,
                'image_url': image_url,
                'prep_time': prep_time,
                'cook_time': cook_time,
                'servings': servings,
                'category': category,
                'slug': unique_slug
            }
            
            supabase.table('recipes').insert(new_recipe).execute()
            flash('Recipe shared successfully!', 'success')
            return redirect(url_for('cookbook'))

    return render_template('share_recipe.html')

@app.route('/recipe/<slug>/edit', methods=['GET', 'POST'])
def edit_recipe(slug):
    response = supabase.table('recipes').select('*').eq('slug', slug).execute()
    if not response.data:
        flash('Recipe not found.', 'error')
        return redirect(url_for('cookbook'))
    
    recipe = response.data[0]
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        image_url = request.form.get('image_url', '')
        
        prep_time = int(request.form.get('prep_time') or 0)
        cook_time = int(request.form.get('cook_time') or 0)
        servings = int(request.form.get('servings') or 1)
        category = request.form.get('category', 'General')

        updated_data = {
            'title': title,
            'description': description,
            'ingredients': ingredients,
            'instructions': instructions,
            'image_url': image_url,
            'prep_time': prep_time,
            'cook_time': cook_time,
            'servings': servings,
            'category': category
        }

        # Update by ID to keep the original URL slug intact (good for SEO)
        supabase.table('recipes').update(updated_data).eq('id', recipe['id']).execute()
        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('recipe_detail', slug=slug))

    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/recipe/<slug>/delete', methods=['POST'])
def delete_recipe(slug):
    supabase.table('recipes').delete().eq('slug', slug).execute()
    flash('Recipe deleted.', 'success')
    return redirect(url_for('cookbook'))

if __name__ == '__main__':
    app.run(debug=True)
import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, flash, g

app = Flask(__name__)
app.secret_key = 'super_secret_cozy_kitchen_key'
DATABASE = 'kitchen_hearth.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    
    # 1. Create the base table if it doesn't exist at all
    db.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            ingredients TEXT,
            instructions TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. AUTOMATIC DATABASE MIGRATION: Check for missing columns and add them
    cursor = db.execute("PRAGMA table_info(recipes)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    if 'prep_time' not in existing_columns:
        db.execute("ALTER TABLE recipes ADD COLUMN prep_time INTEGER DEFAULT 0")
    if 'cook_time' not in existing_columns:
        db.execute("ALTER TABLE recipes ADD COLUMN cook_time INTEGER DEFAULT 0")
    if 'servings' not in existing_columns:
        db.execute("ALTER TABLE recipes ADD COLUMN servings INTEGER DEFAULT 1")
    if 'category' not in existing_columns:
        db.execute("ALTER TABLE recipes ADD COLUMN category TEXT DEFAULT 'General'")
        
    db.commit()
    
    # 3. Seed the database with the Classic Sourdough recipe if the table is completely empty
    cursor = db.execute('SELECT COUNT(*) FROM recipes')
    if cursor.fetchone()[0] == 0:
        db.execute('''
            INSERT INTO recipes (title, description, ingredients, instructions, image_url, prep_time, cook_time, servings, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Classic Sourdough',
            'A beautifully crusty, tangy, and chewy sourdough bread made with a simple starter.',
            '500g bread flour\n350g water\n100g active sourdough starter\n10g salt',
            '1. Mix flour and water, autolyse for 1 hour.\n2. Add starter and salt, fold to combine.\n3. Bulk ferment for 4-5 hours, doing stretch and folds every 30 mins.\n4. Shape and proof in the fridge overnight.\n5. Bake in a Dutch oven at 450F for 20 mins covered, 20 mins uncovered.',
            'https://images.unsplash.com/photo-1585478259715-876acc5be8eb?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
            240, 45, 8, 'Bread'
        ))
        db.commit()

@app.route('/')
def cookbook():
    db = get_db()
    recipes = db.execute('SELECT * FROM recipes ORDER BY created_at DESC').fetchall()
    return render_template('cookbook.html', recipes=recipes)

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    db = get_db()
    recipe = db.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
    if recipe is None:
        flash('Recipe not found.', 'error')
        return redirect(url_for('cookbook'))
    return render_template('recipe_detail.html', recipe=recipe)

@app.route('/share', methods=['GET', 'POST'])
def share_recipe():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        image_url = request.form.get('image_url', '')
        
        # Handle new numeric fields safely
        prep_time = int(request.form.get('prep_time') or 0)
        cook_time = int(request.form.get('cook_time') or 0)
        servings = int(request.form.get('servings') or 1)
        category = request.form.get('category', 'General')

        if not title:
            flash('Title is required!', 'error')
        else:
            db = get_db()
            db.execute(
                'INSERT INTO recipes (title, description, ingredients, instructions, image_url, prep_time, cook_time, servings, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (title, description, ingredients, instructions, image_url, prep_time, cook_time, servings, category)
            )
            db.commit()
            flash('Recipe shared successfully!', 'success')
            return redirect(url_for('cookbook'))

    return render_template('share_recipe.html')

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    db = get_db()
    recipe = db.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,)).fetchone()
    
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

        db.execute(
            'UPDATE recipes SET title = ?, description = ?, ingredients = ?, instructions = ?, image_url = ?, prep_time = ?, cook_time = ?, servings = ?, category = ? WHERE id = ?',
            (title, description, ingredients, instructions, image_url, prep_time, cook_time, servings, category, recipe_id)
        )
        db.commit()
        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    db = get_db()
    db.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
    db.commit()
    flash('Recipe deleted.', 'success')
    return redirect(url_for('cookbook'))

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
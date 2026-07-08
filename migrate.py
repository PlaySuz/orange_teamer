import sqlite3
import re
import unicodedata
from supabase import create_client, Client

# --- Supabase Configuration ---
SUPABASE_URL = "https://zozsojlszffjcpfwzlpf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvenNvamxzemZmamNwZnd6bHBmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MjkwMjI1NywiZXhwIjoyMDk4NDc4MjU3fQ.gFgRzunh0tO_cthvN7TQPIz2DsDLe9WkbCedWTdf3U4"  # <--- PASTE YOUR ANON KEY HERE!

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Slug Generation Helper ---
def generate_slug(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

# --- Local SQLite Connection ---
sqlite_db = sqlite3.connect('kitchen_hearth.db')
sqlite_db.row_factory = sqlite3.Row
cursor = sqlite_db.cursor()

# Fetch all local recipes
cursor.execute("SELECT * FROM recipes")
local_recipes = cursor.fetchall()

# Check exactly which columns exist in the local DB
column_names = [description[0] for description in cursor.description]

print(f"Found {len(local_recipes)} recipes in your local database.")
print("Starting migration to Supabase...\n")

# Keep track of used slugs to prevent duplicates
used_slugs = set()

for recipe in local_recipes:
    # Safely extract data, providing defaults if columns are missing in the local DB
    title = recipe['title']
    description = recipe['description'] if 'description' in column_names else ""
    ingredients = recipe['ingredients'] if 'ingredients' in column_names else ""
    instructions = recipe['instructions'] if 'instructions' in column_names else ""
    image_url = recipe['image_url'] if 'image_url' in column_names else ""
    
    prep_time = recipe['prep_time'] if 'prep_time' in column_names else 0
    cook_time = recipe['cook_time'] if 'cook_time' in column_names else 0
    servings = recipe['servings'] if 'servings' in column_names else 1
    category = recipe['category'] if 'category' in column_names else "General"
    
    # Generate slug if it doesn't exist in the local DB
    if 'slug' in column_names and recipe['slug']:
        base_slug = recipe['slug']
    else:
        base_slug = generate_slug(title)
        
    # Ensure slug uniqueness (e.g. if you have two recipes named "Pasta")
    slug = base_slug
    counter = 1
    while slug in used_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1
    used_slugs.add(slug)
        
    data_to_insert = {
        'title': title,
        'description': description,
        'ingredients': ingredients,
        'instructions': instructions,
        'image_url': image_url,
        'prep_time': prep_time,
        'cook_time': cook_time,
        'servings': servings,
        'category': category,
        'slug': slug
    }
    
    try:
        supabase.table('recipes').insert(data_to_insert).execute()
        print(f"✅ Successfully migrated: {title} (Slug: {slug})")
    except Exception as e:
        print(f"❌ Skipped {title}. Error: {e}")

sqlite_db.close()
print("\n🎉 Migration process finished!")
from app import app

print("\nRegistered routes:")
for rule in app.url_map.iter_rules():
    print(rule)

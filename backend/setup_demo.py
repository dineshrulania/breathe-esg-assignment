"""
Setup script to create demo data for the ESG platform.
Run with: python manage.py shell < setup_demo.py
"""

from core.models import Company, User

# Create demo company
company, created = Company.objects.get_or_create(
    name="Demo Corporation",
    defaults={'is_active': True}
)

if created:
    print(f"✓ Created company: {company.name}")
else:
    print(f"✓ Company already exists: {company.name}")

# Create demo users
users_data = [
    {
        'username': 'admin',
        'email': 'admin@demo.com',
        'password': 'admin123',
        'role': 'admin',
        'first_name': 'Admin',
        'last_name': 'User'
    },
    {
        'username': 'analyst',
        'email': 'analyst@demo.com',
        'password': 'analyst123',
        'role': 'analyst',
        'first_name': 'Sarah',
        'last_name': 'Analyst'
    },
    {
        'username': 'viewer',
        'email': 'viewer@demo.com',
        'password': 'viewer123',
        'role': 'viewer',
        'first_name': 'John',
        'last_name': 'Viewer'
    }
]

for user_data in users_data:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults={
            'email': user_data['email'],
            'company': company,
            'role': user_data['role'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name']
        }
    )
    
    if created:
        user.set_password(user_data['password'])
        user.save()
        print(f"✓ Created user: {user.username} ({user.role})")
    else:
        print(f"✓ User already exists: {user.username}")

print("\n" + "="*50)
print("Demo setup complete!")
print("="*50)
print("\nLogin credentials:")
print("-" * 50)
for user_data in users_data:
    print(f"{user_data['role'].upper():10} | {user_data['username']:10} | {user_data['password']}")
print("-" * 50)

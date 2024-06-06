from pymongo import MongoClient

def create_indexes():
    # Establish connection to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['your_database_name']

    # Access the unified collection
    unified_collection = db['users']

    # Creating indexes
    print("Creating indexes...")
    # Index on username and email
    unified_collection.create_index("username", unique=True)
    unified_collection.create_index("email", unique=True)

    # Compound index for date of birth and username
    unified_collection.create_index([("personal_info.date_of_birth", 1), ("username", 1)])

    # Index for sorting operations on activity dates
    unified_collection.create_index([("activity.date", -1)])

    print("Indexes created successfully.")

def analyze_performance():
    # Connect to MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['your_database_name']
    
    # Access the unified collection
    unified_collection = db['users']

    # Sample aggregation to analyze activity frequency and potential bottlenecks
    print("Analyzing activity frequency...")
    agg_result = unified_collection.aggregate([
        {"$unwind": "$activity"},
        {"$group": {
            "_id": "$activity.action",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ])

    # Print results
    for result in agg_result:
        print(result)

if __name__ == '__main__':
    create_indexes()
    analyze_performance()

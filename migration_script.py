from pymongo import MongoClient
from pymongo import errors
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Establish connection to MongoDB
client = MongoClient(os.getenv('MONGO_URI'),retryWrites=True)
db = client[os.getenv('DATABASE_NAME')]

# New unified collection
unified_collection = db['users']

# Collections to merge
details_collection = db['user_details']
preferences_collection = db['user_preferences']
activities_collection = db['user_activities']

# Start a session for transaction
with client.start_session() as session:
    try:
        # Start a transaction
        with session.start_transaction():
            # Clear the unified collection if needed (use with caution)
            unified_collection.delete_many({}, session=session)

            # Iterate over the details collection and integrate data from other collections
            for detail in details_collection.find(session=session):
                # Prepare the unified document structure based on the new schema
                unified_document = {
                    "_id": detail["_id"],
                    "username": detail.get("username"),
                    "email": detail.get("email"),
                    "personal_info": {
                        "first_name": detail.get("first_name"),
                        "last_name": detail.get("last_name"),
                        "date_of_birth": detail.get("date_of_birth"),
                        "gender": detail.get("gender"),
                        "phone": detail.get("phone")
                    },
                    "address": {
                        "street": detail.get("street"),
                        "city": detail.get("city"),
                        "state": detail.get("state"),
                        "zip_code": detail.get("zip_code"),
                        "country": detail.get("country")
                    },
                    "created_at": detail.get("created_at", datetime.now()),
                    "updated_at": datetime.now(),
                    "account_status": detail.get("status", "active")  # Default to active if not specified
                }

                # Integrate preferences
                preference = preferences_collection.find_one({"_id": detail["_id"]}, session=session)
                if preference:
                    unified_document["preferences"] = {
                        "language": preference.get("language"),
                        "timezone": preference.get("timezone"),
                        "marketing_opt_in": preference.get("marketing_opt_in", False)
                    }

                # Integrate activities
                activities = list(activities_collection.find({"user_id": detail["_id"]}, session=session))
                unified_document["activity"] = [
                    {
                        "date": activity["date"],
                        "action": activity["action"],
                        "details": activity.get("details", "")
                    } for activity in activities
                ]

                # Insert the unified document into the new collection
                unified_collection.insert_one(unified_document, session=session)

            # Validation check
            if unified_collection.count_documents({}, session=session) != details_collection.count_documents({}, session=session):
                raise Exception("Data mismatch error: not all documents were migrated properly.")

            # Commit the transaction
            session.commit_transaction()
            print("Data migration complete with transaction.")
            
    except (errors.PyMongoError, Exception) as e:
        # Abort transaction on error
        session.abort_transaction()
        print(f"Transaction aborted due to error: {e}")

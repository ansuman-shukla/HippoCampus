from app.core.database import collection
import logging

logger = logging.getLogger(__name__)


async def create_user_if_not_exists(data: dict):
    """
    Create a user if they do not exist in the database.
    """
    logger.info(f"👤 USER SERVICE: Checking/creating user from JWT payload")
    
    # Extract data from the decoded JWT
    user_id = data.get("sub")
    email = data.get("email")
    role = data.get("role")
    created_at = data.get("created_at")
    last_sign_in_at = data.get("updated_at")  # Last sign-in is "updated_at"
    issuer = data.get("iss")  # Top-level claim

    logger.info(f"   ├─ User ID: {user_id}")
    logger.info(f"   ├─ Email: {email}")
    logger.info(f"   ├─ Role: {role}")
    logger.info(f"   ├─ Issuer: {issuer}")
    logger.info(f"   ├─ Created at: {created_at}")
    logger.info(f"   └─ Last sign in: {last_sign_in_at}")

    # User metadata (e.g., name, picture)
    user_metadata = data.get("user_metadata", {})
    full_name = user_metadata.get("full_name")
    picture = user_metadata.get("picture")
    
    logger.info(f"   ├─ Full name: {full_name}")
    logger.info(f"   └─ Picture present: {bool(picture)}")

    # App metadata (e.g., auth provider)
    app_metadata = data.get("app_metadata", {})
    provider = app_metadata.get("provider")
    providers = app_metadata.get("providers")
    
    logger.info(f"   ├─ Provider: {provider}")
    logger.info(f"   └─ Providers: {providers}")

    # Combine into user_data
    user_data = {
        "id": user_id,
        "email": email,
        "role": role,
        "created_at": created_at,
        "last_sign_in_at": last_sign_in_at,
        "issuer": issuer,
        "full_name": full_name,
        "picture": picture,
        "provider": provider,
        "providers": providers
    }

    logger.info(f"🔍 USER SERVICE: Checking if user exists in database")
    if not await user_exists(user_id):
        logger.info(f"➕ USER SERVICE: User not found, creating new user")
        await create_user(user_data)
        logger.info(f"✅ USER SERVICE: New user created successfully")
    else:
        logger.info(f"✅ USER SERVICE: User already exists, skipping creation")
    
    return user_data


async def user_exists(user_id: str):
    logger.info(f"🔍 USER SERVICE: Checking if user exists")
    logger.info(f"   └─ User ID: {user_id}")
    
    query = collection.find_one({"id": user_id})
    exists = query is not None
    
    logger.info(f"   └─ User exists: {exists}")
    if exists:
        logger.info(f"   └─ Found user data keys: {list(query.keys()) if query else 'None'}")
    
    return exists


async def create_user(user_data: dict):
    logger.info(f"➕ USER SERVICE: Creating new user in database")
    logger.info(f"   ├─ User ID: {user_data.get('id')}")
    logger.info(f"   ├─ Email: {user_data.get('email')}")
    logger.info(f"   ├─ Full name: {user_data.get('full_name')}")
    logger.info(f"   └─ Data keys: {list(user_data.keys())}")
    
    try:
        result = collection.insert_one(user_data)
        logger.info(f"✅ USER SERVICE: User created successfully")
        logger.info(f"   ├─ Inserted ID: {result.inserted_id}")
        logger.info(f"   └─ Acknowledged: {result.acknowledged}")
        return user_data
    except Exception as e:
        logger.error(f"❌ USER SERVICE: Failed to create user in database")
        logger.error(f"   ├─ Error type: {type(e).__name__}")
        logger.error(f"   ├─ Error message: {str(e)}")
        logger.error(f"   └─ This may cause issues with user data persistence")
        raise

    
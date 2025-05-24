from app.core.database import collection


async def create_user_if_not_exists(data: dict):
    """
    Create a user if they do not exist in the database.
    """
    # Extract data from the decoded JWT
    user_id = data.get("sub")
    email = data.get("email")
    role = data.get("role")
    created_at = data.get("created_at")
    last_sign_in_at = data.get("updated_at")  # Last sign-in is "updated_at"
    issuer = data.get("iss")  # Top-level claim

    # User metadata (e.g., name, picture)
    user_metadata = data.get("user_metadata", {})
    full_name = user_metadata.get("full_name")
    picture = user_metadata.get("picture")

    # App metadata (e.g., auth provider)
    app_metadata = data.get("app_metadata", {})
    provider = app_metadata.get("provider")
    providers = app_metadata.get("providers")

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

    if not await user_exists(user_id):
        await create_user(user_data)
    return user_data


async def user_exists(user_id: str):    
    query = collection.find_one({"id": user_id})
    return query is not None


async def create_user(user_data: dict):
    collection.insert_one(user_data)
    return user_data

    
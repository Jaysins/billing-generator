
def register_every():
    from pymongo import MongoClient

    db = MongoClient(settings.DATABASE_URL)["shipping"]["profile"]


    for us in db:
        data = dict(email=us.get("email"), username=us.get("username"), name=us.get("name"),
                    first_name=us.get("first_name"), last_name=us.get("last_name"), phone=us.get("phone"),
                    instance_id=us.get("instance_id"), referral_code=us.get("referral_code"),
                    referred_by=us.get("referred_by"), is_anonymous=us.get("is_anonymous"), user_id=us.get("user_id"),
                    date_created=us.get("date_created"), last_updated=us.get("last_updated"), region=us.get("region"), )
        ProfileService.register(**data)

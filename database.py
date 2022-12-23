import pymongo
DB_URI = "mongodb+srv://emiliausers:emiliausers@cluster0.tdixf.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
DB_NAME = "Emila" 

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

user_collection = database['users']

async def present_in_userbase(user_id : int):
    found = user_collection.find_one({'_id': user_id})
    if found:
        return True
    else:
        return False
async def get_status():
    no_users = user_collection.find().count()
    if no_users:
        return no_users
    else:
        return False

async def add_to_userbase(user_id: int):
    user_collection.insert_one({'_id': user_id})
    return

async def total_users_count():
    count = user_collection.count_documents({})
    return count

async def get_users():
    user_docs = user_collection.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])
        
    return user_ids
    
async def del_from_userbase(user_id: int):
    user_collection.delete_one({'_id': user_id})
    return

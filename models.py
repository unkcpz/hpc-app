"""Application Models"""
import bson, os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

DATABASE_URL=f'mongodb+srv://mphpc:{os.environ.get("password")}@mongodb-heroku-mp-hpc-a.dzddt.mongodb.net/hpcdb?retryWrites=true&w=majority'
print(DATABASE_URL)
client = MongoClient(DATABASE_URL)
db = client.myDatabase

class Jobs:
    """Jobs Model"""
    def __init__(self):
        return

    def create(self, userid, jobid):
        """Create a new job in DB"""
        job = self.get_by_userid_and_jobid(userid, jobid)
        if job:
            return
        new_job = db.jobs.insert_one(
            {
                "jobid": jobid,
                "userid": userid,
            }
        )
        return self.get_by_id(new_job.inserted_id)
    
    def get_by_userid_and_jobid(self, userid, jobid):
        """job"""
        job = db.jobs.find_one({"userid": userid, "jobid": jobid})
        if not job:
            return
        job["_id"] = str(job["_id"])
        return 
    
    def get_by_id(self, jobid):
        """Get a job given its jobid"""
        job = db.jobs.find_one({"_id": bson.ObjectId(jobid)})
        if not job:
            return
        job["_id"] = str(job["_id"])
        return job

    def get_by_userid(self, userid):
        """Get all jobs created by a user"""
        jobs = db.jobs.find({"userid": userid})
        return [job.get('jobid') for job in jobs]
    
    def get_all(self):
        """For admin only"""
        books = db.books.find()
        return [{**book, "_id": str(book["_id"])} for book in books]


    def update(self, book_id, title="", description="", image_url="", category="", userid=""):
        """Update a book"""
        data={}
        if title: data["title"]=title
        if description: data["description"]=description
        if image_url: data["image_url"]=image_url
        if category: data["category"]=category

        book = db.books.update_one(
            {"_id": bson.ObjectId(book_id)},
            {
                "$set": data
            }
        )
        book = self.get_by_id(book_id)
        return book

class User:
    """User Model"""
    def __init__(self):
        return

    def create(self, name="", email=""):
        """Create a new user"""
        user = self.get_by_email(email)
        if user:
            return
        new_user = db.users.insert_one(
            {
                "name": name,
                "email": email,
                "active": True,
            }
        )
        return self.get_by_id(new_user.inserted_id)

    def get_all(self):
        """Get all users"""
        users = db.users.find({"active": True})
        return [{**user, "_id": str(user["_id"])} for user in users]

    def get_by_id(self, userid):
        """Get a user by id"""
        user = db.users.find_one({"_id": bson.ObjectId(userid), "active": True})
        if not user:
            return
        user["_id"] = str(user["_id"])
        return user

    def get_by_email(self, email):
        """Get a user by email"""
        user = db.users.find_one({"email": email, "active": True})
        if not user:
            return
        user["_id"] = str(user["_id"])
        return user

    def update(self, userid, name=""):
        """Update a user"""
        data = {}
        if name:
            data["name"] = name
        user = db.users.update_one(
            {"_id": bson.ObjectId(userid)},
            {
                "$set": data
            }
        )
        user = self.get_by_id(userid)
        return user

    def delete(self, userid):
        """Delete a user"""
        Books().delete_by_userid(userid)
        user = db.users.delete_one({"_id": bson.ObjectId(userid)})
        user = self.get_by_id(userid)
        return user

    def disable_account(self, userid):
        """Disable a user account"""
        user = db.users.update_one(
            {"_id": bson.ObjectId(userid)},
            {"$set": {"active": False}}
        )
        user = self.get_by_id(userid)
        return user
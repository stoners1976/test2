from locust import HttpLocust, TaskSet



def login(l):

    l.client.post("/goodnight/api/v3/users/signin/normal", {"email":"joe.cho@email.com", "pw":"password", "social_id":0})



def profile(l):

    l.client.get("/goodnight/api/v3/users/profile")



class UserBehavior(TaskSet):

    tasks = {profile: 1}



    def on_start(self):

        login(self)



class WebsiteUser(HttpLocust):

    task_set = UserBehavior

    min_wait = 5000

    max_wait = 9000 

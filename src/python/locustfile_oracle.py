from locust import HttpUser, task

class User(HttpUser):
    @task
    def index(self):
        self.client.get("/oracle/insert")
        # self.client.get("/oracle/select")

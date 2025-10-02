from locust import HttpUser, task

class User(HttpUser):
    @task
    def index(self):
        self.client.get("/mongo/insert")
        # self.client.get("/mongo/select")

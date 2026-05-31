"""Locust load tests — run through nginx in soak tests: --host=http://localhost:80"""
from locust import HttpUser, between, task


class StudyNexsUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.username = "test_admin"
        self.password = "Admin@123"
        self.token = ""
        self.login()

    def login(self):
        resp = self.client.post(
            "/api/v1/auth/login",
            json={"username": self.username, "password": self.password},
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token", "")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(3)
    def view_profile(self):
        self.client.get("/api/v1/users/me")

    @task(2)
    def list_classes(self):
        self.client.get("/api/v1/academic/classes")

    @task(2)
    def list_students(self):
        self.client.get("/api/v1/academic/students?page_size=20")

    @task(1)
    def fee_stats(self):
        self.client.get("/api/v1/fees/stats")

    @task(1)
    def notifications(self):
        self.client.get("/api/v1/notifications/unread-count")

    @task(1)
    def health(self):
        self.client.get("/health")

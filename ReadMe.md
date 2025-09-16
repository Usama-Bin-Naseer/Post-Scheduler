# Flask Post Scheduler

**Flask Post Scheduler** is a web application that allows users to schedule text and image-based posts for future publication. Built with Flask, this app supports uploading content, scheduling posts, and automatically managing the content at the specified time.

## Features:
- Upload text and images for posts.
- Schedule posts for a future time.
- Edit and delete scheduled posts.
- View published posts in the "Preview" section.
- Dockerized for easy deployment.

## Technologies Used:
- Flask
- SQLAlchemy
- APScheduler
- Docker

## Installation:
Clone the repository:
```bash
git clone https://github.com/yourusername/flask-post-scheduler.git
cd Post-Scheduler/
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run the Flask app:**
```bash
python app.py
```

**Docker Setup:**
To build and run the app with Docker:

```bash
docker build -t flask-post-scheduler .
docker run -p 5000:5000 flask-post-scheduler
```

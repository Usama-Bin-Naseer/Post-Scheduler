# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the app will run on
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py
# Make Flask available externally
ENV FLASK_RUN_HOST=0.0.0.0  

# Run the application
CMD ["flask", "run"]

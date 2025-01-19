# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt into the container
COPY requirements.txt .

# Install any needed dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Expose the port that the app runs on (5001 in this case)
EXPOSE 5001

# Set the default command to run your app
CMD ["python", "app/app.py"]

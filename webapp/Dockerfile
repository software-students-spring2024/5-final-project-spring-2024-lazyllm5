FROM python:3.10-slim-buster

# Set the working directory in the image
WORKDIR /webapp

# install dependencies into the image - doing this first will speed up subsequent builds, as Docker will cache this step
COPY requirements.txt .
RUN pip3 install -r requirements.txt


# Copy the current directory contents into the container at /quiz_app
ADD . .

# expose the port that the Flask app is running on... by default 5000
EXPOSE 3000

# Run app.py when the container launches
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=3000"]
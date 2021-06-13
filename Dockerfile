#Base python image
FROM python:3.7-slim-buster

# Install Flask
RUN pip install Flask

# Copy the code into a folder named app
ADD . /app

# switch the working directory to app
WORKDIR /app

# Install App dependencies
RUN pip3 install -r requirements.txt

# Set ENV variables
ENV PORT 5000

RUN export FLASK_APP="app:create_app('config/local.py')"



# Expose port 5000 for app
EXPOSE ${PORT}

CMD ["python", "-u", "app.py"]
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

# Install system dependencies required for pyodbc and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    unixodbc-dev \
    curl \
    gnupg2 \
    apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install -r requirements.txt
# Set environment variables from the .env file
ENV DB_PORT=${DB_PORT}
ENV DB_USER=${DB_USER}
ENV DB_NAME=${DB_NAME}
ENV DB_HOST=${DB_HOST}
ENV DB_PASSWORD=${DB_PASSWORD}

# Expose port 8000 for the Django app
EXPOSE 8000

# Start the Django app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
